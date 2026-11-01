"""F1 M2: full-INT8 post-training quantisation with >=200 training-only calibration windows."""
from pathlib import Path

import numpy as np
import tensorflow as tf

from data_pipeline.preprocessing import normalize, write_pipeline_contract, validate_pipeline_contract


def convert(model, out):
    d = np.load('training/data/dataset.npz')
    cal = normalize(d['X'][d['train']], np.load('data_pipeline/training_stats.npy'))
    if len(cal) < 200:
        raise ValueError('need at least 200 training-only calibration windows')

    def representative():
        for row in cal:
            yield [row.reshape(1, 6).astype(np.float32)]
    c = tf.lite.TFLiteConverter.from_keras_model(model)
    c.optimizations = [tf.lite.Optimize.DEFAULT]
    c.representative_dataset = representative
    c.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    c.inference_input_type = tf.int8
    c.inference_output_type = tf.int8
    Path(out).write_bytes(c.convert())
    it = tf.lite.Interpreter(model_path=str(out))
    it.allocate_tensors()
    assert it.get_input_details()[0]['dtype'] == np.int8 and it.get_output_details()[0]['dtype'] == np.int8
    write_pipeline_contract(out)
    return out


def main():
    validate_pipeline_contract('training/models/M1.keras')
    convert(tf.keras.models.load_model('training/models/M1.keras'), 'training/models/M2_int8.tflite')
    Path('inference/model.tflite').write_bytes(Path('training/models/M2_int8.tflite').read_bytes())
    write_pipeline_contract('inference/model.tflite')
    print('M2 written; copied to inference/model.tflite as the provisional deployed model')


if __name__ == '__main__':
    main()
