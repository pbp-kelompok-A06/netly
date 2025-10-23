from booking.views import booking_detail, create_booking, complete_booking, show_json, show_json_by_id, show_booking_list, test
from django.urls import path
app_name = 'booking'
urlpatterns = [
    path('create_booking/', create_booking, name='create_booking'),
    path('booking_detail/<uuid:booking_id>/', booking_detail, name='booking_detail'),
    path('booking_detail/<uuid:booking_id>/complete/', complete_booking, name='complete_booking'),
    path('show_json/', show_json, name='show_json'),
    path('show_json/<uuid:booking_id>/', show_json_by_id, name='show_json_by_id'),
    path('booking_list/', show_booking_list, name='show_booking_list'),
    path('test/', test, name='test'),
    ]   
