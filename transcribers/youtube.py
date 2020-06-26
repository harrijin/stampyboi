# Returns YouTube transcripts (including auto-generated) as a list of dictionaries, where each dictionary has 3 values
# 'text': 'string'
# 'start': time in seconds
# 'duration': time in seconds
import json
from youtube_transcript_api import YouTubeTranscriptApi
from .transcriber import Transcriber
from .utils import extract_words

ERROR_MESSAGE = "ERROR:YouTube video is unable to be searched, either because the video/captions are unavailable or the video is age-restricted."
SPACE_REPLACEMENT_CHAR = '-'

class YouTube(Transcriber):
    def __init__(self, source):
        super().__init__()
        self.source = source

    def getTranscript(self):
        try:
            listTranscript = YouTubeTranscriptApi.get_transcript(self.source)
            transcript = list()
            for dic in listTranscript:
                phrase = dic['text']
                time = dic['start']
                words = extract_words(phrase)
                transcript.append((SPACE_REPLACEMENT_CHAR.join(words), time))
        except:
            transcript = ERROR_MESSAGE
        return transcript

    def convertToJSON(self, filepath):
        transcript=self.getTranscript()
        text=""
        times=[]
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
