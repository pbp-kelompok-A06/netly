from booking.views import booking_detail, create_booking, complete_booking
from django.urls import path
urlpatterns = [
    path('create_booking/', create_booking, name='create_booking'),
    path('booking_detail/<str:booking_id>/', booking_detail, name='booking_detail'),
    path('booking_detail/<str:booking_id>/complete/', complete_booking, name='complete_booking'),
    ]