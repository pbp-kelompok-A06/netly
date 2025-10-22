from django.urls import path
from event.views import (
    show_events,
    event_detail,
    join_leave_event,
    join_event_ajax,
    create_event_ajax,
    edit_event_ajax,
    delete_event_ajax,
    get_event_json,
)

app_name = 'event'

urlpatterns = [
    path('', show_events, name='show_events'),
    path('<uuid:pk>/', event_detail, name='event_detail'),
    path('<uuid:pk>/join/', join_leave_event, name='join_leave_event'),
    path('ajax/join/<uuid:pk>/', join_event_ajax, name='join_event_ajax'),
    
    path('ajax/create/', create_event_ajax, name='create_event_ajax'),
    path('ajax/edit/<uuid:pk>/', edit_event_ajax, name='edit_event_ajax'),
    path('ajax/delete/<uuid:pk>/', delete_event_ajax, name='delete_event_ajax'),
    path('ajax/get/<uuid:pk>/', get_event_json, name='get_event_json'),         # untuk fetch data ke form edit
]