from bs4 import BeautifulSoup
from utils import get_pdf_text
from transcriber import Transcriber
import requests
import re

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

TIMESTAMP_LEN = 12


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

    def __init__(self, title, season, episode):

        super().__init__()

        # Get list of shows and transcripts from 8flix
        r = requests.get(SHOW_TRANSCRIPTS_URL)
        soup = BeautifulSoup(r.content)

        # Find show from title
        shows = soup.select(SHOWS_CSS_SELECTOR)
        show = self.__find_show(title, shows)
        show_details = show.parent.find_next_sibling('ul')

        # Find season
        szns = show_details.select(SEASONS_CSS_SELECTOR)
        szn = szns[season - 1]
        episodes = szn.select(EPISODES_CSS_SELECTOR)

        # Find episode
        epis = episodes[episode - 1]

        # Get episode link and fetch pdf
        episode_link = epis['href']
        e = requests.get(episode_link)
        pdf_soup = BeautifulSoup(e.content)
        buttons = pdf_soup.select(BUTTONS_CSS_SELECTOR)
        pdf_url = BASE_URL + buttons[PDF_BUTTON_INDEX]['href']

        # Extract text from PDF
        transcript = get_pdf_text(pdf_url)

        stage_dir_re = re.compile(STAGE_DIRECTIONS_REGEX)
        transcript = stage_dir_re.sub(' ', transcript)

        end_stamp_re = re.compile(END_TIMESTAMP_REGEX)
        transcript = end_stamp_re.sub('', transcript)

        transcript_list = re.split(BLOCK_NUMBER_REGEX, transcript)

        # Remove intro text from generated timestamp-text pairs
        transcript_list.pop(0)



        self.transcript_list = transcript_list

        # Remove 
    
    def get_transcript(self):
        return self.transcript_list

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
