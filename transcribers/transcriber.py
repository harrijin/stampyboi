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
from abc import ABC, abstractmethod, json

class Transcriber(ABC):
    def __init__(self, source)
        self.source = source
        super().__init__()

    def separatePhrases(phrases)
        words = OrderedDict()
        for key, value in phrases.items():
            splitPhrase=value.split()
            msIncrement=0
            for word in splitPhrase
                words(key+msIncrement) = word
                msIncrement+=0.01

        return words

    @abstractmethod
    def getTranscript()
        pass
#       Call separatePhrases() here if necessary

    def convertToJSON()
        with open("transcript.json", "w") as outfile:
            json.dumps(getTranscript(), outfile)

