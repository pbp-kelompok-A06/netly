from django import forms
from django.utils.html import strip_tags
from community.models import Forum, Forum_Post

class ForumForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = [
            "title", 
            "description"
        ]

    def clean_title(self):
        title = self.cleaned_data.get("title", "")
        return strip_tags(title)

    def clean_description(self):
        description = self.cleaned_data.get("description", "")
        return strip_tags(description)


class ForumPostForm(forms.ModelForm):
    class Meta:
        model = Forum_Post
        fields = [
            "header", 
            "content"
        ]

    def clean_header(self):
        header = self.cleaned_data.get("header", "")
        return strip_tags(header)

    def clean_content(self):
        content = self.cleaned_data.get("content", "")
        return strip_tags(content)
