import json
from itertools import chain
from random import sample
# from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from .models import BlogPost, BlogComment, Profile, News, Tweet, Event, BlogTag
from .models import SiteVisit, NewsTopic, Site, SslProxy
from .models import MobileDataStat
from django.http import Http404, JsonResponse, HttpResponse
from django.utils import timezone
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.conf import settings
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from .tasks import send_async_mail


def context_decorator(fn):
    def decorated_fn(*args, **kwargs):
        request = args[0]
        if (fn.__name__ != 'search') and request.GET.get('searchquery'):
            return redirect('/search?searchquery=%s' % request.GET['searchquery'])
        newstopics = NewsTopic.objects.filter(active=True).order_by(
            'priority'
        ).values_list('topic', flat=True)
        hm_topics = len(newstopics)
        if hm_topics == 0:
            per_topic = 0
        else:
            per_topic = (5 / hm_topics) + 1
        newslist = []
        for topic in newstopics:
            topicnews = News.objects.filter(topic__topic=topic).order_by(
                '-posted_on')[:per_topic]
            newslist = list(chain(newslist, topicnews))
        # news = News.objects.order_by('-posted_on').all()[:5]
        news = newslist
        pop_posts = BlogPost.objects.order_by(
            '-popularity').filter(displayed=True, publish_on__lte=timezone.now())[:5]
        tweets = Tweet.objects.order_by('-posted_on')[:4]
        if fn.__name__ == 'blogposts':
            tweets = tweets[:3]
        blog_cats = BlogTag.objects.filter(main_cat=True)
        writers = Profile.objects.filter(
            role__gte=1, posts__id__gte=1, posts__displayed=True).order_by(
            'name').distinct()

        ctx = {}
        ctx['news'] = news
        ctx['pop_posts'] = pop_posts
        ctx['tweets'] = tweets
        ctx['blog_cats'] = blog_cats
        ctx['writers'] = writers
        if request.user.is_authenticated:
            ctx['logged_in'] = True
        else:
            ctx['logged_in'] = False

        return fn(ctx, *args, **kwargs)
    return decorated_fn


def visit_log(request):
    params = {
        'referrer': request.META.get('HTTP_REFERER'),
        'user_agent': request.META.get('HTTP_USER_AGENT'),
    }
    visit = SiteVisit(
        ip_address1=request.META.get('HTTP_X_FORWARDED_FOR').split(',')[0]
    )


@context_decorator
def index(ctx, request):
    posts = BlogPost.objects.filter(
        displayed=True, publish_on__lte=timezone.now()).order_by('-publish_on')[:10]
    events = Event.objects.all().order_by('real_date')[:3]
    ctx['posts'] = posts
    ctx['events'] = events
    # testwork.apply_async(['work'])
    return render(
        request, 'blog/index.html', ctx
    )


@context_decorator
def blogposts(ctx, request, link):
    try:
        post = BlogPost.objects.filter(
            displayed=True, publish_on__lte=timezone.now()).get(link=link)
    except BlogPost.DoesNotExist:
        raise Http404('Article does not exist')
    post.visit_count += 1
    post.popularity += 1
    post.save()
    ctx['post'] = post
    sugs = BlogPost.objects.filter(displayed=True, publish_on__lte=timezone.now())[:3]
    comments = post.comments.all().order_by('-created_on')
    ctx['sugs'] = sugs
    ctx['comments'] = comments
    return render(request, 'blog/blogpost.html', ctx)


