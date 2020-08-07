# Returns YouTube transcripts (including auto-generated) as a list of dictionaries, where each dictionary has 3 values
# 'text': 'string'
# 'start': time in seconds
# 'duration': time in seconds
import json
from youtube_transcript_api import YouTubeTranscriptApi
from .transcriber import Transcriber
from .utils import extract_words

SPACE_REPLACEMENT_CHAR = '-'

class YouTube(Transcriber):
    def __init__(self, source):
        super().__init__()
        self.source = source
        try:
            self.transcript = YouTubeTranscriptApi.get_transcript(self.source)
        except Exception as err:
            self.transcript = str(err)

    def getTranscript(self):
        if isinstance(self.transcript, str):
            return self.transcript

        result = list()
        for dic in self.transcript:
            phrase = dic['text']
            time = int(dic['start'])
            words = extract_words(phrase)
            if len(words) != 0:
                result.append((SPACE_REPLACEMENT_CHAR.join(words), time))
        return result

    def getJSON(self):
        if isinstance(self.transcript, str):
            return self.transcript

        phrase_list = []
        time_list = []
        for dic in self.transcript:
            words = extract_words(dic['text'])
            time = dic['start']
            if len(words) != 0:
                phrase_list.append(SPACE_REPLACEMENT_CHAR.join(words))
                time_list.append(time)
        return {
            "id":self.source,
            "type":"yt",
            "script":' '.join(phrase_list),
            "times":time_list
        }

    def convertToJSON(self, filepath):
        jsonObject = self.getJSON()
        with open(filepath, "w") as outfile:
            json.dump(jsonObject, outfile)
