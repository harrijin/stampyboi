import scrapy

class YoutubeSpider(scrapy.Spider):
    name = "youtube"
    start_urls = [
        'https://www.youtube.com/'
    ]

    def parse(self, response):
        pass