from celery import task
from django.utils import timezone
from django.core.mail import send_mail
import datetime
from .models import NewsTopic, News, Log, SslProxy, Event, EventInternal
from .models import TwitterTopic, Tweet
from .utils import get_news_links, get_events, get_link_info, get_parsed_date
from .utils import get_tweets_by_topic, get_tweets_by_user
import requests
from bs4 import BeautifulSoup


@task
def scrape_news(count=0):
    if count > 4:
        return
    Log.objects.create(message='Running scrape_news')
    News.objects.all().update(new=False)
    cycle = 0
    last_cycle = News.objects.order_by('cycle').first()
    if last_cycle:
        cycle = last_cycle.cycle
    topics = NewsTopic.objects.filter(
        active=True,
        start_from__lte=timezone.now()
        # auto_expire_on__gte=timezone.now()
    )                   #  .values_list('topic', flat=True)
    tc = 0
    for cnt in range(1):
        for topic in topics:
            proxy = SslProxy.objects.exclude(not_working=True).order_by(
                'working', '-discovered_on').first()
            if not proxy:
                Log.objects.create(message='No proxies available')
                return
            try:
                results = get_news_links(topic.topic, proxy.ip_address)
            except Exception as e:
                Log.objects.create(message='Error in getting news', content=str(e))
                proxy.not_working = True
                proxy.save()
                count += 1
                scrape_news.apply_async(args=[count], countdown=12)
                return
            else:
                if not results:
                    proxy.not_working = True
                    proxy.save()
                    continue
                proxy.working = True
                proxy.save()
            for content, link in results:
                if News.objects.filter(link=link).exists():
                    continue
                News.objects.create(
                    topic=topic,
                    content=content,
                    link=link,
                    cycle=cycle
                )
                tc += 1
        if tc > 40:
            arts = News.objects.filter(new=False, cycle__lte=(cycle-10))
            for art in arts:
                if art.cycle % 50 != 0:
                    art.delete()
    NewsTopic.objects.filter(auto_expire_on__lte=timezone.now()).delete()
    Log.objects.create(message='Ran scrape_news, scraped %d items' % tc)


@task
def testwork(source=None):
    if not source:
        Log.objects.create(message='Test message from celery.')
        return
    Log.objects.create(
        message='Log message from celery_%s' % source
    )


@task
def obtain_ssls(count = 0):
    if count > 4:
        return
    Log.objects.create(message='Running obtain_ssls')
    proxy = SslProxy.objects.exclude(not_working=True).order_by(
        'working', '-not_working').first()
    if not proxy:
        Log.objects.create(message='No proxies available')
        return
    try:
        res = requests.get(
            'https://www.sslproxies.org/',
            # proxies={'https': proxy.ip_address}
        )
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('tbody')
        for row in table.find_all('tr')[1:]:
            ip = row.find_all('td')[0].text
            port = row.find_all('td')[1].text
            purl = 'https://' + ip + ':' + port
            if not SslProxy.objects.filter(ip_address=purl):
                SslProxy.objects.create(
                    ip_address=purl
                )
    except Exception as e:
        Log.objects.create(
            content=str(e),
            message='Error in scraping proxy from Ssl site'
        )
        proxy.not_working = True
        proxy.save()
        count += 1
        obtain_ssls.apply_async(args=[count], countdown=11)
        return
    else:
        proxy.working = True
        proxy.save()


@task
def process_raw_events():
    raws = EventInternal.objects.filter(processed=False)
    proxy = SslProxy.objects.exclude(not_working=True).order_by(
        'working', '-not_working').first()
    if not proxy:
        proxy = None
    else:
        proxy = proxy.ip_address
    c = 0
    for raw in raws:
        try:
            eff_url, desc, title = get_link_info(raw.raw_link, proxy=proxy)
        except Exception as e:
            Log.objects.create(
                message='Error in scraping link info of Events',
                content=str(e)
            )
            # proxy.not_working = True
            print(e)
            raw.processed = True
            raw.save()
            continue
        else:
            if Event.objects.filter(link=eff_url).exists():
                continue
            proc_event = Event(
                subject=raw.subject,
                link=eff_url,
                location=raw.location,
                event_time=raw.date
            )
            if desc != '' and len(desc) < 248:
                proc_event.content = desc
            real_date = get_parsed_date(raw.date)
            if real_date:
                proc_event.real_date = real_date
            proc_event.save()
            raw.processed = True
            raw.save()
            c += 1
    EventInternal.objects.filter(processed=True).delete()
    Log.objects.create(message='Added %d new events' % c)


@task
def scrape_raw_events():
    Log.objects.create(
        message='Running scrape_raw_events'
    )
    events = get_events()
    te = 0
    for link, date, subject, location in events:
        if EventInternal.objects.filter(raw_link=link).exists():
            continue
        EventInternal.objects.create(
            raw_link=link,
            date=date,
            subject=subject,
            location=location
        )
        te += 1
    Log.objects.create(
        message='Obtained %d raw events' % te
    )
    process_raw_events.apply_async()


@task
def remove_expired_events():
    Log.objects.create(message='Running remove_expired_events')

    Event.objects.filter(
        real_date__lte=timezone.now()-datetime.timedelta(days=2)).delete()


@task
def get_tweets():
    Log.objects.create(message='running get_tweets')
    users = TwitterTopic.objects.filter(active=True)
    c = 0
    for user in users:
        tweets = get_tweets_by_user(user)
        for tweet in tweets:
            if Tweet.objects.filter(link=tweet['link']).exists():
                continue
            Tweet.objects.create(
                **tweet
            )
            c += 1

    Log.objects.create(message='Ran get_tweets, added %d new tweets' % c)


@task
def send_async_mail(subject, message, from_, to, fail_silently=True):
    send_mail(subject, message, from_, to, fail_silently)