from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('rooms/<int:number>/', views.room_detail_view, name='room-detail'),
    path("rooms/", views.floor_selector_view, name="floor-selector"),
    path("rooms/<int:room_number>/form/", views.form_view, name="room-form"),
    path("rooms/form-thank-you/", views.form_saving_view, name="form-thank-you"),
    path("rooms/applications/", views.aplication_list_view, name="applications"),
    path('rooms/<int:number>/delete/', views.delete_room_view, name='delete-room'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)