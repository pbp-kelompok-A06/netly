from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        # field yang mau kita show di formnya
        fields = ['name', 
                #   'lapangan', tunggu
                  'description',
                  'start_date',
                  'end_date',
                  'location',
                  'max_participants',
                  'image_url'
                  ]
        # input tanggal with calendar
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }