from django.shortcuts import render
from .models import Room, Application
from .forms import  ApplicationModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models.fields.files import FileField
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages






def room_detail_view(request, number):
    room = get_object_or_404(Room, number=number)
    residents = room.residents.all()  # related_name='shared_rooms'

    total_slots = room.capacity
    available_slots = total_slots - residents.count()

    has_pending_application = False
    if request.user.is_authenticated and request.user.role == 'student':
        has_pending_application = Application.objects.filter(user=request.user, status='pending').exists()

    context = {
        'room': room,
        'residents': residents,
        'total_slots': total_slots,
        'available_slots': available_slots,
        'has_pending_application': has_pending_application,
    }
    return render(request, 'room_detail.html', context)


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
    rooms = Room.objects.filter(floor=selected_floor)

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
  