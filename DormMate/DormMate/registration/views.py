from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import (
    AdminCreationForm,
    RoomForm,
    RoomGroupForm,
    PetitionForm,
    PetitionResponseForm,
    NewsForm,
    ProfileUpdateForm,
    CustomPasswordChangeForm,
)
from .models import CustomUser, Petition, News
from django.contrib.auth.decorators import login_required
from rooms.models import Application, Room
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
import smtplib
import ssl
from email.mime.text import MIMEText
from django.http import HttpResponseForbidden
from django.db.models import (
    BooleanField,
    Case,
    When,
    Value,
    Q,
    ExpressionWrapper,
)
from django.db import models
from django.db.models import Count
from django.contrib.auth import update_session_auth_hash


# -----------------------------
#      РЕЄСТРАЦІЯ КОРИСТУВАЧІВ
# -----------------------------

def register_view(request):
    """Реєстрація студента та автоматичний вхід після успіху."""
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = "student"
            user.save()
            login(request, user)
            return redirect("welcome")
    else:
        form = CustomUserCreationForm()
    return render(request, "sign_in.html", {"form": form})


# -----------------------------
#              ЛОГІН
# -----------------------------

def login_view(request):
    """Авторизація користувача."""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # якщо користувач спершу намагався потрапити на захищену сторінку
            next_url = request.GET.get("next")
            return redirect(next_url or "account")
        else:
            messages.error(request, "Неправильний логін або пароль")
    else:
        form = AuthenticationForm()
    return render(request, "log_in.html", {"form": form})


# -----------------------------
#             ВИХІД
# -----------------------------

def logout_view(request):
    logout(request)
    return redirect("floor-selector")


# -----------------------------
#        АККАУНТ КОРИСТУВАЧА
# -----------------------------


@login_required
def account_view(request):
    """Показ профілю та заявок (для адміна — усі заявки)."""
    user = request.user
    applications = None

    if user.role == "admin":
        applications = Application.objects.select_related("user").all().order_by("-id")

    return render(
        request,
        "account.html",
        {
            "user": user,
            "applications": applications,
        },
    )


# -----------------------------
#   ДОПОМІЖНА ПЕРЕВІРКА РОЛІ
# -----------------------------

def is_admin(user):
    return user.is_authenticated and user.role == "admin"


# -----------------------------
#      СТВОРЕННЯ АДМІН-КОРИСТУВАЧА
# -----------------------------


@login_required
@user_passes_test(is_admin)
def create_admin_view(request):
    if request.method == "POST":
        form = AdminCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("account")
    else:
        form = AdminCreationForm()
    return render(request, "create_admin.html", {"form": form})


# -----------------------------
#            СПИСОК ЮЗЕРІВ
# -----------------------------


@login_required
def user_list_view(request):
    if request.user.role != "admin":
        return redirect("account")  # заборона для не‑адмінів

    admins = CustomUser.objects.filter(role="admin").order_by("username")
    students = CustomUser.objects.filter(role="student").order_by("username")
    users = list(admins) + list(students)

    return render(request, "user_list.html", {"users": users})


# -----------------------------
#      СПИСОК ЗАЯВОК НА КІМНАТИ
# -----------------------------


