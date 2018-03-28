from django.contrib.sitemaps import Sitemap
from .models import BlogPost
from django.utils import timezone


class ArticleSitemap(Sitemap):
    changefreq = "never"
    priority = 0.5

    def items(self):
        return BlogPost.objects.filter(displayed=True, publish_on__lte=timezone.now())

    def lastmod(self, obj):
        return obj.created_on