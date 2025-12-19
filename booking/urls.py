from booking.views import booking_detail, create_booking, complete_booking, show_json, show_json_by_id, show_booking_list, test, show_create_booking, delete_booking, get_booking_data_flutter, get_jadwal_detail_json, create_booking_flutter, check_admin, get_lapangan_detail_json
from django.urls import path
app_name = 'booking'
urlpatterns = [
    path('create_booking_flutter/', create_booking_flutter, name='create_booking_flutter'),
    path('create_booking/', create_booking, name='create_booking'),
    path('show_create_booking/<uuid:lapangan_id>/', show_create_booking, name='show_create_booking'),
    path('get_booking_data_flutter/<uuid:lapangan_id>/', get_booking_data_flutter, name='get_booking_data_flutter'),
    path('booking_detail/<uuid:booking_id>/', booking_detail, name='booking_detail'),
    path('booking_detail/<uuid:booking_id>/complete/', complete_booking, name='complete_booking'),
    path('show_json_id/<uuid:booking_id>/', show_json_by_id, name='show_json_by_id'),
    path('show_json/', show_json, name='show_json'),    
    path('booking_list/', show_booking_list, name='show_booking_list'),
    path('delete_booking/<uuid:booking_id>/', delete_booking, name='delete_booking'),
    path('get_jadwal_detail_json/<uuid:pk>/', get_jadwal_detail_json, name='get_jadwal_detail_json'),
        
    path('test/', test, name='test'),
    path('check_admin/', check_admin, name='check_admin'),
    path('get_lapangan_detail_json/<uuid:pk>/', get_lapangan_detail_json, name="get_lapangan_detail_json")
]   
