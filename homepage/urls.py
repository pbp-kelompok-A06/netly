from django.urls import path
from . import views
from homepage.views import index, api_get_all_courts, proxy_image

app_name = 'homepage'

urlpatterns = [
    path('', views.index, name='homepage'),
    path("court/<uuid:court_id>/", views.court_detail, name="court-detail"),
    
    path('favorites/', views.favorite_page_html, name='favorite-list'),
    
    path('web/favorites/add/<uuid:court_id>/', views.web_add_favorite, name='web-add-favorite'),

    path('api/courts/', views.api_get_all_courts, name='api-all-courts'),
    path('api/court/<uuid:court_id>/', views.api_get_court_detail, name='api-court-detail'),
    
    path('api/favorites/', views.api_get_favorites, name='api-favorites-list'),
    path('api/favorites/add/<uuid:court_id>/', views.api_add_favorite, name='api-add-favorite'),
    path('api/favorites/update/<uuid:favorite_id>/', views.api_update_favorite, name='api-update-favorite'),
    path('api/favorites/remove/<uuid:favorite_id>/', views.api_remove_favorite, name='api-remove-favorite'),
    path('api/favorites/toggle/<uuid:court_id>/', views.api_toggle_favorite, name='api-toggle-favorite'),

    path('search-courts/', views.search_courts_ajax, name='search-courts-ajax'),
    path("filter-courts/", views.filter_courts, name="filter-courts"),
    path('proxy-image/', proxy_image, name='proxy_image'),
]