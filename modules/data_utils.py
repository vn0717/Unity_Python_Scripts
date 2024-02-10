import numpy as np

def destagger_u(U):
    return (U[:,:,1:] + U[:,:,:-1]) / 2

def destagger_v(V):
    return (V[:,1:] + V[:,:-1]) / 2

def destagger_w(W):
    return (W[1:] + W[:-1]) / 2
