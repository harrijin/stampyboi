#Put all the tfrecord files in the same directory

import tensorflow as tf
import numpy as np
import os

filenames = []

for file in os.listdir(os.getcwd()):
    if file.endswith(".tfrecord"):
        filenames.append(file)

raw_dataset = tf.data.TFRecordDataset(filenames)

for raw_record in raw_dataset.take(-1): #grab all the records
    example = tf.train.Example()
    example.ParseFromString(raw_record.numpy()) #turn it into an example
    id = str(example.features.feature['id'].bytes_list.value[0]) #extract the id feature (bytes)
    id = id[2:6] #remove the byte stuff

    print(id)
