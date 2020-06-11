import numpy as np
import deepspeech
import wave
import sys
import shlex
import subprocess
import json

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

    return desired_sample_rate, np.frombuffer(output, np.int16)

def metadata_to_string(metadata):
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

    return json.dumps(result)

    #return ''.join(token.text+str(token.start_time)+'\n' for token in metadata.tokens)

def speech2Text(audio_file):
    print('Source File: ' + audio_file)
    model = deepspeech.Model('deepspeech-0.7.3-models.pbmm')
    model.enableExternalScorer('deepspeech-0.7.3-models.scorer')
    desired_sample_rate = model.sampleRate()
    print('Model: '+str(desired_sample_rate))

    fin = wave.open(audio_file, 'rb')
    fs_orig = fin.getframerate()
    if fs_orig != desired_sample_rate:
        #print('Warning: original sample rate ({}) is different than {}hz. Resampling might produce erratic speech recognition.'.format(fs_orig, desired_sample_rate), file=sys.stderr)
        fs_new, audio = convert_samplerate(audio_file, desired_sample_rate)
    else:
        audio = np.frombuffer(fin.readframes(fin.getnframes()), np.int16)

    print('Source: '+str(fs_orig))

    fin.close()

    print(metadata_to_string(model.sttWithMetadata(audio, 1).transcripts[0]))

speech2Text(sys.argv[1])
