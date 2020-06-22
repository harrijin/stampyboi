# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from transcribers.youtube import YouTube
from scrapy.exceptions import DropItem
from datetime import datetime

class TranscriberPipeline:

    def open_spider(self, spider):
        spider.start_time = datetime.now()
        spider.vid_count = 0
        spider.all_count = 0

    def close_spider(self, spider):
        run_time = datetime.now() - spider.start_time
        print("TIME ELAPSED: %s" % run_time)
        print("COUNT: %d" % spider.vid_count)
        print("ALL  : %d" % spider.all_count)

    def process_item(self, item, spider):
        spider.all_count += 1

        transcriber = YouTube(item["realid"])
        transcript = transcriber.getTranscript()
        if transcript == "ERROR:YouTube video is unable to be searched, either because the video/captions are unavailable or the video is age-restricted.":
            raise DropItem("No captions: %s" % item["realid"])
        else:
            spider.vid_count += 1
            print("COUNT: %d" % spider.vid_count)
            print("ALL  : %d" % spider.all_count)
            return {
                'id' : item['realid'],
                'transcript' : transcript
            }
        # return item

        # TODO Fix the pipe to upload info to the database
