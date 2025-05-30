from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import AdminCreationForm , RoomForm
from .models import CustomUser
from django.contrib.auth.decorators import login_required
from rooms.models import Application, Room
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
import smtplib
import ssl
from email.mime.text import MIMEText
from django.http import HttpResponseForbidden
from django.shortcuts import redirect


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'student' 
            user.save()
            login(request, user)
            return redirect('welcome')
    else:
        form = CustomUserCreationForm()
    return render(request, 'sign_in.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next')  # если пользователь сначала пытался попасть на защищённую страницу
            return redirect(next_url or 'account')
        else:
            messages.error(request, "Неправильный логин или пароль")
    else:
        form = AuthenticationForm()
    return render(request, "log_in.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect('floor-selector')


@login_required
def account_view(request):
    user = request.user
    applications = None

    if user.role == 'admin':
        applications = Application.objects.select_related('user').all().order_by('-id')

    return render(request, 'account.html', {
        'user': user,
        'applications': applications,
    })




def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@login_required
@user_passes_test(is_admin)
def create_admin_view(request):
    if request.method == 'POST':
        form = AdminCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('account')
    else:
        form = AdminCreationForm()
    return render(request, 'create_admin.html', {'form': form})


@login_required
def user_list_view(request):
    if request.user.role != 'admin':
        return redirect('account')  # запрет для не-админов

    admins = CustomUser.objects.filter(role='admin').order_by('username')
    students = CustomUser.objects.filter(role='student').order_by('username')
    users = list(admins) + list(students)

    return render(request, 'user_list.html', {'users': users})



@login_required
def application_list_view(request):
    status = request.GET.get('status', 'all')  # теперь 'all' по умолчанию

    if request.user.role == 'admin':
        if status == 'all':
            applications = Application.objects.all().order_by('-created_at')
        else:
            applications = Application.objects.filter(status=status).order_by('-created_at')
    else:
        if status == 'all':
            applications = Application.objects.filter(user=request.user).order_by('-created_at')
        else:
            applications = Application.objects.filter(user=request.user, status=status).order_by('-created_at')

    context = {
        'applications': applications,
        'current_status': status,
    }
    return render(request, 'application_list.html', context)



@login_required
def application_detail_view(request, pk):
    application = get_object_or_404(Application, pk=pk)

    # Проверка доступа:
    # - Админ может смотреть все заявки
    # - Студент — только свои
    if request.user.role != 'admin' and application.user != request.user:
        return render(request, '403.html')  # страница "Доступ запрещён"

    return render(request, 'application_detail.html', {'application': application})


def send_email_unverified(subject, message, from_email, to_email):
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    context = ssl._create_unverified_context()

    with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
        server.starttls(context=context)
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.sendmail(from_email, [to_email], msg.as_string())


@login_required
def change_application_status(request, pk, new_status):
    application = get_object_or_404(Application, pk=pk)
    user = request.user

    allowed_statuses = ['pending', 'approved', 'rejected']
    if new_status not in allowed_statuses:
        return HttpResponseForbidden("Недопустимый статус.")

    # Студент может только отменить свою заявку, если она в ожидании
    if user.role == 'student':
        if application.user != user or application.status != 'pending' or new_status != 'rejected':
            return HttpResponseForbidden("У вас нет прав для этого действия.")

    # Админ может всё
    elif user.role == 'admin':
        pass  # доступ разрешён

    else:
        return HttpResponseForbidden("Доступ запрещён.")

    # Обновляем статус заявки
    application.status = new_status
    application.save()

    # Обновляем привязку комнаты к пользователю и ManyToMany связь
    if new_status == 'approved':
        try:
            room = Room.objects.get(number=application.room_number)
            # Обновляем ForeignKey пользователя
            application.user.room = room
            application.user.save()

            # Добавляем пользователя в ManyToMany room.residents
            room.residents.add(application.user)
        except Room.DoesNotExist:
            # Если комната не найдена, сбрасываем связь
            if application.user.room:
                # Убираем пользователя из прошлой комнаты, если была
                application.user.room.residents.remove(application.user)
            application.user.room = None
            application.user.save()
    else:
        # Если статус не approved — удаляем пользователя из комнаты
        if application.user.room:
            application.user.room.residents.remove(application.user)
        application.user.room = None
        application.user.save()

    # Отправка email-уведомления
    subject = f"Статус вашей заявки: {application.get_status_display()}"
    message = (
        f"Здравствуйте, {application.user.username}!\n\n"
        f"Статус вашей заявки на поселение изменён на: {application.get_status_display()}.\n\n"
        "Вы можете проверить статус в своём аккаунте.\n\n"
        "С уважением,\n"
        "Команда общежития."
    )

    send_email_unverified(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        application.user.email
    )

    return redirect('application-detail', pk=pk)



@login_required
def reset_application_status(request, pk):
    application = get_object_or_404(Application, pk=pk)
    user = application.user  # Пользователь, подавший заявку

    application.status = 'pending'
    application.save()

    # Сброс комнаты
    user.room = None
    user.save()

    # Отправка email-уведомления
    subject = f"Статус вашей заявки: {application.get_status_display()}"
    message = (
        f"Здравствуйте, {user.username}!\n\n"
        f"Статус вашей заявки на поселение изменён на: {application.get_status_display()}.\n\n"
        "Вы можете проверить статус в своём аккаунте.\n\n"
        "С уважением,\n"
        "Команда общежития."
    )

    send_email_unverified(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        user.email
    )

    return redirect('application-detail', pk=pk)




@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        email = user.email
        username = user.username
        user.delete()

        # Отправка письма
        send_mail(
            subject='Ваш аккаунт был удалён',
            message=f'Здравствуйте, {username}!\n\nВаш аккаунт на сайте общежития был успешно удалён.\nЕсли это была ошибка — обратитесь в администрацию.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return redirect('login')
    

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@user_passes_test(is_admin)
def add_room(request):
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('floor-selector')  # или другой URL
    else:
        form = RoomForm()
    return render(request, 'add_room.html', {'form': form})