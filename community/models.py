from django.db import models
from authentication_user.models import UserProfile
import uuid


class Forum(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator_id = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="forum_creator")
    member = models.ManyToManyField(UserProfile, blank=True, related_name="forum_member")
    title = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.title

class Forum_Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="forum_post_user")
    forum_id = models.ForeignKey(Forum, on_delete=models.CASCADE)
    header = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.header