@login_required
def application_list_view(request):
    status = request.GET.get("status", "all")
    only_returning = request.GET.get("returning") == "1"

    if request.user.role == "admin":
        base_queryset = Application.objects.annotate(
            is_returning_to_same_room=Case(
                When(user__room__number=models.F("room_number"), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
            was_resident=ExpressionWrapper(Q(user__room__isnull=False), output_field=BooleanField()),
        )
    else:
        base_queryset = Application.objects.filter(user=request.user).annotate(
            is_returning_to_same_room=Case(
                When(user__room__number=models.F("room_number"), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
            was_resident=ExpressionWrapper(Q(user__room__isnull=False), output_field=BooleanField()),
        )

    if status != "all":
        base_queryset = base_queryset.filter(status=status)

    if only_returning:
        base_queryset = base_queryset.filter(is_returning_to_same_room=True)

    applications = base_queryset.order_by("-created_at")

    context = {
        "applications": applications,
        "current_status": status,
        "only_returning": only_returning,
    }
    return render(request, "application_list.html", context)


# -----------------------------
#        ДЕТАЛІ ЗАЯВКИ
# -----------------------------


@login_required
def application_detail_view(request, pk):
    application = get_object_or_404(Application, pk=pk)

    # Перевірка доступу:
    # – Адмін може дивитися всі заявки
    # – Студент — тільки свої
    if request.user.role != "admin" and application.user != request.user:
        return render(request, "403.html")  # сторінка «Доступ заборонено»

    return render(request, "application_detail.html", {"application": application})


# -----------------------------
#          НАДІСЛАТИ ЛИСТ
# -----------------------------

def send_email_unverified(subject, message, from_email, to_email):
    """Надсилання листа без перевірки SSL‑сертифіката (для локального SMTP)"""
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    context = ssl._create_unverified_context()

    with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
        server.starttls(context=context)
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.sendmail(from_email, [to_email], msg.as_string())


# -----------------------------
#      ЗМІНА СТАТУСУ ЗАЯВКИ
# -----------------------------


@login_required
def change_application_status(request, pk, new_status):
    application = get_object_or_404(Application, pk=pk)
    user = request.user

    allowed_statuses = ["pending", "approved", "rejected"]
    if new_status not in allowed_statuses:
        return HttpResponseForbidden("Неприпустимий статус.")

    # Студент може лише відхилити власну заявку
    if user.role == "student":
        if application.user != user or application.status != "pending" or new_status != "rejected":
            return HttpResponseForbidden("У вас немає прав для цієї дії.")
    elif user.role != "admin":
        return HttpResponseForbidden("Доступ заборонено.")

    # Отримуємо інформацію про кімнату
    try:
        room = Room.objects.get(number=application.room_number)
    except Room.DoesNotExist:
        return HttpResponseForbidden("Кімнату не знайдено.")

    student = application.user

    # Обробка схвалення — переселення в нову кімнату
    if new_status == "approved":
        old_room = student.room
        if old_room and old_room != room:
            old_room.residents.remove(student)
        student.room = room
        student.save()
        room.residents.add(student)

    # Присвоюємо статус
    application.status = new_status
    application.save()

    # Формуємо лист
    subject = f"Статус вашої заявки: {application.get_status_display()}"
    message = (
        f"Вітаємо, {student.username}!\n\n"
        f"Статус вашої заявки на поселення в кімнату №{room.number} (поверх {room.floor}) "
        f"змінено на: {application.get_status_display()}.\n\n"
        "Ви можете перевірити статус у своєму акаунті.\n\n"
        "З повагою,\n"
        "Команда гуртожитку."
    )

    send_email_unverified(subject, message, settings.DEFAULT_FROM_EMAIL, student.email)

    return redirect("application-detail", pk=pk)


# -----------------------------
#      СКИДУЄМО СТАТУС ЗАЯВКИ
# -----------------------------


@login_required
def reset_application_status(request, pk):
    application = get_object_or_404(Application, pk=pk)
    user = application.user  # Користувач, що подав заявку

    old_room = user.room
    room_info = "не була прив'язана до жодної кімнати"

    # Якщо користувач був поселений — видаляємо зв'язок
    if old_room:
        old_room.residents.remove(user)
        room_info = f"Кімната №{old_room.number} (поверх {old_room.floor})"
        user.room = None
        user.save()

    # Скидання статусу заявки
    application.status = "pending"
    application.save()

    # Формуємо лист
    subject = f"Статус вашої заявки: {application.get_status_display()}"
    message = (
        f"Вітаємо, {user.username}!\n\n"
        f"Статус вашої заявки скинуто до: {application.get_status_display()}.\n"
        f"Раніше ви були прикріплені до: {room_info} — цей зв'язок видалено.\n\n"
        "Ви можете подати нову заявку до іншої кімнати.\n\n"
        "З повагою,\n"
        "Команда гуртожитку."
    )

    send_email_unverified(subject, message, settings.DEFAULT_FROM_EMAIL, user.email)

    return redirect("application-detail", pk=pk)


# -----------------------------
#        ВИДАЛЕННЯ АККАУНТА
# -----------------------------


@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        email = user.email
        username = user.username
        user.delete()

        # Надсилання листа
        send_mail(
            subject="Ваш акаунт було видалено",
            message=(
                f"Вітаємо, {username}!\n\n"
                "Ваш акаунт на сайті гуртожитку успішно видалено.\n"
                "Якщо це була помилка — зверніться до адміністрації."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return redirect("login")


# -----------------------------
#              КІМНАТИ
# -----------------------------

def is_admin(user):
    return user.is_authenticated and user.role == "admin"


@user_passes_test(is_admin)
def add_room(request):
    single_form = RoomForm()
    group_form = RoomGroupForm()

    if request.method == "POST":
        if "add_single" in request.POST:
            single_form = RoomForm(request.POST, request.FILES)
            if single_form.is_valid():
                room = single_form.save(commit=False)
                base_number = single_form.cleaned_data["number"]
                floor = room.floor

                try:
                    number_int = int(base_number)
                except ValueError:
                    messages.error(request, "Номер кімнати має бути числом.")
                    return render(
                        request,
                        "add_room.html",
                        {
                            "form": single_form,
                            "group_form": group_form,
                        },
                    )

                # Генерація повного номера
                if number_int < 10:
                    room.number = f"{floor}0{number_int}"
                else:
                    room.number = f"{floor}{number_int}"

                room.save()
                single_form.save_m2m()
                messages.success(request, f"Кімната {room.number} додана.")
                return redirect("add-room")

        elif "add_group" in request.POST:
            group_form = RoomGroupForm(request.POST)
            if group_form.is_valid():
                count = group_form.cleaned_data["count"]
                floor_input = group_form.cleaned_data["floors"]
                price = group_form.cleaned_data["price"]
                capacity = group_form.cleaned_data["capacity"]
                about = group_form.cleaned_data["about"]

                floor_list = [int(f.strip()) for f in floor_input.split(",") if f.strip().isdigit()]
                created_rooms = []

                for floor in floor_list:
                    existing_numbers = set(
                        Room.objects.filter(floor=floor).values_list("number", flat=True)
                    )

                    created = 0
                    number_suffix = 1

                    while created < count:
                        number = f"{floor}{number_suffix:02d}"
                        if number not in existing_numbers:
                            Room.objects.create(
                                number=number,
                                floor=floor,
                                price=price,
                                capacity=capacity,
                                about=about,
                            )
                            created_rooms.append(number)
                            created += 1
                        number_suffix += 1

                if created_rooms:
                    messages.success(
                        request,
                        f"Додано кімнати: {', '.join(created_rooms)}",
                    )
                else:
                    messages.info(request, "Нові кімнати не були додані — усі вже існують.")
                return redirect("add-room")

    return render(
        request,
        "add_room.html",
        {
            "form": single_form,
            "group_form": group_form,
        },
    )


# -----------------------------
#              ПЕТИЦІЇ
# -----------------------------


@login_required
def create_petition_view(request):
    if request.method == "POST":
        form = PetitionForm(request.POST)
        if form.is_valid():
            petition = form.save(commit=False)
            petition.author = request.user
            petition.save()
            return redirect("petition-list")
    else:
        form = PetitionForm()
    return render(request, "create_petition.html", {"form": form})


def petition_list_view(request):
    sort = request.GET.get("sort", "date")  # Тип сортування: за замовчуванням — дата

    petitions = Petition.objects.annotate(
        vote_count=Count("votes"),
        response_count=Count("responses"),  # Кількість відповідей адмінів
    )

    if sort == "votes":
        petitions = petitions.order_by("-vote_count", "-created_at")
    else:
        petitions = petitions.order_by("-created_at")

    return render(
        request,
        "petition_list.html",
        {
            "petitions": petitions,
            "sort": sort,
        },
    )


@login_required
def vote_for_petition(request, petition_id):
    petition = get_object_or_404(Petition, id=petition_id)

    if request.user in petition.votes.all():
        messages.warning(request, "Ви вже проголосували за цю петицію.")
    else:
        petition.votes.add(request.user)
        messages.success(request, "Ваш голос зараховано!")

    return redirect("petition-list")


# -----------------------------
#     ДЕТАЛІ ПЕТИЦІЇ & ВІДПОВІДІ
# -----------------------------


@login_required
def petition_detail_view(request, petition_id):
    petition = get_object_or_404(Petition, id=petition_id)
    user_has_voted = request.user in petition.votes.all()

    responses = petition.responses.all().order_by("-created_at")

    if request.method == "POST" and request.user.is_staff:  # лише адміни можуть відповідати
        form = PetitionResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.petition = petition
            response.responder = request.user
            response.save()
            return redirect("petition-detail", petition_id=petition.id)
    else:
        form = PetitionResponseForm()

    context = {
        "petition": petition,
        "user_has_voted": user_has_voted,
        "responses": responses,
        "response_form": form if request.user.is_staff else None,
    }
    return render(request, "petition_detail.html", context)


# -----------------------------
#                НОВИНИ
# -----------------------------

def news_list(request):
    news = News.objects.all()
    return render(request, "news_list.html", {"news": news})


@user_passes_test(is_admin)
def create_news(request):
    if request.method == "POST":
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            news = form.save(commit=False)
            news.author = request.user
            news.save()
            return redirect("news-list")
    else:
        form = NewsForm()
    return render(request, "create_news.html", {"form": form})


@user_passes_test(is_admin)
def delete_news(request, news_id):
    news = get_object_or_404(News, id=news_id)
    news.delete()
    return redirect("news-list")


@login_required
def edit_profile(request):
    if request.method == 'POST':
        profile_form = ProfileUpdateForm(request.POST, instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)

        if 'update_profile' in request.POST and profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Профіль оновлено.')
            return redirect('edit-profile')

        if 'change_password' in request.POST and password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль змінено.')
            return redirect('edit-profile')
    else:
        profile_form = ProfileUpdateForm(instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'edit_profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
    })