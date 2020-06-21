# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from transcribers.youtube import YouTube
from scrapy.exceptions import DropItem

class TranscriberPipeline:

    def process_item(self, item, spider):
        transcriber = YouTube(item["realid"])
        transcript = transcriber.getTranscript()
        if transcript == "ERROR:YouTube video is unable to be searched, either because the video/captions are unavailable or the video is age-restricted.":
            raise DropItem("No captions: %s" % item["realid"])
        return {
            'id' : item['realid'],
            'transcript' : transcript
        }
        # return item

        # TODO Fix the pipe to upload info to the database
