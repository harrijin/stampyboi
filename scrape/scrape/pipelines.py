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

# DEST_PATH = 'http://localhost:8983/solr/stampyboi/update/json/docs'

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

    def close_spider(self, spider):
        spider.executor.shutdown()
        print('SUCCESSFUL EXTRACTIONS: ' + str(successes))

    def process_item(self, item, spider):
        id = item['realid']
        spider.executor.submit(extract, id)
        return item