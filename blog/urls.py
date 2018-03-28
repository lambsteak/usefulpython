from django.urls import path
from django.contrib.sitemaps.views import sitemap
from .sitemap import ArticleSitemap
from . import views

sitemaps = {'blog': ArticleSitemap()}
urlpatterns = [
    path('blog/<link>/', views.blogposts, name='blogposts'),
    path('categories/<name>/', views.categories, name='categories'),
    path('columnists/<name>/', views.columnists, name='columnists'),
    path('blogcomments/<int:pk>', views.blogcomments, name='blogcomments'),
    path('login/', views.login_view, name='login_view'),
    path('signup/', views.signup_view, name='signup_view'),
    path('logout/', views.logout_view, name='logout_view'),
    path('account/', views.account, name='account'),
    path('blog/', views.blog, name='blog'),
    path('discussions/', views.tweets, name='tweets'),
    path('news/', views.news, name='news'),
    path('tools/', views.tools, name='events'),
    # path('contribute/', views.contribute, name='contribute'),
    # path('contribute/<link>', views.contribute_link, name='contribute_link'),
    path('search/', views.search, name='search'),
    path('about/', views.about, name='about'),
    path('hidden-937987398127918/<link>', views.hidden_post, name='hidden_post'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
    path('login2', views.login2, name='login2'),
    path('privacypolicy/', views.privacypolicy, name='privacypolicy'),
    path('termsofservice/', views.tos, name='termsofservice'),
    path('testmail', views.test_mail, name='testmail'),

    path('api_ssls/', views.api_ssls, name='api_ssls'),
    path('api_mobile_data_mobile_end/', views.api_mobile_data_mobile_end,
         name='api_mobile_data_mobile_end'),
    path('api_mobile_data_server_end/', views.api_mobile_data_server_end,
         name='api_mobile_data_server_end'),
    path('', views.index, name='index'),
]