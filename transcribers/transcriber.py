'''
Abstract class for transcriber classes to inherit from
Attributes:
    source - currently must be a string containing the video source

Methods:
    separatePhrases() - takes in an OrderedDict of the form {time:phrase...}
                        and separates the phrases into timestamped words
    getTranscript() - abstract method that must be implemented by subclasses
    convertToJSON() - call this method to convert a video into a timestamped transcript .JSON file
'''
from abc import ABC, abstractmethod
import json

class Transcriber(ABC):
    def __init__(self):
        super().__init__()


    @abstractmethod
    def getTranscript():
        pass
#       Call separatePhrases() here if necessary

    def convertToJSON(self, filepath):
        with open(filepath, "w") as outfile:
            json.dump(self.getTranscript(), outfile)

