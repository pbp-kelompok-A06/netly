from django.utils import timezone
from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from authentication_user.models import UserProfile

#liat app sebelah
# dummy
from admin_lapangan.models import Lapangan
from admin_lapangan.models import JadwalLapangan as Jadwal

import uuid

# Create your models here.
# asumsi setiap booking hanya untuk 1 lapangan dan bisa lebih dari 1 jadwal
class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lapangan_id = models.ForeignKey(Lapangan, on_delete=models.CASCADE)
    jadwal = models.ManyToManyField(Jadwal)
    user_id = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    status_book = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    #hitung total_price
    def total_price(self):
        return self.lapangan_id.price * self.jadwal.count()
    
    #b = Booking(lapangan=lap, user=u)
    # b.save()              # wajib dulu
    # b.jadwal.add(j1, j2)
    #j1.isbooked = True
    #j1.save()
    
    
    def is_expired(self):
        now = timezone.now()
        for j in self.jadwal.all():
            waktu_selesai = datetime.combine(j.tanggal, j.end_main)
            #maksud make aware di sini yaitu 
            waktu_selesai = timezone.make_aware(waktu_selesai)
            if waktu_selesai > now:
                return False  # masih ada jadwal yang belum lewat
        if(self.status_book == 'pending'):
            self.status_book = 'failed'
            self.save()
        return True  # semua jadwal sudah lewat

    def __str__(self):
        for j in self.jadwal.all():
            print(j.waktu_mulai, j.waktu_selesai)

        return f"{self.lapangan_id.nama} booked by {self.user_id.username} on {self.jadwal.all()}"