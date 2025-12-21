from django.urls import path
from admin_lapangan.views import (
    admin_dashboard,
    show_lapangan_list,
    lapangan_detail,
    create_lapangan_ajax,
    get_lapangan_json,
    edit_lapangan_ajax,
    delete_lapangan_ajax,
    show_jadwal_list,
    create_jadwal_ajax,
    get_jadwal_json,
    edit_jadwal_ajax,
    delete_jadwal_ajax,
    fetch_lapangan_list_ajax,  
    fetch_jadwal_list_ajax, 
    import_lapangan_data,
    get_all_lapangan_json,
    get_lapangan_detail_json,
    create_lapangan_flutter,
    create_lapangan_flutter,
    edit_lapangan_flutter,
    delete_lapangan_flutter,
    # Jadwal imports
    get_jadwal_by_lapangan,
    get_jadwal_detail,
    create_jadwal_flutter,
    edit_jadwal_flutter,
    delete_jadwal_flutter,
    toggle_availability_flutter,

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
    path('lapangan/ajax/fetch/', fetch_lapangan_list_ajax, name='fetch_lapangan_list_ajax'), 
    
    # Jadwal URLs
    path('lapangan/<uuid:lapangan_id>/jadwal/', show_jadwal_list, name='jadwal_list'),
    path('lapangan/<uuid:lapangan_id>/jadwal/ajax/create/', create_jadwal_ajax, name='create_jadwal_ajax'),
    path('lapangan/<uuid:lapangan_id>/jadwal/ajax/fetch/', fetch_jadwal_list_ajax, name='fetch_jadwal_list_ajax'),
    path('jadwal/ajax/get/<uuid:pk>/', get_jadwal_json, name='get_jadwal_json'),
    path('jadwal/ajax/edit/<uuid:pk>/', edit_jadwal_ajax, name='edit_jadwal_ajax'),
    path('jadwal/ajax/delete/<uuid:pk>/', delete_jadwal_ajax, name='delete_jadwal_ajax'),

    path('import-data/', import_lapangan_data, name="import_lapangan_data"),
    path('api/lapangan/', get_all_lapangan_json, name='get_all_lapangan_json'),
    path('api/lapangan/<uuid:pk>/', get_lapangan_detail_json, name='get_lapangan_detail_json'),
    path('create-flutter/', create_lapangan_flutter, name='create_lapangan_flutter'),
    path('edit-flutter/<uuid:lapangan_id>/', edit_lapangan_flutter, name='edit_lapangan_flutter'),
    path('delete-flutter/<uuid:lapangan_id>/', delete_lapangan_flutter, name='delete_lapangan_flutter'),

    # Jadwal API endpoints
    path('api/jadwal/<uuid:lapangan_id>/', get_jadwal_by_lapangan, name='get_jadwal_by_lapangan'),
    path('api/jadwal/detail/<uuid:jadwal_id>/', get_jadwal_detail, name='get_jadwal_detail'),
    
    # Jadwal Flutter endpoints
    path('jadwal/create-flutter/', create_jadwal_flutter, name='create_jadwal_flutter'),
    path('jadwal/edit-flutter/<uuid:jadwal_id>/', edit_jadwal_flutter, name='edit_jadwal_flutter'),
    path('jadwal/delete-flutter/<uuid:jadwal_id>/', delete_jadwal_flutter, name='delete_jadwal_flutter'),
    path('jadwal/toggle-availability/<uuid:jadwal_id>/', toggle_availability_flutter, name='toggle_availability_flutter'),
    path('api/my-lapangan/', get_all_lapangan_json, name='get_my_lapangan_json'),
]