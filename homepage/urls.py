from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='homepage'),
    path("court/<int:court_id>/", views.court_detail, name="court-detail"),
    path('booking/<int:court_id>/', views.booking_placeholder, name='booking-placeholder'),
    path('search-courts/', views.search_courts_ajax, name='search-courts-ajax'),
    path("filter-courts/", views.filter_courts, name="filter-courts"),
]

