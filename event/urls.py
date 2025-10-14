from django.urls import path
from event.views import (
    show_events,
    event_detail,
    create_event,
    edit_event
)

app_name = 'event'

urlpatterns = [
    path('', show_events, name='show_events'),
    path('create/', create_event, name='create_event'),
    path('<uuid:pk>/', event_detail, name='event_detail'),
    path('<uuid:pk>/edit/', edit_event, name='edit_event'),
]