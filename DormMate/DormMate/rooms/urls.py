from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Список комнат по этажам
    path("rooms/", views.floor_selector_view, name="floor-selector"),

    # Детали комнаты
    path("rooms/<int:number>/", views.room_detail_view, name="room-detail"),

    # Подать заявление на комнату
    path("rooms/<int:room_number>/form/", views.form_view, name="room-form"),
    path("rooms/form-thank-you/", views.form_saving_view, name="form-thank-you"),
    # Удалить комнату
    path("rooms/<int:number>/delete/", views.delete_room_view, name="delete-room"),

    # ✅ Новое: Добавить жителя в комнату
    path("rooms/<int:number>/add-resident/", views.add_resident_view, name="add-resident"),

    # ✅ Новое: Удалить жителя из комнаты
    path("rooms/<int:number>/remove-resident/<int:user_id>/", views.remove_resident_view, name="remove-resident"),
]

# Медиафайлы в режиме отладки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
