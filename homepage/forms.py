from django import forms
from .models import LapanganFavorit

class FavoriteForm(forms.ModelForm):
    class Meta:
        model = LapanganFavorit
        fields = ['label']
        widgets = {
            'label': forms.Select(attrs={'class': 'border border-gray-300 rounded-lg p-2 w-full'})
        }