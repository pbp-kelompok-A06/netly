from django.urls import path
from . import views

app_name = 'homepage'

urlpatterns = [
    path('', views.index, name='homepage'),
    path("court/<uuid:court_id>/", views.court_detail, name="court-detail"),
    path('search-courts/', views.search_courts_ajax, name='search-courts-ajax'),
    path("filter-courts/", views.filter_courts, name="filter-courts"),
]

