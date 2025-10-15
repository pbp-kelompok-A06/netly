from django.urls import path
from event.views import (
    show_events,
    event_detail,
    create_event,
    edit_event,
    delete_event,
    join_leave_event,
    join_event_ajax
)

app_name = 'event'

urlpatterns = [
    path('', show_events, name='show_events'),
    path('create/', create_event, name='create_event'),
    path('<uuid:pk>/', event_detail, name='event_detail'),
    path('<uuid:pk>/edit/', edit_event, name='edit_event'),
    path('<uuid:pk>/delete/', delete_event, name='delete_event'),
    path('<uuid:pk>/join/', join_leave_event, name='join_leave_event'),
    path('ajax/join/<uuid:pk>/', join_event_ajax, name='join_event_ajax'),
]