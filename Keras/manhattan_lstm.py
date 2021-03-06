import os, datetime, argparse
from sys import exit

from time import time
from math import exp
import numpy as np

import matplotlib
from matplotlib import pyplot as plt

# DL Imports
import tensorflow as tf

import keras
import keras.backend as K
from keras.models import Model, model_from_json
from keras.layers import Activation, Embedding, Input
from keras.layers import LSTM, Lambda, concatenate
from keras import regularizers

# Custom Modules
from data import Data
from embedding_google import Get_Embedding

def exponent_neg_manhattan_distance(x, hidden_size=50):
    ''' Helper function for the similarity estimate of the LSTMs outputs '''
    return K.exp(-K.sum(K.abs(x[:,:hidden_size] - x[:,hidden_size:]), axis=1, keepdims=True))

def exponent_neg_cosine_distance(x, hidden_size=50):
    ''' Helper function for the similarity estimate of the LSTMs outputs '''
    leftNorm = K.l2_normalize(x[:,:hidden_size], axis=-1)
    rightNorm = K.l2_normalize(x[:,hidden_size:], axis=-1)
    return K.exp(K.sum(K.prod([leftNorm, rightNorm], axis=0), axis=1, keepdims=True))

def get_model(max_len, embedding_size, vocab_size, embedding, hidden_size, distance_metric):
    seq_1 = Input(shape=(max_len,), dtype='int32', name='sequence1')
    seq_2 = Input(shape=(max_len,), dtype='int32', name='sequence2')

    embed_layer = Embedding(output_dim=embedding_size, input_dim=vocab_size+1, input_length=max_len, trainable=False)
    embed_layer.build((None,))
    embed_layer.set_weights([embedding.embedding_matrix])

    input_1 = embed_layer(seq_1)
    input_2 = embed_layer(seq_2)

    l1 = LSTM(units=hidden_size)

    l1_out = l1(input_1)
    l2_out = l1(input_2)

    concats = concatenate([l1_out, l2_out], axis=-1)

    if distance_metric == 'cosine': main_output = Lambda(exponent_neg_cosine_distance, output_shape=(1,))(concats)
    else: main_output = Lambda(exponent_neg_manhattan_distance, output_shape=(1,))(concats)

    model = Model(inputs=[seq_1, seq_2], outputs=[main_output])
    
    return model

def save_model(model):
    # serialize model to JSON
    model_json = model.to_json()
    with open("../Models/model.json", "w") as json_file:
        json_file.write(model_json)
    # serialize weights to HDF5
    model.save_weights("../Models/model.h5")
    print("Saved model to disk")

def load_model(model):
    # load json and create model
    json_file = open('../Models/model.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    loaded_model = model_from_json(loaded_model_json)
    # load weights into new model
    loaded_model.load_weights("../Models/model.h5")
    print("Loaded model from disk")

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("-dn", "--data_name", type=str, help="Dataset name.", default="sick")
    parser.add_argument("-df", "--data_file", type=str, help="Path to dataset.", default="../Datasets/SICK.tsv")
    parser.add_argument("-e", "--embd_file", type=str, help="Path to Embedding File.", default="../Embeddings/GoogleNews/GoogleNews-vectors-negative300.bin.gz")
    parser.add_argument("-tr", "--training_ratio", type=float, help="Ratio of training set.", default=0.8)
    parser.add_argument("-l", "--max_len", type=int, help="Maximum number of words in a sentence.", default=20)
    parser.add_argument("-z", "--hidden_size", type=int, help="Number of Units in LSTM layer.", default=50)
    parser.add_argument("-b", "--batch_size", type=int, help="Batch Size.", default=32)
    parser.add_argument("-n", "--num_iters", type=int, help="Number of iterations/epochs.", default=7)
    parser.add_argument("-lr", "--learning_rate", type=float, help="Learning rate for optimizer.", default=1.0)
    parser.add_argument("-dm", "--distance_metric", type=str, help="Metric for computing distance between input sequences (manhattan/cosine).", default='manhattan')

    args = parser.parse_args()

    # Explicitly mentioned to take care of invalid inputs
    distance_metric = 'manhattan'
    if args.distance_metric == 'cosine': distance_metric = 'cosine'

    print('## Reading Data.', end="\n\n")
    data = Data(args.data_name, args.data_file, args.training_ratio, args.max_len)

    x_train, y_train = data.x_train, data.y_train
    x_val, y_val = data.x_val, data.y_val
    vocab_size = data.vocab_size
    max_len = data.max_len

    print('\n')
    print('## Number of training samples        :', len(x_train[0]))
    print('## Number of validation samples      :', len(x_val[0]))
    print('## Maximum sequence length           :', max_len)
    print('\n\n')

    print('## Building Embedding Matrix', end="\n\n")
    embedding = Get_Embedding(args.embd_file, data.word_to_id)
    embedding_size = embedding.embedding_matrix.shape[1]

    print('## Building model.', end="\n\n")
    model = get_model(max_len, embedding_size, vocab_size, embedding, args.hidden_size, distance_metric)

    opt = keras.optimizers.Adadelta(lr=args.learning_rate, clipnorm=1.25)

    model.compile(optimizer=opt, loss='mean_squared_error', metrics=['accuracy'])
    model.summary()

    print("## Start Training", end="\n\n")
    training_start_time = time()

    history = model.fit(x_train, y_train, validation_data=(x_val, y_val),
                        epochs=args.num_iters, batch_size=args.batch_size, verbose=1)

    print("## Training time finished.\n{} epochs in {}".format(args.num_iters, datetime.timedelta(seconds=time()-training_start_time)), end="\n\n")

    print('## Saving Model')
    save_model(model)

    print("## Plotting Model Accuracy and Loss")
    # "Accuracy"
    plt.figure(1)
    plt.plot(history.history['accuracy'])
    plt.plot(history.history['val_accuracy'])
    plt.title('Model Accuracy')
    plt.ylabel('accuracy')
    plt.xlabel('epoch')
    plt.legend(['Training', 'Validation'], loc='upper left')
    plt.show()

    # "Loss"
    plt.figure(2)
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('Model Loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['Training', 'Validation'], loc='upper left')
    plt.show()
