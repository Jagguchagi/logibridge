"""F1 M3: 35% structured pruning (PolynomialDecay 0 -> 0.35), physical compaction, full INT8.

Dense layers have neurons, not convolution filters; "structured" here means whole hidden neurons
(disclosed in docs/DISCLOSURES.md).

Default method (custom): whole hidden neurons are masked, ranked by the L2 norm of their input
column, on the tfmot PolynomialDecay schedule (0 -> 35%). Verified on real TensorFlow (V15 sandbox
run): zero columns [11, 6], compact widths [21, 10], compacted output identical to the masked network.

Why not tfmot prune_low_magnitude(block_size=(fan_in, 1))? Reproduced on tfmot 0.8.1: for a block
that spans a whole kernel dimension, pruning_utils.factorized_pool returns a rank-1 tensor and
expand_tensor then raises "Input tensor must be rank 2" during the first training step. The tfmot
route is kept as --method tfmot only so the failure stays visible; it exits with an explanation.
The method used is recorded in pruning.json so it can be disclosed.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import tensorflow as tf
import tensorflow_model_optimization as tfmot

from data_pipeline.preprocessing import normalize, validate_pipeline_contract, write_pipeline_contract
from training.compaction import fold_and_compact
from training.convert_ptq import convert

TARGET, PRUNE_EPOCHS, FINETUNE_EPOCHS, BATCH = 0.35, 40, 20, 32
EXPECTED_ZERO = [round(32 * TARGET), round(16 * TARGET)]  # [11, 6]


def schedule(n):
    end = int(np.ceil(n / BATCH)) * PRUNE_EPOCHS - 1  # last reachable optimizer step
    return tfmot.sparsity.keras.PolynomialDecay(0.0, TARGET, begin_step=0, end_step=end, frequency=1), end


def flat(model):
    return [w for layer in model.layers for w in layer.get_weights()]


def run_tfmot(base, x, y):
    sched, end = schedule(len(x))
    hidden = {l.name for l in base.layers[:2]}

    def clone_fn(layer):  # fresh layers so the loaded M1 is never modified
        fresh = layer.__class__.from_config(layer.get_config())
        if layer.name in hidden:
            return tfmot.sparsity.keras.prune_low_magnitude(
                fresh, pruning_schedule=sched, block_size=(int(layer.kernel.shape[0]), 1))
        return fresh
    model = tf.keras.models.clone_model(base, clone_function=clone_fn)
    for src, dst in zip(base.layers, model.layers):
        (dst.layer if hasattr(dst, 'layer') else dst).set_weights(src.get_weights())
    model.compile(optimizer=tf.keras.optimizers.Adam(3e-4), loss='sparse_categorical_crossentropy')
    model.fit(x, y, epochs=PRUNE_EPOCHS, batch_size=BATCH, verbose=2,
              callbacks=[tfmot.sparsity.keras.UpdatePruningStep()])
    return tfmot.sparsity.keras.strip_pruning(model), end


def run_custom(base, x, y):
    model = tf.keras.models.clone_model(base)
    model.set_weights(base.get_weights())
    sched, end = schedule(len(x))
    hidden = model.layers[:2]
    rank = [np.argsort(np.linalg.norm(l.get_weights()[0], axis=0)) for l in hidden]
    masks = [np.ones(l.units, dtype=np.float32) for l in hidden]

    class Mask(tf.keras.callbacks.Callback):
        def apply(self):
            for layer, m in zip(hidden, masks):
                k, b = layer.get_weights()
                layer.set_weights([k * m[None, :], b * m])

        def on_train_batch_begin(self, batch, logs=None):
            _, frac = sched(int(self.model.optimizer.iterations.numpy()))
            for j, layer in enumerate(hidden):
                masks[j][rank[j][:int(round(float(frac) * layer.units))]] = 0
            self.apply()

        def on_train_batch_end(self, batch, logs=None):
            self.apply()
    cb = Mask()
    model.compile(optimizer=tf.keras.optimizers.Adam(3e-4), loss='sparse_categorical_crossentropy')
    model.fit(x, y, epochs=PRUNE_EPOCHS, batch_size=BATCH, verbose=2, callbacks=[cb])
    for j in range(2):
        masks[j][rank[j][:EXPECTED_ZERO[j]]] = 0
    cb.apply()
    return model, end


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--method', choices=['tfmot', 'custom'], default='custom')
    a = ap.parse_args()
    tf.keras.utils.set_random_seed(43)
    validate_pipeline_contract('training/models/M1.keras')
    base = tf.keras.models.load_model('training/models/M1.keras')
    before = [w.copy() for w in base.get_weights()]
    d = np.load('training/data/dataset.npz')
    x = normalize(d['X'][d['train']], np.load('data_pipeline/training_stats.npy'))
    y = d['y'][d['train']]
    try:
        pruned, end = (run_tfmot if a.method == 'tfmot' else run_custom)(base, x, y)
    except ValueError as exc:
        if 'rank 2' in str(exc):
            raise SystemExit('tfmot block pruning cannot express whole-column blocks (Input tensor must be rank 2). '
                             'This is a known library limitation, not a data problem: run without --method '
                             '(default custom whole-neuron masks) and disclose it.')
        raise
    if not all(np.array_equal(p, q) for p, q in zip(before, base.get_weights())):
        raise SystemExit('M1 weights changed during pruning; refusing to continue')
    w = flat(pruned)
    zero = [int(np.all(w[i] == 0, axis=0).sum()) for i in (0, 2)]
    if 0 in zero:
        raise SystemExit(f'No whole zero columns {zero}: investigate the pruning run; do not report this model as structured-pruned.')
    cw, rep = fold_and_compact(w)
    widths = rep['compact_widths']
    small = tf.keras.Sequential([tf.keras.layers.Input((6,)),
                                 tf.keras.layers.Dense(widths[0], activation='relu'),
                                 tf.keras.layers.Dense(widths[1], activation='relu'),
                                 tf.keras.layers.Dense(3, activation='softmax')])
    small.set_weights(cw)
    p, q = pruned.predict(x, verbose=0), small.predict(x, verbose=0)
    np.testing.assert_allclose(p, q, atol=1e-5)
    small.compile(optimizer=tf.keras.optimizers.Adam(2e-4), loss='sparse_categorical_crossentropy')
    small.fit(x, y, epochs=FINETUNE_EPOCHS, batch_size=BATCH, verbose=2)
    small.save('training/models/M3.keras')
    write_pipeline_contract('training/models/M3.keras')
    convert(small, 'training/models/M3_pruned_int8.tflite')
    result = {'method_used': a.method, 'target_sparsity': TARGET, 'end_step': end, 'zero_columns': zero,
              'expected_zero_columns': EXPECTED_ZERO, 'compact_widths': widths,
              'removed_fraction_per_layer': [1 - widths[0] / 32, 1 - widths[1] / 16],
              'removed_units': rep['removed_units'],
              'pre_finetune_max_abs_difference': float(np.max(np.abs(p - q))),
              'note': 'Whole Dense neurons, not convolution filters. Report actual fractions, not exactly 35%.'}
    Path('optimisation/results').mkdir(parents=True, exist_ok=True)
    Path('optimisation/results/pruning.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
