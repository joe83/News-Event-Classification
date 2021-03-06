import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import re
import unicodedata
import datetime
import ipdb
import time
import sys

class bing_scrape():

    def __init__(self, days):
        current_day = datetime.datetime.now()
        self.start_date = current_day.strftime('%Y-%m-%d')
        self.days=days
        self.search_date = '7'
        if self.days == 7:
            self.search_date = '8'
        elif self.days == 30:
            self.search_date = '9'



    def reuters_links(self):
        links - []
        base = 'http://www.reuters.com/search?blob=' + self.search_term +   '&pn='
        for page in range(1,50):
            base += str(page)
            req = requests.get(base)
            soup = BeautifulSoup(req.text, 'html.parser')
            for li in soup.findAll(_class = 'SearchHeadline'):
                for a in li.findAll('a'):
                    links.append(a['href'])
        self.links = list(set(links))

    def bing_links(self):
        page = 1
        links = []
        results = 150
        while page * 10 < results:
            req_text = 'http://www.bing.com/news/search?q=' + self.search_term.replace(' ', '+') + '&qft=interval%3d"'
            # req = 'http://www.bing.com/news/search?q=' + self.search_term.replace(' ', '+') + '&qft=interval%3d'
            req_text += self.search_date + '"&first=' + str(page)
            req = requests.get(req_text)
            page += 10
            soup = BeautifulSoup(req.text)
            results = int(soup.findAll('span', {'class': 'ResultsCount'})[0].text.split()[0].replace(',', ''))
            print results
            for div in soup.findAll('div', {'class' : 'newstitle'}):
                for a in div.findAll('a'):
                    links.append(a['href'])
            
        self.links = list(set(links))

    def get_articles(self):
        descriptions = []
        titles = []
        image_urls = []
        articles = []
        new_links = []
        new_dates = []
        sources = []
        print "num links", len(self.links)

        for i, link in enumerate(self.links):
            try:
                req = requests.get(link)
            except:
                continue
            new_links.append(link)
            soup = BeautifulSoup(req.text, 'html.parser')
            entire_article = soup.findAll('article')
            text = ''
            if not entire_article:
                text = ' '.join([par.text for par in soup.findAll('p')])
            else:
                for art in entire_article:
                    for par in art.findAll('p'):
                        text += par.text + ' '
            text = self.decode_unicode(text)
            articles.append(text)
            try:
                title = soup.findAll('meta', {'name' : 'dc.title'})[0]['content']
            except:
                try:
                    title = soup.findAll('title')[0].text
                except:
                    title = 'None'
            title = self.decode_unicode(title)
            titles.append(title)
            try:
                desc = soup.findAll(attrs =  {'property' : 'og:description'})[0].attrs['content']
                desc = self.decode_unicode(desc)
            except:
                desc = 'None'
            descriptions.append(desc)
            try:
                image_urls.append(soup.findAll(attrs =  {'property' : 'og:image'})[0].attrs['content'])
            except:
                image_urls.append('#')

            if self.days != 1:
                date = self.get_date(req.text) 
                if not date:
                    try:
                        new_dates.append(new_dates[-1])
                    except IndexError:
                        new_dates.append(self.start_date)
                else:
                    new_dates.append(date)
            else:
                new_dates.append(self.start_date)

            sources.append(self.get_source(link))
        # print "art", len(articles)
        # print "links", len(new_links)
        # print "source", len(sources)
        # print "titles", len(titles)
        # print "image_urls", len(image_urls)
        # print "description", len(descriptions)
        # print "dates", len(new_dates)
        frame = pd.DataFrame({'text' : articles, 'url' : new_links, 'source' : sources, \
                'publish_date' : new_dates, 'category' : self.search_term, \
                'title': titles, 'image_url': image_urls, 'description' : descriptions}, \
                columns = ['source', 'url', 'image_url', 'title', 'description', 'text', 'publish_date', 'category'])
        frame = frame.dropna()
        frame.to_csv('data/bing_' + self.search_term.replace(' ', '_') + '_data.csv', index=False, encoding='utf-8')
        
    def get_source(self, url):
        pieces = []
        for seg in url.split('.'):
            for piece in seg.split('/'):
                pieces.append(piece)
        if 'com' in pieces:
            ind = pieces.index('com')
        elif 'net' in pieces:
            ind = pieces.index('net')
        elif len(pieces) >=2:
            ind = 2
        else:
            return 'None'
        return pieces[ind - 1]

    def get_date(self, text):
        date_reg_exp = re.compile('2014[-/][0-1]\d{1}[-/][0-3]\d{1}')
        matches_list = date_reg_exp.findall(text)
        matches_list = [m for m in matches_list if m[-2] <= '31']
        if matches_list:
            return matches_list[0].replace('/', '-')
        return 0

    def decode_unicode(self, text):
        text = unicode(text)
        a = '/'; b = '\''
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore')
        text = str(re.sub('[\n]+', ' ', text))
        text = str(re.sub('[\t]+', ' ', text))
        text = text.replace(a, '')
        text = text.replace(b, '')
        return text

    def run(self, search_term):
        self.search_term = search_term
        self.bing_links()
        self.get_articles()

if __name__ == '__main__':
    search_term = sys.argv[1]
    bing = bing_scrape()
    bing.run(search_term)
