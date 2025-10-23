from django.db import models
from authentication_user.models import UserProfile
import uuid


class Forum(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator_id = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="forum_creator")
    member = models.ManyToManyField(UserProfile, blank=True, related_name="forum_member", null=True)
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
    

class Forum_Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="forum_comment_user")
    forum_id = models.ForeignKey(Forum, on_delete=models.CASCADE)
    forum_post_id = models.ForeignKey(Forum_Post, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return f"Comment.{self.user_id}"
   