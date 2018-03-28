# usefulpython
### Codebase driving [UsefulPython.com](https://usefulpython.com) - a  Django powered Python blog, news and tools website.

The website is mostly written from scratch, using a base Bootstrap theme for front-end.

## Features
This site provides a basic blogging app with features such as dynamic categories (using post tags), scheduled posts and hidden posts, a WYSIWYG editor for content creators with support for embedding media in articles, a single-threaded comment system, and popular posts section using the article view and comments as the criteria. The app also periodically runs web scraping and other tasks using celery-beat to display upcoming tech events and tech news, and uses Twitter API to display the relevant top tweets. The tasks can easily be configured from the admin site by changing the topics to search for to obtain the news and tweets

## Tools used in this project:
- [celery](http://celery.readthedocs.io/en/latest/) and celery-beat (using RabbitMQ as the messaging queue) for scheduling periodic tasks (making API calls, listening RSS feeds, curating the database etc)
- [python-twitter](https://python-twitter.readthedocs.io/en/latest/) for making Twitter API calls for fetching the needed Python and programming discussions
- requests and BeautifulSoup modules for fetching RSS feeds and parsing the HTML/XML pages
- tinymce for text editing in admin site for the content creators
- django-celery-beat for easily rescheduling the scheduled periodic tasks from admin site
- [django-allauth](http://django-allauth.readthedocs.io/en/latest/index.html) for social OAuth based user signup
-  easy-thumbnails for adjusting image resolution in templates
- other apps such as humanize to format dates and times
- Markdown and Pygments for rendering the blog in HTML from original markdown files



