# Returns YouTube transcripts (including auto-generated) as a list of dictionaries, where each dictionary has 3 values
# 'text': 'string'
# 'start': time in seconds
# 'duration': time in seconds
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from transcriber import Transcriber

class YouTube(Transcriber)
    def __init__(self, source):
        super().__init__(self, source)
        
    def getVideoId():
        # Examples:
        # - http://youtu.be/SA2iWivDJiE
        # - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
        # - http://www.youtube.com/embed/SA2iWivDJiE
        # - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
        query = urlparse(self.source)
        if query.hostname == 'youtu.be': return query.path[1:]
        if query.hostname in ('www.youtube.com', 'youtube.com'):
            if query.path == '/watch': return parse_qs(query.query)['v'][0]
            if query.path[:7] == '/embed/': return query.path.split('/')[2]
            if query.path[:3] == '/v/': return query.path.split('/')[2]
        # fail?
        return None

    def getTranscript():
        phrases = OrderedDict()
        listTranscript = YouTubeTranscriptApi.get_transcript(getVideoId())
        for dic in listTranscript:
            phrases[dic['start']] = dic['text']
        return super.separatePhrases(phrases)        
