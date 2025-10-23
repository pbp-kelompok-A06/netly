from django.db import models
from authentication_user.models import UserProfile
import uuid
import os

def configure_lapangan_image_path(obj, filename):
    file_type = filename.split(".")[-1]
    filename = f"{obj.id}.{file_type}"
    return os.path.join('lapangan_images', filename)

class Lapangan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin_lapangan = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='lapangan_managed', default=1)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class JadwalLapangan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lapangan = models.ForeignKey(Lapangan, on_delete=models.CASCADE, related_name='jadwal')
    tanggal = models.DateField()
    start_main = models.TimeField()
    end_main = models.TimeField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.lapangan.name} - {self.tanggal} ({self.start_main} - {self.end_main})"

    class Meta:
        ordering = ['tanggal', 'start_main']
        unique_together = ['lapangan', 'tanggal', 'start_main']