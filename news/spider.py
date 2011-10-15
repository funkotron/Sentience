from sentience.news.models import Entity,Article,Stock
import re
import urllib
import BeautifulSoup
from datetime import datetime
from datetime import timedelta

class Spider():

    def __init__(self,
                 entity=None,
                 start=(datetime.now()-timedelta(days=20)).date(),
                 end=datetime.now().date(),
                 chunk_size=50,
                 total_articles=1000):
        self.entity = entity
        self.start = start
        self.end = end
        self.chunk_size = chunk_size #How many results to return in one request
        self.total_articles = total_articles

    def get_visible(self,url):
        #Return the visible text on a page
        #Adapted from http://stackoverflow.com/questions/1936466/beautifulsoup-grab-visible-webpage-text
        html = urllib.urlopen(url).read()
        soup = BeautifulSoup.BeautifulSoup(html)
        texts = soup.findAll(text=True)

        def visible(element):
            if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
                return False
            elif re.match('.*<!--.*-->.*', str(element), re.DOTALL):
                return False
            return True

        visible_texts = filter(visible, texts)
        return visible_texts

    def find_articles(self):
        #Return any article urls related to an entity between two given dates

        start_count = 0
        while True:
            url = "http://www.google.co.uk/finance/company_news?q=%s:%s&startdate=%s&enddate=%s&start=%d&num=%d"%(
                  self.entity.exchange,
                  self.entity.ticker,
                  self.start.strftime("%Y-%m-%d"),
                  self.end.strftime("%Y-%m-%d"),
                  start_count,
                  self.chunk_size)
            html = urllib.urlopen(url).read()
            soup = BeautifulSoup.BeautifulSoup(html)
            article_list = soup.findAll("div", {"class":"g-section news sfe-break-bottom-16"})
            if not article_list:
                break
            for i in article_list:
                link = i.find("span",{"class":"name"}).a
                name = link.text
                print link.attrs[0][1]
                url = link.attrs[0][1]
                date_text = i.find("span",{"class":"date"}).text
                try:
                    date = datetime.strptime(date_text,"%b %d, %Y").date()
                except:
                    date = datetime.today().date()
                src = i.find("span",{"class":"src"}).text
                body = self.get_visible(url)
                article = Article(name=name,
                                  entity=self.entity,
                                  src=src,
                                  date = date,
                                  body = body)
                article.save()
            start_count += self.chunk_size


        return True

    def grab_prices(self):
        #Get stock prices
        url = ("http://www.google.co.uk/finance/historical?q=%s:%s&startdate=%s&enddate=%s&output=csv" % (
              self.entity.exchange,
              self.entity.ticker,
              self.start.strftime("%Y-%m-%d"),
              self.end.strftime("%Y-%m-%d")
        ))
        html = urllib.urlopen(url).read().split('\n')
        for row in html[1:]:
            fields = row.split(',')
            if not fields[0]:
                continue
            date = datetime.strptime(fields[0],"%d-%b-%y")
            price = int(fields[4].replace('.',''))
            stock = Stock(date=date,
                               price=price,
                               entity=self.entity)
            stock.save()


        return True

    def run(self):
        self.find_articles()
        self.grab_prices()
        return True

g = Entity(name="Google",ticker="GOOG",exchange="NASDAQ")
g.save()
spider = Spider(entity=g)
spider.grab_prices()
