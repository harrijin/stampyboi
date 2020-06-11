import numpy as np
import deepspeech
from scipy.io.wavfile import read 

def main():
    model = deepspeech.Model('deepspeech-0.7.3-models.pbmm')
    model.enableExternalScorer('deepspeech-0.7.3-models.scorer')
    stream = model.createStream()
    audio_array = read('gettysburg.wav')
    audio = np.array(audio_array[1],dtype=np.int16)

    print(model.stt(audio))

main()
