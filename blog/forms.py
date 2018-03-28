from tinymce.widgets import TinyMCE
from .models import BlogPost, Site
from django.forms import ModelForm, CharField


class BlogForm(ModelForm):
    # body = CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 80}))
    exclude = []

    class Meta:
        model = BlogPost
        exclude = []


class SiteForm(ModelForm):
    body = CharField(widget=TinyMCE(attrs={'cols':80, 'rows': 60}))
    exclude = []

    class Meta:
        model = Site
        exclude = []