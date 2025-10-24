from django import forms
from .models import Lapangan, JadwalLapangan
from datetime import datetime

class LapanganForm(forms.ModelForm):
    class Meta:
        model = Lapangan
        fields = ['name', 'location', 'description', 'price', 'image']

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price < 0:
            raise forms.ValidationError('Harga tidak boleh negatif.')
        return price


class JadwalLapanganForm(forms.ModelForm):
    class Meta:
        model = JadwalLapangan
        fields = ['tanggal', 'start_main', 'end_main', 'is_available']

    def clean(self):
        cleaned_data = super().clean()
        tanggal = cleaned_data.get('tanggal')
        start_main = cleaned_data.get('start_main')
        end_main = cleaned_data.get('end_main')

        if tanggal and tanggal < datetime.now().date():
            raise forms.ValidationError('Tanggal tidak boleh di masa lalu.')

        if start_main and end_main:
            if start_main >= end_main:
                raise forms.ValidationError('Waktu mulai harus lebih awal dari waktu selesai.')

        return cleaned_data