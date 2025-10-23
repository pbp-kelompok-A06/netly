from django.urls import path
from admin_lapangan.views import (
    admin_dashboard,
    show_lapangan_list,
    lapangan_detail,  # NEW
    create_lapangan_ajax,
    get_lapangan_json,
    edit_lapangan_ajax,
    delete_lapangan_ajax,
    show_jadwal_list,
    create_jadwal_ajax,
    get_jadwal_json,
    edit_jadwal_ajax,
    delete_jadwal_ajax,
)

app_name = 'admin_lapangan'

urlpatterns = [
    # Dashboard
    path('', admin_dashboard, name='dashboard'),
    
    # Lapangan URLs
    path('lapangan/', show_lapangan_list, name='lapangan_list'),
    path('lapangan/<uuid:pk>/', lapangan_detail, name='lapangan_detail'), 
    path('lapangan/ajax/create/', create_lapangan_ajax, name='create_lapangan_ajax'),
    path('lapangan/ajax/get/<uuid:pk>/', get_lapangan_json, name='get_lapangan_json'),
    path('lapangan/ajax/edit/<uuid:pk>/', edit_lapangan_ajax, name='edit_lapangan_ajax'),
    path('lapangan/ajax/delete/<uuid:pk>/', delete_lapangan_ajax, name='delete_lapangan_ajax'),
    
    # Jadwal URLs
    path('lapangan/<uuid:lapangan_id>/jadwal/', show_jadwal_list, name='jadwal_list'),
    path('lapangan/<uuid:lapangan_id>/jadwal/ajax/create/', create_jadwal_ajax, name='create_jadwal_ajax'),
    path('jadwal/ajax/get/<uuid:pk>/', get_jadwal_json, name='get_jadwal_json'),
    path('jadwal/ajax/edit/<uuid:pk>/', edit_jadwal_ajax, name='edit_jadwal_ajax'),
    path('jadwal/ajax/delete/<uuid:pk>/', delete_jadwal_ajax, name='delete_jadwal_ajax'),
]