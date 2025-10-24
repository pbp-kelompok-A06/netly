from django.forms import ModelForm
from community.models import Forum, Forum_Post

class ForumForm(ModelForm):
    class Meta:
        model = Forum
        fields = [
            "title",
            "description"
        ]

class ForumPostForm(ModelForm):
    class Meta:
        model = Forum_Post
        fields = [
            "header",
            "content"
        ]
