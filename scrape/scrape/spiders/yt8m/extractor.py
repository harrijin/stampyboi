'''
Extracts 4-digit encoded video IDs from tensorflow.Examples from Youtube 8M.

$ cd records
$ curl data.yt8m.org/download.py | partition=2/video/train mirror=us python

'''

import tensorflow as tf
import numpy as np
import os

filenames = []

for file in os.listdir(os.getcwd() + "/records"):
    if file.endswith(".tfrecord"):
        filenames.append("records/" + file)

raw_dataset = tf.data.TFRecordDataset(filenames)

output = open('../ids.txt', 'w')
for raw_record in raw_dataset.take(-1): # grab all the records
    example = tf.train.Example()
    example.ParseFromString(raw_record.numpy()) # turn it into an example
    id = str(example.features.feature['id'].bytes_list.value[0]) # extract the id feature (bytes)
    id = id[2:6] # remove the byte stuff

    output.write(id + "\n")
output.close()