def blogcomments(request, pk):
    # login required?
    try:
        blog = BlogPost.objects.get(pk=pk)
    except BlogPost.DoesNotExist:
        raise Http404('Comment\'s article does not exist')
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'logged_out': True})
        data = json.loads(request.body.decode('utf-8'))
        if not data['value']:
            return JsonResponse({'empty': True})
        content = data['value']
        try:
            user = Profile.objects.get(user__id=int(data['user_id']))
        except Profile.DoesNotExist:
            return redirect('login_view')
        BlogComment.objects.create(
            post=blog, author=user,
            content=content, created_on=timezone.now()
        )
        blog.popularity += 1
        blog.save()
        return JsonResponse({'success': True})
    # comments = BlogComment.objects.filter(post__id=pk).values().order_by('-created_on')
    comments = BlogComment.objects.filter(post__id=pk).order_by('-created_on')
    html = render_to_string('blog/snippet_comments.html', {'comments': comments})
    res = {}
    res['html'] = html
    return JsonResponse(res)


@context_decorator
def signup_view(ctx, request):
    logout(request)
    if request.method == 'GET':
        return render(request, 'blog/register.html', ctx)
    email = request.POST.get('email', False)
    if not email or not request.POST.get('first_name', False):
        return HttpResponse('Sufficient credentials not given')
    if User.objects.filter(email=email):
        ctx['email_exists'] = True
        return render(request, 'blog/register.html', ctx)
    last_name = ''
    if request.POST.get('last_name', False):
        last_name = request.POST['last_name']
    user = User.objects.create_user(
        username=email, email=email, password=request.POST['password'],
        first_name=request.POST['first_name'], last_name=last_name
    )
    # profile is getting created via signals
    fl = request.FILES.get('avatar', False)
    if fl:
        profile = Profile.objects.get(user=user)
        profile.avatar.save(
            request.POST['email'] + '.jpeg',
            request.FILES['avatar']
        )
    '''
    profile = Profile.objects.create(
        user=user, name=request.POST['first_name']+' '+request.POST['last_name'],
        role=0
    )
    
    '''
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return redirect('/')


@context_decorator
def login_view(ctx, request):
    if request.method == 'GET':
        return render(request, 'blog/login.html', ctx)
    if not request.POST.get('email', False):
        ctx['errmsg'] = 'Email not entered'
        return render(request, 'blog/login.html', ctx)
    user = authenticate(
        username=request.POST['email'],
        password=request.POST['password']
    )
    if user is None:
        ctx['errmsg'] = 'Invalid email or password'
        return render(request, 'blog/login.html', ctx)
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return redirect('/')


def logout_view(request):
    logout(request)
    return redirect('/login/')


@context_decorator
def account(ctx, request):
    if not request.user.is_authenticated:
        return redirect('/')
    if request.method == 'GET':
        return render(request, 'blog/account.html', ctx)
    # user = authenticate(username=request.user.username, password=request.POST['old_pw'])
    if request.FILES.get('avatar', False):
        prof = Profile.objects.get(user=request.user)
        prof.avatar.save(prof.user.username+'.jpeg', request.FILES['avatar'])
    if request.POST.get('new_pw', False):
        if not request.POST.get('old_pw', False):
            return HttpResponse('<h2>Enter current password</h2>')
        user = authenticate(username=request.user.username, password=request.POST['old_pw'])
        if user is None:
            return HttpResponse('<h2>Invalid password</h2>')
        user.set_password(request.POST['new_pw'])
        user.save()
        logout(request)
        login(request, user)
    return redirect('/')


@context_decorator
def blog(ctx, request):
    posts = BlogPost.objects.filter(
        displayed=True,
        publish_on__lte=timezone.now()).order_by('-publish_on')
    ctx['posts'] = posts
    return render(request, 'blog/blog.html', ctx)


@context_decorator
def tweets(ctx, request):
    tweets = Tweet.objects.all().order_by('-publish_on')[:100]
    ctx['all_tweets'] = tweets
    return render(request, 'blog/tweets.html', ctx)


@context_decorator
def news(ctx, request):
    news = News.objects.order_by('-posted_on').all()[:120]
    ctx['all_news'] = news
    return render(request, 'blog/news.html', ctx)


@context_decorator
def tools(ctx, request):
    events = Event.objects.all().order_by('real_date')
    ctx['events'] = events
    return render(request, 'blog/tools.html', ctx)


