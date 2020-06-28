# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from transcribers.youtube import YouTube
from transcribers.file import FileExtractor
from scrapy.exceptions import DropItem
from datetime import datetime
import youtube_dl

class TranscriberPipeline:

    def open_spider(self, spider):
        spider.start_time = datetime.now()
        spider.vid_count = 0
        spider.all_count = 0
        self.model = deepspeech.Model('./transcribers/deepspeech-0.7.4-models.pbmm')
        self.model.enableExternalScorer('./transcribers/deepspeech-0.7.4-models.scorer')

    def close_spider(self, spider):
        run_time = datetime.now() - spider.start_time
        print("TIME ELAPSED: %s" % run_time)
        print("COUNT: %d" % spider.vid_count)
        print("ALL  : %d" % spider.all_count)

    def process_item(self, item, spider):
        spider.all_count += 1

        id = item['realid']
        transcriber = YouTube(id)
        transcript = transcriber.getTranscript()
        if isinstance(transcript, str) # Returned error message instead of transcript list
            opts = {
                'outtmpl' : '%(id)s.%(ext)s',
                'postprocessors' : [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                }],
                'logger': MyLogger(),
                'cookiefile' : 'cookies.txt',
            }
            with youtube_dl.YoutubeDL(opts) as ydl:
                ydl.download(['https://www.youtube.com/watch?v=' + id])

            try:
                with open(id + '.wav') as input:
                    transcriber = FileExtractor(id + '.wav', self.model)
                    transcript = transcriber.getTranscript()
            except FileNotFoundError:
                raise DropItem("No captions: " + id)

        spider.vid_count += 1
        print("COUNT: %d" % spider.vid_count)
        print("ALL  : %d" % spider.all_count)
        return {
            'id' : id,
            'transcript' : transcript
        }
        # return item

        # TODO Fix the pipe to upload info to the database

class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)