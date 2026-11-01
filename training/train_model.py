"""D1/F1 M1: 6-32-16-3 ReLU MLP (FP32). Gate: validation accuracy must exceed 88%."""
import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from data_pipeline.preprocessing import normalize, write_pipeline_contract


def build():
    return tf.keras.Sequential([tf.keras.layers.Input((6,)),
                                tf.keras.layers.Dense(32, activation='relu'),
                                tf.keras.layers.Dense(16, activation='relu'),
                                tf.keras.layers.Dense(3, activation='softmax')])


def main():
    tf.keras.utils.set_random_seed(42)
    d = np.load('training/data/dataset.npz')
    X = normalize(d['X'], np.load('data_pipeline/training_stats.npy'))
    y, tr, va = d['y'], d['train'], d['val']
    model = build()
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss='sparse_categorical_crossentropy')
    model.fit(X[tr], y[tr], epochs=100, batch_size=32, verbose=2)
    pred = model.predict(X[va], verbose=0).argmax(1)
    acc = float(accuracy_score(y[va], pred))
    Path('training/models').mkdir(parents=True, exist_ok=True)
    Path('optimisation/results').mkdir(parents=True, exist_ok=True)
    model.save('training/models/M1.keras')
    write_pipeline_contract('training/models/M1.keras')
    Path('training/models/M1_fp32.tflite').write_bytes(tf.lite.TFLiteConverter.from_keras_model(model).convert())
    write_pipeline_contract('training/models/M1_fp32.tflite')
    result = {'accuracy': acc, 'confusion_matrix': confusion_matrix(y[va], pred, labels=[0, 1, 2]).tolist(),
              'report': classification_report(y[va], pred, labels=[0, 1, 2], output_dict=True, zero_division=0)}
    Path('optimisation/results/training_metrics.json').write_text(json.dumps(result, indent=2))
    print(f'validation accuracy {acc:.4f}')
    if acc <= 0.88:
        raise SystemExit('Accuracy is not above 88%: revisit features/architecture before continuing (brief D1).')


if __name__ == '__main__':
    main()
