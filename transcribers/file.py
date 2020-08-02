import numpy as np
import deepspeech
import sys, subprocess, json
import wave, shlex
import moviepy
from moviepy.audio.io.AudioFileClip import AudioFileClip
from os.path import splitext
from timeit import default_timer as timer
from .transcriber import Transcriber

try:
    from shlex import quote
except ImportError:
    from pipes import quote

class FileExtractor(Transcriber):
    def __init__(self, source, model):
        super().__init__()
        self.source = source
        # print('Source File: ' + self.source)
        self.model = model

    def getTranscript(self):
        rate_model = self.model.sampleRate()
        # print('Model SR: {}Hz'.format(rate_model))

        extension = splitext(self.source)[1]
        if extension in ['.ogv', '.mp4', '.mpeg', '.avi', '.mov']:
            # print('Extracting audio from video format ' + extension)
            audio, audio_length = video2Audio(self.source)
        else:
            wav = wave.open(self.source, 'rb')
            rate_orig = wav.getframerate()
            if rate_orig != rate_model:
                audio = convert_samplerate(self.source, rate_model)
            else:
                audio = np.frombuffer(wav.readframes(wav.getnframes()), np.int16)
            wav.close()
            audio_length = wav.getnframes() * (1/rate_orig)

            # print('Source SR: {}Hz'.format(rate_orig))

        # timeElapsed = timer()
        transcript = self.model.sttWithMetadata(audio, 1).transcripts[0]
        # timeElapsed = timer() - timeElapsed

        # print('Audio length: %.3f' % (audio_length))
        # print('Time elapsed: %.3f' % (timeElapsed))
        # print()
        # print(''.join(token.text for token in metadata.tokens))
        # print()

        result = metadata_to_list(transcript)
        return result, audio_length

    def convertToJSON(self, filepath):
        pass

def video2Audio(video_file):
    '''Takes in any extension supported by ffmpeg: .ogv, .mp4, .mpeg, .avi, .mov, etc'''
    audio = AudioFileClip(video_file, nbytes=2, fps=16000)
    sound_array = audio.to_soundarray(fps=16000, quantize=True, nbytes=2)

    if audio.nchannels == 2:
        sound_array = sound_array.sum(axis=1) / 2
        sound_array = sound_array.astype(np.int16)

    return sound_array, audio.duration

def convert_samplerate(audio_path, desired_sample_rate):
    sox_cmd = 'sox {} --type raw --bits 16 --channels 1 --rate {} --encoding signed-integer --endian little --compression 0.0 --no-dither - '.format(quote(audio_path), desired_sample_rate)
    try:
        output = subprocess.check_output(shlex.split(sox_cmd), stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError('SoX returned non-zero status: {}'.format(e.stderr))
    except OSError as e:
        raise OSError(e.errno, 'SoX not found, use {}hz files or install it: {}'.format(desired_sample_rate, e.strerror))

    return np.frombuffer(output, np.int16)

def metadata_to_list(metadata):
    result = []
    word = ''
    stamp = None
    for token in metadata.tokens:
        if token.text == ' ' and stamp is not None:
            result.append((word, stamp))
            word = ''
        else:
            if word == '':
                stamp = token.start_time
            word += str(token.text)
    if word != '':
        result.append((word, stamp))

    return result

# DEBUG STUFF
# trans = FileExtractor('uploadedFiles/gettysburg.wav')
# result = trans.getTranscript()
# print(json.dumps(result, sort_keys=True, indent=4))