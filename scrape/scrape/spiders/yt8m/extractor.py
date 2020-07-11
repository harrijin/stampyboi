'''
Extracts 4-digit encoded video IDs from tensorflow.Examples from Youtube 8M.

$ cd records
$ curl data.yt8m.org/download.py | partition=2/video/train mirror=us python

'''

import tensorflow as tf
import numpy as np
import os, subprocess

def write(filenames, output):
    raw_dataset = tf.data.TFRecordDataset(filenames)
    def parse(proto):
        return tf.io.parse_single_example(proto, {'id' : tf.io.FixedLenFeature([], tf.string)})

    parsed_dataset = raw_dataset.map(parse)

    for features in parsed_dataset:
        id_data = features['id'].numpy()
        output.write(id_data.decode('utf-8') + '\n')

with open('ids.txt', 'w') as output:
    for count in range(1, 101):
        subprocess.run('cd records;curl data.yt8m.org/download.py | shard=%d,100 partition=2/video/train mirror=us python;rm *.json' % count, shell=True)

        filenames = []
        for file in os.listdir(os.getcwd() + '/records'):
            filenames.append('records/' + file)

        write(filenames, output)

        os.chdir('records')
        for file in os.listdir(os.getcwd()):
            os.remove(file)
        os.chdir('..')

        print('Finished shard ' + str(count))