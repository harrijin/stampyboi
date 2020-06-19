# Returns YouTube transcripts (including auto-generated) as a list of dictionaries, where each dictionary has 3 values
# 'text': 'string'
# 'start': time in seconds
# 'duration': time in seconds
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from .transcriber import Transcriber
from .utils import extract_words
import json

class YouTube(Transcriber):

	ERROR_MESSAGE = "ERROR:YouTube video is unable to be searched, either because the video/captions are unavailable or the video is age-restricted."
	SPACE_REPLACEMENT_CHAR = '-'

    def __init__(self, source):
        super().__init__()
        self.source = source
        
 #  @staticmethod
 #  def __getVideoId(source):
 #      # Examples:
 #      # - http://youtu.be/SA2iWivDJiE
 #      # - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
 #      # - http://www.youtube.com/embed/SA2iWivDJiE
 #      # - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
 #      query = urlparse(source)
 #      if query.hostname == 'youtu.be': return query.path[1:]
 #      if query.hostname in ('www.youtube.com', 'youtube.com'):
 #          if query.path == '/watch': return parse_qs(query.query)['v'][0]
 #          if query.path[:7] == '/embed/': return query.path.split('/')[2]
 #          if query.path[:3] == '/v/': return query.path.split('/')[2]
 #      # fail?
 #      return None

    def getTranscript(self):
        try:    
            listTranscript = YouTubeTranscriptApi.get_transcript(self.source)
            transcript = list()
            for dic in listTranscript:
                phrase = dic['text']
                time = dic['start']
                words = extract_words(phrase)
				newPhrase = list()
                for word in words:
                    newPhrase.append(word)
				transcript.append((SPACE_REPLACEMENT_CHAR.join(newPhrase), time))
        except:
            transcript = ERROR_MESSAGE
        return transcript        

    def convertToJSON(self, filepath):
      transcript=self.getTranscript()
      text=""
      times=[]
      i=0
      for timestamp in transcript:
          text+=(timestamp[0]+" ")
          times.append(timestamp[1])
      jsonObject={
          "id":self.source,
          "type":"yt",
          "script":text,
          "times":times
      }
      with open(filepath, "w") as outfile:
          json.dump(jsonObject, outfile)
      
 
