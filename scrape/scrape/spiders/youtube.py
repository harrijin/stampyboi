import scrapy
import re

class YoutubeSpider(scrapy.Spider):
    name = "youtube"
    start_urls = []

    input = open("ids.txt")
    template = "http://data.yt8m.org/2/j/i/{}/{}.js"

    for line in input:
        url = template.format(line[0:2], line)
        start_urls.append(url)

    def parse(self, response):
        id = response.xpath("/html/body/p/text()").get()
        if id:
            match = re.search("\"([0-9A-z-_]{11})\"\\);", id)
            if match:
                return match.group(1)