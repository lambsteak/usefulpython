from django.contrib import admin
from .models import BlogPost, BlogTag, BlogComment, BlogEmbed, Tweet, News, Event, Profile
from .models import NewsTopic, Log, SiteVisit, Site, SslProxy, EventInternal, TwitterTopic
from .forms import SiteForm

admin.site.site_header = 'TechKnack Admin'
admin.site.site_title = 'Administration | TechKnack'
# admin.site.index_title = 'TechKnack Admnistration'

class TagInline(admin.TabularInline):
    model = BlogTag.post.through
    extra = 2


class BlogAdmin(admin.ModelAdmin):
    # form = BlogForm()

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'authors':
            kwargs["queryset"] = Profile.objects.filter(user=request.user)
        return super(BlogAdmin, self).formfield_for_manytomany(
            db_field, request, **kwargs)


class SiteAdmin(admin.ModelAdmin):
    form = SiteForm()


class BlogAdmin(admin.ModelAdmin):
    exclude = ('visit_count', 'popularity')
    inlines = [TagInline]
    list_filter = ['displayed', ('authors', admin.RelatedOnlyFieldListFilter)]
    list_display = ['title', 'get_author', 'visit_count', 'publish_on', 'displayed']
    search_fields = ['title']

    def get_author(self, obj):
        return obj.authors.all()[0].name
    get_author.short_description = 'Author'


admin.site.register(BlogPost, BlogAdmin)
admin.site.register([
    BlogTag, BlogComment, BlogEmbed, Tweet, News, Event, Profile,
    NewsTopic, Log, Site, SslProxy, TwitterTopic
])
