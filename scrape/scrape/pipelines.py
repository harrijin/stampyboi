# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from transcribers.youtube import YouTube
from datetime import datetime
import json, subprocess
import concurrent.futures
import pysolr
import os
from pathlib import Path
# from transcribers.file import FileExtractor
# import youtube_dl

SOLR_COLLECTION = 'stampyboi'
SOLR_HOST_DIR = '/Documents'
WORKING_DIRECTORY = os.getcwd()
HOME = str(Path.home())
os.chdir(HOME + SOLR_HOST_DIR)
file = open("solrhost.txt", "r")
SOLR_HOST = str(file.read())
os.chdir(WORKING_DIRECTORY)
solr = pysolr.Solr('http://'+SOLR_HOST+'/solr/'+SOLR_COLLECTION)

successes = 0

def extract(id):
    transcriber = YouTube(id)
    transcriptJSON = transcriber.getJSON()

    if not isinstance(transcriptJSON, str): # No error message
        transcriptJSON = transcriber.getJSON()
        solr.add(transcriptJSON, commit=True)
        # command = ["curl", "-X", "POST", "-H", "Content-Type: application/json", DEST_PATH, "--data-binary", json.dumps(transcriptJSON)]
        # subprocess.run(command)
        # print(" ".join(command))
        global successes
        successes += 1
    else:
        print("No captions: " + id)

class TranscriberPipeline:

    def open_spider(self, spider):
        spider.executor = concurrent.futures.ThreadPoolExecutor()
        # self.model = deepspeech.Model('./transcribers/deepspeech-0.7.4-models.pbmm')
        # self.model.enableExternalScorer('./transcribers/deepspeech-0.7.4-models.scorer')

    def close_spider(self, spider):
        spider.executor.shutdown()
        print('SUCCESSFUL EXTRACTIONS: ' + str(successes))

    def process_item(self, item, spider):
        id = item['realid']
        spider.executor.submit(extract, id)
        return item

# STT processing of YT videos - unnecessary due to autocaptions applying on all convertible audio
# if isinstance(transcript, str) # Returned error message instead of transcript list
#     opts = {
#         'outtmpl' : '%(id)s.%(ext)s',
#         'postprocessors' : [{
#             'key': 'FFmpegExtractAudio',
#             'preferredcodec': 'wav',
#         }],
#         'cookiefile' : 'cookies.txt',
#     }
#     with youtube_dl.YoutubeDL(opts) as ydl:
#         ydl.download(['https://www.youtube.com/watch?v=' + id])

#     try:
#         with open(id + '.wav') as input:
#             transcriber = FileExtractor(id + '.wav', self.model)
#             transcript = transcriber.getTranscript()
#     except FileNotFoundError:
#         raise DropItem("No captions: " + id)