from bs4 import BeautifulSoup
from utils import get_pdf_text
import requests
import re

BASE_URL = 'https://8flix.com'
SHOW_TRANSCRIPTS_URL = 'https://8flix.com/transcripts/shows/'

SHOWS_CSS_SELECTOR = '#menu-transcripts > li > div > a'
SEASONS_CSS_SELECTOR = 'li.menu-item.fl-has-submenu > ul'
EPISODES_CSS_SELECTOR = 'a'

BUTTONS_CSS_SELECTOR = 'div.fl-button-wrap > a'
PDF_BUTTON_INDEX = 0


"""
FlixExtractor is the caption extractor for video sources where 
captions are available on 8flix.
"""


class FlixExtractor():

    

    """
    title - String of title of Netflix show
    """

    def __init__(self, title, season, episode):

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
        self.raw_transcript = get_pdf_text(pdf_url)
    
    def get_raw_transcript(self):
        return self.raw_transcript

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

