import numpy as np
import functools
import operator


def img2chromosome(img_arr):
    return np.reshape(a=img_arr, newshape=(functools.reduce(operator.mul, img_arr.shape)))


def chromosome2img(vector, shape):
    if len(vector) != functools.reduce(operator.mul, shape):
        raise ValueError("A vector of length {vector_length} into an array of shape {shape}.".format(
            vector_length=len(vector), shape=shape))
    return np.reshape(a=vector, newshape=shape)
