from transcribers.flix import FlixExtractor
from pathlib import Path
import os, pysolr

SOLR_HOST_DIR = '/Documents'
WORKING_DIRECTORY = os.getcwd()
HOME = str(Path.home())
os.chdir(HOME + SOLR_HOST_DIR)
file = open("solrhost.txt", "r")
SOLR_HOST = str(file.read())
os.chdir(WORKING_DIRECTORY)

solr = pysolr.Solr('http://'+SOLR_HOST+'/solr/stampyboi')

def extract(videoID):
    print(f'START   {videoID}')
    transcriber = FlixExtractor(videoID)
    transcriptJSON = transcriber.convertToJSON()
    print(f'EXTRACT {videoID}')
    solr.add(transcriptJSON, commit=True)
    print(f'DONE    {videoID}')

with open('flix.txt') as f:
    for line in f:
        id = line.rstrip()
        extract(id)
