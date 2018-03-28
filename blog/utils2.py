from bs4 import BeautifulSoup


def text_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.text