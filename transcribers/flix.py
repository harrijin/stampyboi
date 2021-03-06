from bs4 import BeautifulSoup
from .utils import get_pdf_text, extract_words
from .transcriber import Transcriber
import os
import subprocess
import requests
import re
import json
import srt
import math

BASE_URL = 'https://8flix.com'
SHOW_TRANSCRIPTS_URL = 'https://8flix.com/transcripts/shows/'

SHOWS_CSS_SELECTOR = '#menu-transcripts > li > div > a'
SEASONS_CSS_SELECTOR = 'li.menu-item.fl-has-submenu > ul'
EPISODES_CSS_SELECTOR = 'a'

BUTTONS_CSS_SELECTOR = 'div.fl-button-wrap > a'
PDF_BUTTON_INDEX = 0

END_TIMESTAMP_REGEX = ' --> [\d:,]+\s'
STAGE_DIRECTIONS_REGEX = '\[(.*?)\]'
BLOCK_NUMBER_REGEX = '\s+\d+\s+(?=\d{2}:\d{2}:\d{2},\d{3})'
TIMESTAMP_COMPONENTS_REGEX = '[:,]'

TIMESTAMP_LEN = 12

SPACE_REPLACEMENT_CHAR = '-'

NETFLIX_ID_DIRECTORY = os.path.join(os.getcwd(),'flixIDConverter', 'netflixIDDictionary.json')


"""
FlixExtractor is the caption extractor for video sources where
captions are available on 8flix.
"""


class FlixExtractor(Transcriber):

    """
    title - String of title of Netflix show
    season - integer indicating the season number
    episode - integer indicating the episode number
    """

    def __init__(self, netflixID):

        super().__init__()
        self.id = netflixID


    def getTranscript(self):
        with open(NETFLIX_ID_DIRECTORY, "r") as file:
            dictionary = json.load(file)
        entry = dictionary[self.id]
        show = entry[0]
        szn = entry[1]
        epis = entry[2]
        query = (show + " " + "{0:0=2d}".format(szn) + "x" + "{0:0=2d}".format(epis)).replace(" ", "-")
        command = ["addic7ed", "-l", "english", "-bb", query]
        subDownload = subprocess.run(command, stdout=subprocess.PIPE, universal_newlines=True)
        if "Completed" in subDownload.stdout:
            tupleList = []
            srtDirectory = os.path.join(os.getcwd(), query + '.srt')
            filestr = open(srtDirectory, 'r').read()
            subtitles = srt.parse(filestr)
            for subtitle in subtitles:
                time = int(subtitle.start.total_seconds())
                phrase = subtitle.content
                words = extract_words(phrase)
                if len(words) != 0:
                    tupleList.append((SPACE_REPLACEMENT_CHAR.join(words), time))
            subprocess.run(["rm", srtDirectory])
        else:
            print(subDownload.stdout)
            raise ValueError("ERROR: Show not found")
        # Old 8flix stuff======================================
        # # Extract text from PDF
        # transcript = get_pdf_text(self.pdf_url)

        # # Strip stage directions
        # stage_dir_re = re.compile(STAGE_DIRECTIONS_REGEX)
        # transcript = stage_dir_re.sub(' ', transcript)

        # # Strip end timestamps
        # end_stamp_re = re.compile(END_TIMESTAMP_REGEX)
        # transcript = end_stamp_re.sub('', transcript)

        # transcript_list = re.split(BLOCK_NUMBER_REGEX, transcript)

        # # Remove intro text from generated timestamp-text pairs
        # transcript_list.pop(0)

        # transcript = list()

        # for component in transcript_list:

        #     timestamp = component[:TIMESTAMP_LEN]
        #     time = self.__convert_to_seconds(timestamp)

        #     phrase = component[TIMESTAMP_LEN:]
        #     words = extract_words(phrase)
        #     if len(words) != 0:
        #         transcript.append((SPACE_REPLACEMENT_CHAR.join(words), time))

        return tupleList


    def convertToJSON(self):
        transcript=self.getTranscript()
        text=""
        times=[]
        for timestamp in transcript:
            text+=(timestamp[0]+" ")
            times.append(timestamp[1])
        jsonObject={
            "id":self.id,
            "type":"flix",
            "script":text,
            "times":times,
            # "title":self.show
        }
        return jsonObject

    @staticmethod
    def __convert_to_seconds(timestamp):
        components = re.split(TIMESTAMP_COMPONENTS_REGEX, timestamp)
        hour_seconds = int(components[0]) * 60 * 60
        minute_seconds = int(components[1]) * 60
        seconds = int(components[2])

        return hour_seconds + minute_seconds + seconds



    """
    Finds the element containing show data

    title - String of title of Netflix show
    shows - BeautifulSoup ResultSet of shows from 8flix

    returns BeautifulSoup Element containing show data
    """
    @staticmethod
    def __find_show(title, shows):

        for show in shows:
            if re.search(title, show.text):
                return show
        # If show not found
        raise ValueError('Show not found')


"""
OLD 8FLIX STUFF

        self.show=title
        self.szn=season
        self.epis=episode
        # Get list of shows and transcripts from 8flix
        r = requests.get(SHOW_TRANSCRIPTS_URL)
        soup = BeautifulSoup(r.content)

        # Find show from title
        shows = soup.select(SHOWS_CSS_SELECTOR)
        show = self.__find_show(title, shows)
        show_details = show.parent.find_next_sibling('ul')

        # Find season
        szns= show_details.select(SEASONS_CSS_SELECTOR)
        if (season <= 0 or season > len(szns)):
            raise IndexError('Season out of range')
        szn = szns[season - 1]
        episodes = szn.select(EPISODES_CSS_SELECTOR)

        # Find episode
        if (episode <= 0 or episode > len(episodes)):
            raise IndexError('Episode out of range')
        epis = episodes[episode - 1]

        # Get episode link and fetch pdf
        episode_link = epis['href']
        e = requests.get(episode_link)
        pdf_soup = BeautifulSoup(e.content)
        buttons = pdf_soup.select(BUTTONS_CSS_SELECTOR)
        self.pdf_url = BASE_URL + buttons[PDF_BUTTON_INDEX]['href']
"""
