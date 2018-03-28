from xml.etree import ElementTree as ET
from datetime import datetime, timedelta
import pytz
import requests
from bs4 import BeautifulSoup
import twitter
from django.utils.text import slugify
from django.conf import settings
from .models import Log
from django.utils import timezone

def generate_link(name):
    return slugify(name)


def text_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.text


def _get_url(topic):
    topic = topic.replace(' ', '%20')
    url = 'https://news.google.com/news/rss/headlines/section/q/%s/' % \
          topic
    return url


def get_news_links(topic, proxy):
    try:
        res = requests.get(
            _get_url(topic),
            proxies={'https': proxy}
        )
    except Exception as e:
        Log.objects.create(
            message='Could not download Google\'s rss with proxy: %s' % proxy,
            content=str(e)
        )
        return
    if res.status_code not in range(200, 300):
        Log.objects.create(
            message='While downloading rss from Google news: status code: %s' % str(res.status_code)
        )
        return
    root = ET.fromstring(res.text).find('channel')
    items = root.findall('item')
    tc = 0
    for child in items[1:]:
        title = child.find('title').text
        if '(promoted)' in title.lower():
            continue
        link = child.find('link').text
        yield (title, link)


def get_events():
    url = 'https://www.techmeme.com/events'
    res = requests.get(url)
    if not str(res.status_code).startswith('2'):
        return []
    soup = BeautifulSoup(res.text, 'html.parser')
    res1 = soup.select('div#events > div[class^=ne]')
    res2 = soup.select('div#events > div[class^=featured]')
    results = res1 + res2
    for sample in results:
        sam = sample.find('div')
        link = sam.find('a')['href']
        date = sam.find('div').text
        subject = sam.find_all('div')[1].text
        location = sam.find_all('div')[2].text
        yield (link, date, subject, location)


def get_link_info(url, proxy=None):
    targ_base = 'http://www.getlinkinfo.com/info'
    params = {'link': 'https://www.techmeme.com' + url}
    if proxy:
        proxies = {'https': proxy}
    else:
        proxies = None
    proxies = {'https': '190.11.32.94:53281'}
    res = requests.get(
        targ_base, params=params,
        proxies=proxies
    )
    soup = BeautifulSoup(res.text, 'html.parser')
    # Log.objects.create(message='soup', content=str(soup))
    ele = soup.find('div', class_='link-info')
    eff_url = ele.find('dl')
    eff_url = eff_url.find_all('dd')[3]
    eff_url = eff_url.find('a')['href']
    desc = ele.find('dl').find_all('dd')[1].text
    if '(none)' in desc:
        desc = ''
    title = ele.find('dl').find_all('dd')[0].text
    return eff_url, desc, title


def get_parsed_date(txt):
    start = txt.split('-')[0]
    start = start + ' ' + str(datetime.today().year)
    try:
        dt_obj = datetime.strptime(start, '%b %d %Y')
        dt_obj = dt_obj.replace(tzinfo=pytz.UTC)
    except Exception:
        return
    else:
        return dt_obj


def get_tweets_by_topic(topic):
    api = twitter.Api(
        consumer_key=settings.TWITTER_CONSUMER_KEY,
        consumer_secret=settings.TWITTER_CONSUMER_SECRET,
        access_token_key=settings.TWITTER_ACCESS_TOKEN_KEY,
        access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET
    )
    if topic.basis == 0:
        restype = 'popular'
    elif topic.basis == 1:
        restype = 'recent'
    else:
        restype = 'mixed'
    results = api.GetSearch(
        term=topic.term, lang='en', result_type=restype,
        since=(timezone.now().date()-timedelta(days=1)).strftime('%Y-%m-%d'),
        count=50
    )
    for result in results:
        text = result.user.name
        text = ''.join([i if ord(i) < 128 else ' ' for i in text]).strip()
        dtstr = result.created_at
        dtstr = ' '.join([i for i in dtstr.split(' ') if not i.startswith('+')])
        dt = datetime.strptime(dtstr, '%c')
        dt = dt.replace(tzinfo=pytz.UTC)
        dp = result.user.profile_image_url
        d = {
            'author': text,
            'author_handle': result.user.screen_name,
            'content': result.text.replace(r'&amp;', r'&'),
            'posted_on': dt
        }
        if not result.urls:
            continue
        d['link'] = result.urls[0].expanded_url
        if dp:
            d['author_pic'] = dp
        yield d


def get_tweets_by_user(user):
    api = twitter.Api(
        consumer_key=settings.TWITTER_CONSUMER_KEY,
        consumer_secret=settings.TWITTER_CONSUMER_SECRET,
        access_token_key=settings.TWITTER_ACCESS_TOKEN_KEY,
        access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET
    )
    results = api.GetUserTimeline(screen_name=user.term, count=5)

    for result in results:
        text = result.user.name
        text = ''.join([i if ord(i) < 128 else ' ' for i in text]).strip()
        dtstr = result.created_at
        dtstr = ' '.join([i for i in dtstr.split(' ') if not i.startswith('+')])
        dt = datetime.strptime(dtstr, '%c')
        dt = dt.replace(tzinfo=pytz.UTC)
        dp = result.user.profile_image_url
        d = {
            'author': text,
            'author_handle': result.user.screen_name,
            'content': result.text.replace(r'&amp;', r'&'),
            'posted_on': dt
        }
        if not result.urls:
            continue
        d['link'] = result.urls[0].expanded_url
        if dp:
            d['author_pic'] = dp
        yield d