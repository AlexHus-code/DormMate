from django.shortcuts import render
from .models import Room, Application
from .forms import  ApplicationModelForm
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
        return redirect('floor-selector')  # или куда ты хочешь перенаправить после удаления
    return redirect('room-detail', number=number)



def floor_selector_view(request):
    # Получаем все доступные этажи с комнатами
    floors = Room.objects.values_list('floor', flat=True).distinct().order_by('floor')

    # Если комнат совсем нет — передаём None
    if not floors:
        return render(request, 'index.html', {
            'floors': [],
            'rooms': None,
            'selected_floor': None,
            'has_rooms': False,
        })

    # Выбираем этаж — либо из запроса, либо первый в списке
    selected_floor = request.GET.get('floor') or floors[0]

    # Сортировка по номеру комнаты
    rooms = Room.objects.filter(floor=selected_floor).order_by('number')

    return render(request, 'index.html', {
        'floors': floors,
        'rooms': rooms,
        'selected_floor': selected_floor,
        'has_rooms': True,
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
            
            # Проверяем, существует ли комната с таким номером
            if not Room.objects.filter(number=room_number).exists():
                messages.error(request, f"Комната №{room_number} не существует.")
                return render(request, "form.html", {"form": submitted_form})

            application = submitted_form.save(commit=False)
            application.user = request.user
            application.save()
            return render(request, "thank_you.html")
        else:
            return render(request, "form.html", {"form": submitted_form})
    else:
        submitted_form = ApplicationModelForm()
        return render(request, "form.html", {"form": submitted_form})



def aplication_list_view(request):
    applications = Application.objects.all()
    file_fields = [
        field.name for field in Application._meta.get_fields()
        if isinstance(field, FileField)
    ]

    apps_with_files = []
    for app in applications:
        files = []
        for field in file_fields:
            file = getattr(app, field)
            if file:
                files.append({
                    'label': field.replace('_', ' ').capitalize(),
                    'url': file.url
                })
        apps_with_files.append({
            'id': app.id,
            'room_number': app.room_number,
            'comment': app.comment,
            'files': files,
        })

    return render(request, 'applications.html', {
        'applications': apps_with_files,
    })
  
User = get_user_model()

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

def room_detail_view(request, number):
    room = get_object_or_404(Room, number=number)
    residents = room.residents.all()
    total_slots = room.capacity
    available_slots = total_slots - residents.count()

    all_users = []
    if request.user.is_authenticated and request.user.role == 'admin':
        # Студенты без комнаты, которые ещё не добавлены в эту
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
    }
    return render(request, 'room_detail.html', context)

@user_passes_test(is_admin)
def add_resident_view(request, number):
    room = get_object_or_404(Room, number=number)

    # Фильтруем только студентов, которые ещё не живут в этой комнате
    all_users = User.objects.filter(role='student').exclude(room=room)

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)

        if room.residents.count() >= room.capacity:
            messages.error(request, 'Комната заполнена.')
        elif user in room.residents.all():
            messages.warning(request, 'Пользователь уже живёт в этой комнате.')
        else:
            room.residents.add(user)
            user.room = room
            user.save()
            messages.success(request, f'{user.username} добавлен в комнату.')

        return redirect('room-detail', number=number)

    return render(request, 'rooms/room_detail.html', {
        'room': room,
        'all_users': all_users,
        'residents': room.residents.all(),
        # другие необходимые данные
    })

@user_passes_test(is_admin)
def remove_resident_view(request, number, user_id):
    room = get_object_or_404(Room, number=number)
    user = get_object_or_404(User, id=user_id)

    room.residents.remove(user)
    if user.room == room:
        user.room = None
        user.save()

    messages.success(request, f'{user.username} удалён из комнаты.')
    return redirect('room-detail', number=number)