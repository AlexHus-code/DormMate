from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),  # ← оставь только эту
    path('account/', views.account_view, name='account'),
    path('welcome/', login_required(lambda request: render(request, 'welcome.html')), name='welcome'),
    path('create-admin/', views.create_admin_view, name='create-admin'),
    path('users/', login_required(views.user_list_view), name='user-list'),
    path('applications/', login_required(views.application_list_view), name='application-list'),
    path('applications/<int:pk>/', views.application_detail_view, name='application-detail'),
    path('applications/<int:pk>/status/<str:new_status>/', views.change_application_status, name='change-application-status'),
    path('applications/<int:pk>/reset/', views.reset_application_status, name='application-reset-status'),
    path('delete-account/', views.delete_account, name='delete-account'),
    path('rooms/add/', views.add_room, name='add-room'),
]
