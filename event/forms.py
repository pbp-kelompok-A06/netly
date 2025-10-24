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

    def clean_end_date(self):
        start_date = self.cleaned_data.get('start_date')
        end_date = self.cleaned_data.get('end_date')

        # cek kedua tanggal valid
        if start_date and end_date:
            # cek apakah tanggal selesai sebelum tanggal mulai
            if end_date < start_date:
                raise forms.ValidationError(
                    "Tanggal selesai tidak boleh sebelum tanggal mulai.", 
                    code='invalid_date'
                    )
        return end_date