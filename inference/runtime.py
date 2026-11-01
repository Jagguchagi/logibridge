"""TFLite wrapper: tflite_runtime (in the container) or tf.lite fallback; INT8 (de)quantisation;
last_clipped records which inputs saturated the INT8 range on the last call."""
import numpy as np


def interpreter_class():
    try:
        from tflite_runtime.interpreter import Interpreter
        return Interpreter
    except ImportError:
        import tensorflow as tf
        return tf.lite.Interpreter


class Model:
    def __init__(self, path):
        self.it = interpreter_class()(model_path=str(path), num_threads=1)
        self.it.allocate_tensors()
        self.i, self.o = self.it.get_input_details()[0], self.it.get_output_details()[0]
        if tuple(int(n) for n in self.i['shape']) != (1, 6) or tuple(int(n) for n in self.o['shape']) != (1, 3):
            raise ValueError('expected a (1, 6) -> (1, 3) model')
        self.last_clipped = np.zeros(6, dtype=bool)

    def predict(self, x):
        x = np.asarray(x, dtype=np.float32).reshape(1, 6)
        if not np.isfinite(x).all():
            raise ValueError('non-finite model input')
        self.last_clipped = np.zeros(6, dtype=bool)
        if np.issubdtype(self.i['dtype'], np.integer):
            scale, zero = self.i['quantization']
            if not np.isfinite(scale) or scale <= 0:
                raise ValueError('invalid input quantisation scale')
            q, lim = np.rint(x / scale + zero), np.iinfo(self.i['dtype'])
            self.last_clipped = ((q < lim.min) | (q > lim.max))[0]
            x = np.clip(q, lim.min, lim.max).astype(self.i['dtype'])
        self.it.set_tensor(self.i['index'], x)
        self.it.invoke()
        p = self.it.get_tensor(self.o['index'])[0]
        if np.issubdtype(self.o['dtype'], np.integer):
            scale, zero = self.o['quantization']
            if not np.isfinite(scale) or scale <= 0:
                raise ValueError('invalid output quantisation scale')
            p = (p.astype(np.float32) - zero) * scale
        p = np.asarray(p, dtype=np.float32)
        if not np.isfinite(p).all():
            raise ValueError('non-finite model output')
        return p
