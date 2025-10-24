import uuid
from django.db import models
from django.contrib.auth.models import User
from authentication_user.models import UserProfile

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # admin pembuat event
    admin = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='event_admin')
    # relasi ke lapangan
    # lapangan = models.ForeignKey('lapangan.Lapangan', on_delete=models.CASCADE, related_name='events_lapangan')
    # peserta event, 1 peserta bisa join banyak event, 1 event bisa diikuti banyak peserta -> many to many
    participant = models.ManyToManyField(UserProfile, related_name='events_participant', blank=True)

    # event's detail
    name = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    location = models.CharField(max_length=100)
    image_url = models.URLField(blank=True, null=True)
    max_participants = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
