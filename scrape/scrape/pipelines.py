# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from transcribers.youtube import YouTube

class TranscriberPipeline:

    def process_item(self, item, spider):
        transcriber = YouTube(item["realid"])
        return {'transcript' : transcriber.getTranscript()}
        # return item

        # TODO Fix the pipe to upload info to the database
