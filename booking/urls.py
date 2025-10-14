from booking.views import create_booking
from django.urls import path
urlpatterns = [
    path('create_booking/', create_booking, name='create_booking'),
    ]