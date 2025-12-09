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
    show_events_flutter,
    edit_event_flutter,
    create_event_flutter,
    join_event_flutter,
    delete_event_flutter,
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

    path('show-events-flutter/', show_events_flutter, name='show_events_flutter'),
    path('create-flutter/', create_event_flutter, name='create_event_flutter'),
    path('edit-flutter/<uuid:pk>/', edit_event_flutter, name='edit_event_flutter'),
    path('delete-flutter/<uuid:pk>/', delete_event_flutter, name='delete_event_flutter'),
    path('join-flutter/<uuid:pk>/', join_event_flutter, name='join_event_flutter'),
]