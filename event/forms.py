from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        # field yang mau kita show di formnya
        fields = ['name', 
                  'lapangan',
                  'description',
                  'start_date',
                  'end_date',
                  'location',
                  'max_participants',
                  'image_url'
                  ]
        