from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

urlpatterns = [
    path('edit-profile/', views.edit_profile, name='edit-profile'),
    path('petition/create/', views.create_petition_view, name='create-petition'),
    path('petition/<int:petition_id>/', views.petition_detail_view, name='petition-detail'),
    path('petition/', views.petition_list_view, name='petition-list'),
    path('petition/vote/<int:petition_id>/', views.vote_for_petition, name='vote-petition'),
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
    path('news/', views.news_list, name='news-list'),
    path('news/create/', views.create_news, name='create-news'),
    path('news/delete/<int:news_id>/', views.delete_news, name='delete-news'),
]
