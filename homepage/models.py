import uuid
from django.db import models
from django.contrib.auth.models import User
from admin_lapangan.models import Lapangan 

class LapanganFavorit(models.Model):
    class LabelChoices(models.TextChoices):
        DEKAT_RUMAH = 'Rumah', 'Dekat Rumah'
        DEKAT_KANTOR = 'Kantor', 'Dekat Kantor'
        LAINNYA = 'Lainnya', 'Lainnya'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lapangan = models.ForeignKey(Lapangan, on_delete=models.CASCADE)
    
    label = models.CharField(
        max_length=20, 
        choices=LabelChoices.choices, 
        default=LabelChoices.LAINNYA
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'lapangan')