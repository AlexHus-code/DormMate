from django.shortcuts import render
from .models import Room, Application
from .forms import ApplicationModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models.fields.files import FileField
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model


def delete_room_view(request, number):
    room = get_object_or_404(Room, number=number)
    if request.method == 'POST':
        room.delete()
        return redirect('floor-selector')  # або куди ти хочеш перенаправити після видалення
    return redirect('room-detail', number=number)


def floor_selector_view(request):
    # Отримуємо список унікальних поверхів
    floors = list(Room.objects.values_list('floor', flat=True).distinct().order_by('floor'))

    # Якщо кімнат немає — показуємо повідомлення
    if not floors:
        return render(request, 'index.html', {
            'floors': [],
            'rooms': [],
            'selected_floor': None,
            'has_rooms': False,
        })

    # Намагаємося отримати поверх із GET-запиту та привести до int
    try:
        selected_floor = int(request.GET.get('floor', floors[0]))
    except (ValueError, TypeError):
        selected_floor = floors[0]

    # Перевіряємо, чи існує такий поверх
    if selected_floor not in floors:
        selected_floor = floors[0]

    # Фільтруємо кімнати за вибраним поверхом
    rooms = Room.objects.filter(floor=selected_floor).order_by('number')

    return render(request, 'index.html', {
        'floors': floors,
        'rooms': rooms,
        'selected_floor': selected_floor,
        'has_rooms': rooms.exists(),
    })


@login_required
def form_view(request, room_number):
    form = ApplicationModelForm(initial={'room_number': room_number})
    return render(request, "form.html", {"form": form})


@login_required
def form_saving_view(request):
    if request.method == 'POST':
        submitted_form = ApplicationModelForm(request.POST, request.FILES)
        if submitted_form.is_valid():
            room_number = submitted_form.cleaned_data.get('room_number')

            # Перевірка: чи існує кімната
            if not Room.objects.filter(number=room_number).exists():
                messages.error(request, f"Кімната №{room_number} не існує.")
                return render(request, "form.html", {"form": submitted_form})

            application = submitted_form.save(commit=False)
            application.user = request.user
            application.save()

            # Передаємо ім'я користувача в шаблон
            return render(request, "thank_you.html", {
                "user": request.user  # <-- передаємо об'єкт користувача
            })

        return render(request, "form.html", {"form": submitted_form})

    submitted_form = ApplicationModelForm()
    return render(request, "form.html", {"form": submitted_form})


User = get_user_model()


def is_admin(user):
    return user.is_authenticated and user.role == 'admin'


def room_detail_view(request, number):
    room = get_object_or_404(Room, number=number)
    residents = room.residents.all()
    total_slots = room.capacity
    available_slots = total_slots - residents.count()

    # Підрахунок заявок зі статусом 'pending' на цю кімнату
    pending_applications_count = Application.objects.filter(
        room_number=room.number,
        status='pending'
    ).count()

    all_users = []
    if request.user.is_authenticated and request.user.role == 'admin':
        all_users = User.objects.filter(
            role='student',
            room__isnull=True
        ).exclude(id__in=residents.values_list('id', flat=True))

    context = {
        'room': room,
        'residents': residents,
        'total_slots': total_slots,
        'available_slots': available_slots,
        'all_users': all_users,
        'pending_applications_count': pending_applications_count,
    }
    return render(request, 'room_detail.html', context)


@user_passes_test(is_admin)
def add_resident_view(request, number):
    room = get_object_or_404(Room, number=number)

    # Фільтруємо лише студентів, які ще не живуть у цій кімнаті
    all_users = User.objects.filter(role='student').exclude(room=room)

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)

        if room.residents.count() >= room.capacity:
            messages.error(request, 'Кімната заповнена.')
        elif user in room.residents.all():
            messages.warning(request, 'Користувач уже живе в цій кімнаті.')
        else:
            room.residents.add(user)
            user.room = room
            user.save()
            messages.success(request, f'{user.username} додано до кімнати.')

        return redirect('room-detail', number=number)

    return render(request, 'rooms/room_detail.html', {
        'room': room,
        'all_users': all_users,
        'residents': room.residents.all(),
        # інші необхідні дані
    })


@user_passes_test(is_admin)
def remove_resident_view(request, number, user_id):
    room = get_object_or_404(Room, number=number)
    user = get_object_or_404(User, id=user_id)

    room.residents.remove(user)
    if user.room == room:
        user.room = None
        user.save()

    messages.success(request, f'{user.username} видалено з кімнати.')
    return redirect('room-detail', number=number)
