from django.db import models
from django.contrib.auth.models import User
import uuid, os

# Create your models here.

def configure_image_path(obj, filename):
    file_type = filename.split(".")[-1]
    username = obj.user.username.strip()
    filename = f"{obj.id}.{file_type}"
    return os.path.join('profile_pics', username, filename)

class UserProfile(models.Model):

    role_option = [
        ('admin', 'Admin'), # yang tampil ke web nanti 'Admin'
        ('user', 'Player')  # yang tampil ke web nanti 'Player'
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile") # reference ke model user; jadi satu user punya satu profile

    fullname = models.CharField(max_length=200, null=False)
    role = models.CharField(max_length=20, choices=role_option, default='user_player')
    location = models.CharField(max_length=255, null=True, blank=True)
    
    profile_picture = models.ImageField(upload_to=configure_image_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.username
