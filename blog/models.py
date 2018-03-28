from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from tinymce.models import HTMLField
from django.utils.text import slugify
from django.urls import reverse
from .utils2 import text_content
import markdown


class Profile(models.Model):
    # 0: reader, 1: contributors, 2: admin, 3: debug
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    avatar = models.ImageField(upload_to='user_avatars', null=True, blank=True)
    role = models.IntegerField(default=0)
    link = models.CharField(max_length=50, default='', blank=True)
    twitter_link = models.CharField(max_length=30, default='', blank=True)
    public_email = models.CharField(max_length=40, default='', blank=True)
    quora_link = models.CharField(max_length=30, default='', blank=True)
    bio = models.CharField(max_length=500, default='', blank=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.link:
            self.link = slugify(self.user.username)
        if not self.avatar:
            self.avatar = 'blog_embeds/noprofile.png'
        super().save(*args, **kwargs)


class Notification(models.Model):
    profiles = models.ManyToManyField(Profile)
    detail = models.CharField(max_length=150)

    def __str__(self):
        return self.detail


class BlogPost(models.Model):
    link = models.CharField(max_length=100, unique=True, default='', blank=True)
    title = models.CharField(max_length=200)
    cover = models.ImageField(upload_to='blog_covers', null=True, blank=True)
    authors = models.ManyToManyField(Profile, related_name='posts')
    created_on = models.DateTimeField(default=timezone.now)
    publish_on = models.DateTimeField(default=timezone.now)
    displayed = models.BooleanField(
        default=True,
        help_text='http://techknack.in:8000/hidden-937987398127918/<link of the post>')
    content_md = models.TextField(null=True, blank=True)
    snippet = models.CharField(max_length=200, default='', blank=True)
    visit_count = models.IntegerField(default=0)
    popularity = models.IntegerField(default=0)
    content = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'

    def __str__(self):
        if not self.displayed:
            return '[HIDDEN]: ' + self.title
        return '%s' % (self.title)

    def save(self, *args, **kwargs):
        if not self.link:
            self.link = slugify(self.title)
        if not self.snippet:
            self.snippet = text_content(self.content)[:160] + '...'
        if not self.cover:
            self.cover = 'blog_embeds/typelogo.jpg'
        super().save(*args, **kwargs)
        author = self.authors.all()
        if author:
            author = author[0]
        else:
            return
        if author.role == 0:
            author.role = 1
            author.save()

    def get_absolute_url(self):
        return reverse('blogposts', kwargs={'link': self.link})

    def get_popularity(self):
        count = self.comments.all().count()
        return self.visit_count + count


class BlogEmbed(models.Model):
    # blog = models.ForeignKey(BlogPost, on_delete=models.DO_NOTHING)
    content = models.FileField(upload_to='blog_embeds')

    class Meta:
        verbose_name = 'Embedded File'
        verbose_name_plural = 'Embedded Files'


class MediaFiles(models.Model):
    content = models.FileField(upload_to='media_files')

    class Meta:
        verbose_name = 'Media File'


class BlogTag(models.Model):
    post = models.ManyToManyField(BlogPost, related_name='tags')
    name = models.CharField(max_length=30)
    link = models.CharField(max_length=100, unique=True, default='', blank=True)
    main_cat = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Blog Topic'
        verbose_name_plural = 'Blog Topics'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.link:
            self.link = slugify(self.name)
        super().save(*args, **kwargs)


class BlogComment(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    content = models.TextField()
    created_on = models.DateTimeField()

    class Meta:
        verbose_name = 'Blog Comment'
        verbose_name_plural = 'Blog Comments'

    def __str__(self):
        return self.content[:50]

    def edit_comment(self, content):
        self.content = content
        self.save()

    def get_time(self):
        pass


class ReadLater(models.Model):
    blog = models.ForeignKey(BlogPost, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self):
        return 'blog: %s\treader: %s' % (self.blog.title, self.user.username)


class Tweet(models.Model):    # Discussions
    author = models.CharField(max_length=40)
    author_handle = models.CharField(max_length=40)
    author_pic = models.CharField(max_length=400, null=True, blank=True)
    link = models.CharField(max_length=400)
    content = models.CharField(max_length=200)
    posted_on = models.DateTimeField()
    publish_on = models.DateTimeField(default=timezone.now)
    displayed = models.BooleanField(default=True)

    def __str__(self):
        return self.content[:60]

    def save(self, *args, **kwargs):
        if not self.author_pic:
            self.author_pic = '/media/blog_embeds/mainlogo.jpeg'
        super().save(*args, **kwargs)


class TwitterTopic(models.Model):
    term = models.CharField(max_length=30)
    basis = models.IntegerField(
        default=0, help_text='0 for popularity, 1 for recent, 2 for mixed')
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.term


class Event(models.Model):    # Codebase
    subject = models.CharField(max_length=50, null=True)
    content = models.CharField(max_length=250, null=True, blank=True)
    event_time = models.CharField(max_length=30, null=True, blank=True)
    publish_on = models.DateTimeField(default=timezone.now)
    displayed = models.BooleanField(default=True)
    link = models.CharField(max_length=200, default='')
    pic = models.ImageField(upload_to='event_pictures', null=True, blank=True)
    location = models.CharField(max_length=60, null=True, blank=True)
    real_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        if self.content:
            return self.content[:60]
        if self.link:
            return self.link
        return 'Event object'

    def save(self, *args, **kwargs):
        if not self.pic:
            self.pic = 'blog_embeds/mainlogo.jpeg'
        super().save(*args, **kwargs)


class EventInternal(models.Model):
    raw_link = models.CharField(max_length=200, null=True, blank=True)
    date = models.CharField(max_length=30, null=True, blank=True)
    subject = models.CharField(max_length=60)
    location = models.CharField(max_length=60, null=True, blank=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return self.subject



class NavTabs(models.Model):
    name = models.CharField(max_length=25)
    link = models.CharField(max_length=40)
    glyphicon = models.CharField(max_length=25)

    def __str__(self):
        return self.name


'''
class BlogPostInternal(models.Model):
    post = models.OneToOneField(
        BlogPost, on_delete=models.DO_NOTHING, related_name='internal')
    created_on = models.DateTimeField(default=timezone.now)
    visit_count = models.IntegerField(default=0)
    popularity = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Blog Post [Internal]'
        verbose_name_plural = 'Blog Posts [Internal]'

    def __str__(self):
        return self.post.title
'''


class NewsTopic(models.Model):
    topic = models.CharField(max_length=40)
    priority = models.IntegerField(default=0)
    auto_expire_on = models.DateTimeField(null=True, blank=True)
    start_from = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'News Topic'

    def __str__(self):
        return self.topic


class News(models.Model):
    topic = models.ForeignKey(NewsTopic, on_delete=models.CASCADE)
    content = models.CharField(max_length=160)
    link = models.URLField(null=True, blank=True)
    posted_on = models.DateTimeField(default=timezone.now)
    new = models.BooleanField(default=True)
    cycle = models.IntegerField()

    pic = models.ImageField(upload_to='news_pics', null=True, blank=True)
    displayed = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'News Item'
        verbose_name_plural = 'News Items'

    def __str__(self):
        return self.content

    def save(self, *args, **kwargs):
        if not self.pic:
            self.pic = 'blog_embeds/mainlogo.jpeg'
        super().save(*args, **kwargs)


class Log(models.Model):
    time = models.DateTimeField(default=timezone.now)
    message = models.CharField(max_length=200)
    content = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.time.strftime('%B %d, %I:%M:%S %p') + ', ' + self.message


class Site(models.Model):
    about = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Site Meta'
        verbose_name_plural = 'Site Meta'


class SiteVisit(models.Model):
    ip_address1 = models.GenericIPAddressField(null=True)
    ip_address2 = models.GenericIPAddressField(null=True)
    time = models.DateTimeField(default=timezone.now)
    referrer = models.CharField(max_length=150, null=True)
    city = models.CharField(max_length=40, null=True)
    region_code = models.CharField(max_length=4, null=True)
    region = models.CharField(max_length=40, null=True)
    country_name = models.CharField(max_length=40, null=True)
    country = models.CharField(max_length=5, null=True)
    postal = models.CharField(max_length=15, null=True)
    latitude = models.DecimalField(max_digits=8, decimal_places=4, null=True)
    longitude = models.DecimalField(max_digits=8, decimal_places=4, null=True)
    timezone = models.CharField(max_length=30, null=True)
    asn = models.CharField(max_length=15, null=True)
    org = models.CharField(max_length=100, null=True)
    user_agent = models.CharField(max_length=150, null=True)

    def __str__(self):
        text = ''
        cols = [
            self.time, self.ip_address1, self.city, self.region,
            self.country_name, self.user_agent, self.org
        ]
        for col in cols:
            if col:
                text += str(col) + ', '
        return text


class SslProxy(models.Model):
    discovered_on = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=30, unique=True)
    not_working = models.BooleanField(default=False)
    working = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Ssl Proxies'

    def __str__(self):
        return self.ip_address + ', working: %s, not working: %s' % (
            str(self.working), str(self.not_working))

