import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

class YoutubeSpider(CrawlSpider):
    name = "youtube"

    def start_requests(self):
        id = getattr(self, 'id', 'MvkN3003iU4')
        url = 'https://www.youtube.com/s/player/0c5285fd/player_ias.vflset/en_US/base.js'
        return scrapy.Request(url=url, callback=self.parse, headers={'Referer': 'https://www.youtube.com/watch?v=' + id})

    def parse(self, response):  
        pass