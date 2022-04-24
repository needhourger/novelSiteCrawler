import scrapy


class XbiqugeSoSpider(scrapy.Spider):
    name = 'xbiquge_so'
    allowed_domains = ['xbiquge.so']
    start_urls = ['http://xbiquge.so/']

    def parse(self, response):
        pass
