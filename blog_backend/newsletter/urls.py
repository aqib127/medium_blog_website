from django.urls import path
from . import views

app_name = 'newsletter'

urlpatterns = [
    path('subscribe/', views.subscribe, name='subscribe'),
    path('confirm/', views.confirm, name='confirm-post'),
    path('confirm/<str:token>/', views.confirm, name='confirm'),
    path('unsubscribe/', views.unsubscribe, name='unsubscribe-post'),
    path('unsubscribe/<uuid:token>/', views.unsubscribe, name='unsubscribe'),
    path('status/', views.status_view, name='status'),
    path('stats/', views.stats, name='stats'),
    path('send/', views.send_to_all, name='send-to-all'),
]
