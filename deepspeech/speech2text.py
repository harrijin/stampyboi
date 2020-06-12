import numpy as np
import deepspeech
import wave
import sys
import shlex
import subprocess
import json
import moviepy
from moviepy.video.io.VideoFileClip import VideoFileClip
from os.path import splitext
from timeit import default_timer as timer

try:
    from shlex import quote
except ImportError:
    from pipes import quote

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

    return result

    #return ''.join(token.text+str(token.start_time)+'\n' for token in metadata.tokens)

def metadata_to_text(metadata):
    return ''.join(token.text for token in metadata.tokens)

def speech2Text(audio_file):
    print('Source File: ' + audio_file)
    model = deepspeech.Model('deepspeech-0.7.3-models.pbmm')
    model.enableExternalScorer('deepspeech-0.7.3-models.scorer')
    rate_model = model.sampleRate()
    print('Model SR: {}Hz'.format(rate_model))

    extension = splitext(audio_file)[1]
    if extension in ['.ogv', '.mp4', '.mpeg', '.avi', '.mov']:
        print('Extracting audio from video format '+extension)
        audio, audio_length = video2Audio(audio_file)
    else:
        wav = wave.open(audio_file, 'rb')
        rate_orig = wav.getframerate()
        if rate_orig != rate_model:
            audio = convert_samplerate(audio_file, rate_model)
        else:
            audio = np.frombuffer(wav.readframes(wav.getnframes()), np.int16)
        wav.close()
        audio_length = wav.getnframes() * (1/rate_orig)

        print('Source SR: {}Hz'.format(rate_orig))

    timeElapsed = timer()
    transcript = model.sttWithMetadata(audio, 1).transcripts[0]
    timeElapsed = timer() - timeElapsed

    print('Audio length: %.3f' % (audio_length))
    print('Time elapsed: %.3f' % (timeElapsed))
    print()
    print(metadata_to_text(transcript))
    print()

    result = metadata_to_list(transcript)
    result_json = json.dumps(result)
    print(json.dumps(result, sort_keys=True, indent=4))
    return result, result_json

def video2Audio(video_file):
    '''Takes in any extension supported by ffmpeg: .ogv, .mp4, .mpeg, .avi, .mov, etc'''
    videoClip = VideoFileClip(video_file)
    audio = videoClip.audio
    if audio.nchannels == 2:
        sound_list = []
        temp = audio.to_soundarray(fps=16000, quantize=True, nbytes=2)
        for i in range(len(temp)):
            sound_list.append((temp[i][0] + temp[i][1])/2)
        sound_array = np.array(sound_list, dtype=np.int16)
    else:
        sound_array = audio.to_soundarray(fps=16000, quantize=True, nbytes=2)
    return sound_array, audio.duration

speech2Text(sys.argv[1])