@context_decorator
def columnists(ctx, request, name):
    ctx['writer_'] = Profile.objects.filter(role__gte=1, link=name, posts__id__gte=1)
    if not ctx['writer_']:
        raise Http404('Columnist has no posts')
    ctx['writer_'] = ctx['writer_'][0]
    ctx['last_date'] = ctx['writer_'].posts.latest('publish_on').publish_on
    posts = BlogPost.objects.filter(
        authors__link=name, displayed=True,
        publish_on__lte=timezone.now()).order_by('-publish_on')
    ctx['posts'] = posts
    return render(request, 'blog/columnists.html', ctx)


@context_decorator
def categories(ctx, request, name):
    ctx['topic'] = name
    tag = BlogTag.objects.filter(link=name)
    if not tag:
        raise Http404("No articles found for the given tag")
    tag = tag[0]
    posts = tag.post.filter(displayed=True, publish_on__lte=timezone.now())
    #bposts = BlogPost.objects.filter(tags__name=name)
    ctx['posts'] = posts
    return render(request, 'blog/categories.html', ctx)


@context_decorator
def search(ctx, request):
    res1 = BlogPost.objects.filter(
        tags__name__iregex=r"\y{0}\y".format(request.GET['searchquery'])).filter(
        displayed=True, publish_on__lte=timezone.now())
    res0 = BlogPost.objects.filter(
        authors__name__iregex=r"\y{0}\y".format(request.GET['searchquery']),
        displayed=True
    )
    results = BlogPost.objects.filter(
        title__iregex=r"\y{0}\y".format(request.GET['searchquery'])).filter(
        displayed=True, publish_on__lte=timezone.now())
    res2 = BlogPost.objects.filter(
        content__iregex=r"\y{0}\y".format(request.GET['searchquery'])).filter(
        displayed=True, publish_on__lte=timezone.now())
    resp = list(chain(res1, res0, results, res2))
    ctx['posts'] = resp
    ctx['querykey'] = request.GET['searchquery']
    return render(request, 'blog/search.html', ctx)


@context_decorator
def about(ctx, request):
    ctx['site'] = Site.objects.get(pk=1)
    try:
        ctx['dev'] = Profile.objects.get(user__username='param')

    except Exception as e:
        # return HttpResponse(str(e))
        raise Http404('We\'ve run into some internal error')
    return render(request, 'blog/about.html', ctx)


@context_decorator
def hidden_post(ctx, request, link):
    post = get_object_or_404(BlogPost, link=link)
    if post.displayed:
        return HttpResponse(
            'This post is publicly displayed. Uncheck "displayed" in admin to hide it.')
    ctx['post'] = post
    sugs = BlogPost.objects.filter(displayed=True, publish_on__lte=timezone.now())[:3]
    comments = post.comments.all().order_by('-created_on')
    ctx['sugs'] = sugs
    ctx['comments'] = comments
    return render(request, 'blog/blogpost.html', ctx)


def login2(request):
    return render(request, 'blog/login2.html')


def privacypolicy(request):
    return render(request, 'blog/privacypolicy.html')


def tos(request):
    return render(request, 'blog/tos.html')


def test_mail(request):
    send_mail(
        'Message from Django', 'This is the message', 'usefulpython@gmail.com',
        ['freefries.p@gmail.com'])
    return HttpResponse('Done')

