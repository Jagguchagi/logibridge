"""Physically remove pruned neurons from Dense-ReLU-Dense-ReLU-Dense, exactly.

A unit whose incoming weights are all zero always outputs ReLU(bias). Removing it is exact only
if that constant is folded into the next layer's bias. Layer 2 is checked after layer-1 removal,
so units fed only by removed (constant) units are also caught.
"""
import numpy as np


def _drop(w_in, b_in, w_out, b_out):
    dead = np.all(w_in == 0, axis=0)
    if dead.all():
        raise ValueError('every unit in a hidden layer is pruned; the layer would be empty')
    b_out = b_out + np.maximum(b_in[dead], 0.0) @ w_out[dead, :]
    keep = ~dead
    return w_in[:, keep], b_in[keep], w_out[keep, :], b_out, np.flatnonzero(dead)


def fold_and_compact(weights):
    w1, b1, w2, b2, w3, b3 = [np.array(w, copy=True) for w in weights]
    w1, b1, w2, b2, gone1 = _drop(w1, b1, w2, b2)
    w2, b2, w3, b3, gone2 = _drop(w2, b2, w3, b3)
    return [w1, b1, w2, b2, w3, b3], {'removed_units': [gone1.tolist(), gone2.tolist()],
                                      'compact_widths': [int(w1.shape[1]), int(w2.shape[1])]}