'''
def contribute(request):
    if not request.user.is_authenticated:
        return redirect('/login/')
    if request.method == 'GET':
        writer = Profile.objects.get(user=request.user)
        if writer.role == 0:
            return Http404('Access Denied')
        count = range(3)
        tags = ['' for i in count]
        return render(request, 'blog/contribute1.html',
                      {'writer': writer, 'count': count, 'tags': tags})
    print(request.POST)
    blog = BlogPost(
        content = request.POST['content'],
        title= request.POST['title'],
    )
    if request.POST.get('displayed', False):
        blog.displayed = True
    else:
        blog.displayed = False
    if request.POST.get('snippet', False):
        blog.snippet = request.POST['snippet']
    else:
        blog.snippet = get_snippet(request.POST['content'])
    if request.POST.get('publish_on', False):
        blog.publish_on = request.POST['publish_on']
    else:
        blog.publish_on = timezone.now()
    if request.FILES.get('cover', False):
        blog.cover.save(blog.link+'.png', request.FILES['cover'])
    blog.save()
    return redirect('/')


def contribute_link(request, link):
    if not request.user.is_authenticated:
        return redirect('/login/')
    if request.method == 'GET':
        writer = Profile.objects.get(user=request.user)
        if (writer.role == 0) or (not writer.posts.filter(link=link)):
            return Http404('Access Denied')
        post = writer.posts.get(link=link)
        tags = post.tags.all().values('name')
        tags = [t['name'] for t in tags]
        count = range(3)
        return render(request, 'blog/contribute1.html',
                      {'writer': writer, 'post': post, 'tags': tags, 'count': count})
    blog = BlogPost.objects.get(link=link)
    blog.content = request.POST['content']
    blog.title = request.POST['title']
    blog.snippet = request.get('snippet', '')
    blog.publish_on = request.POST['publish_on']
    if request.POST.get('displayed', False):
        blog.displayed = True
    else:
        blog.displayed = False
    return redirect('/')


def context(request, searchview=False):
    if (not searchview) and request.GET.get('searchquery'):
        return redirect('/search?searchquery=%s' % request.GET['searchquery']), True
    news = News.objects.order_by('-posted_on').all()[:5]
    pop_posts = BlogPost.objects.order_by(
        '-popularity').filter(displayed=True, publish_on__lte=timezone.now())[:5]
    tweets = Tweet.objects.all().order_by('-posted_on')[:5]
    blog_cats = BlogTag.objects.filter(main_cat=True)
    writers = Profile.objects.filter(role__gte=1, posts__id__gte=1).order_by(
        'name').distinct()

    ctx = {}
    ctx['news'] = news
    ctx['pop_posts'] = pop_posts
    ctx['tweets'] = tweets
    ctx['blog_cats'] = blog_cats
    ctx['writers'] = writers
    if request.user.is_authenticated:
        ctx['logged_in'] = True
    else:
        ctx['logged_in'] = False
    return ctx, False
'''


@csrf_exempt
def api_ssls(request):
    data = json.loads(request.body.decode('utf-8'))
    if data['token'] != settings.INTERNAL_API_TOKEN:
        return JsonResponse({'correct_token': False,
                             'success': False})
    proxies = SslProxy.objects.exclude(not_working=True).order_by(
        '-discovered_on', 'working', '-not_working'
    )[:50]
    res = {}
    res['ssls'] = []
    for p in proxies:
        res['ssls'].append(p.ip_address)
    return JsonResponse(res)


@csrf_exempt
def api_mobile_data_mobile_end(request):
    data = json.loads(request.body.decode('utf-8'))
    if data['token'] != settings.PERSONAL_TOKEN:
        return JsonResponse({'correct_token': False,
                             'success': False})
    MobileDataStat.objects.create(
        data_used=data['data_used'],
        data_cap=data['data_cap']
    )
    return JsonResponse({'success': True})


@csrf_exempt
def api_mobile_data_server_end(request):
    data = json.loads(request.body.decode('utf-8'))
    if data['token'] != settings.PERSONAL_TOKEN:
        return JsonResponse({'correct_token': False,
                             'success': False})
    resp = {}
    resp['stats'] = []
    for entry in MobileDataStat.objects.all()[:10]:
        resp['stats'].append(
            {
                'data_used': entry.data_used,
                'time': entry.time,
                'data_cap': entry.data_cap
            }
        )
    return JsonResponse(resp)
