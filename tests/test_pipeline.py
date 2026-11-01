"""Simulator, preprocessing and dataset (C1, C2, D1)."""
import numpy as np
import pytest

from data_pipeline.preprocessing import Pipeline, normalize
from data_pipeline.simulator import Runner, parse_schedule, safe_run_id, samples, schedule_samples
from training.generate_dataset import windows


def test_stream_rates_and_door_events():
    rows = list(samples('none', 120))
    assert sum(k == 'temperature' for k, _ in rows) == 120
    assert sum(k == 'vibration_rms' for k, _ in rows) == 60
    assert {m['value'] for k, m in rows if k == 'door_event'} == {'OPEN', 'CLOSE'}


@pytest.mark.parametrize('mode', ['none', 'temp_drift', 'vibration', 'combined'])
def test_six_finite_features_every_mode(mode):
    x = windows(mode, 600, 1)
    assert x.shape == (57, 6) and np.isfinite(x).all()


def test_anomaly_parameters():
    drift = windows('temp_drift', 300, 1)
    vib = windows('vibration', 300, 1)
    assert drift[:, 2].mean() > 4          # ~4.8 C/min rate of change
    assert vib[:, 3].mean() > 1.0          # RMS stepped to ~1.2 g
    assert abs(windows('none', 600, 1)[:, 0].mean() - 4.0) < 0.15


def test_schedule_is_continuous_and_drift_restarts():
    temps = [m for k, m in schedule_samples([('none', 100), ('combined', 50), ('none', 50)], 1) if k == 'temperature']
    assert [m['timestamp'] for m in temps] == [float(i) for i in range(200)]
    v = np.array([m['value'] for m in temps])
    assert v[149] > 7 and abs(v[150:].mean() - 4) < 0.3


def test_control_switch_and_validation():
    r = Runner([('none', 10)])
    r.step(0, 0.0)
    r.request('combined')
    assert r.step(1, 1.0)[1]['source'] == 'control' and r.mode == 'combined'
    with pytest.raises(ValueError):
        r.request('meltdown')
    with pytest.raises(ValueError):
        parse_schedule('bogus:5')
    with pytest.raises(ValueError):
        safe_run_id('../etc')


def test_duplicates_bounded_memory_and_gap_reset():
    p = Pipeline()
    p.push('temperature', {'timestamp': 0, 'value': 4})
    p.push('temperature', {'timestamp': 0, 'value': 9})
    assert len(p.buf['temperature']) == 1
    for i in range(1, 1000):
        p.push('temperature', {'timestamp': i, 'value': 4})
    assert len(p.buf['temperature']) <= 128
    p.push('temperature', {'timestamp': 1020, 'value': 8})
    assert list(p.ma['temperature']) == [8]


def test_rejects_bad_input_and_out_of_order_door():
    p = Pipeline()
    with pytest.raises(ValueError):
        p.push('temperature', {'timestamp': 1, 'value': float('nan')})
    p.push('door_event', {'timestamp': 10, 'value': 'OPEN'})
    p.push('door_event', {'timestamp': 9, 'value': 'CLOSE'})
    assert p.door == 'OPEN'


def test_frozen_stats_and_shift():
    s = np.stack([np.arange(6), np.arange(1, 7)]).astype(np.float32)
    np.testing.assert_allclose(normalize(s[0], s), 0)
    np.testing.assert_allclose(normalize(s[0], np.stack([s[0] + 3 * s[1], s[1]])), -3)
    with pytest.raises(ValueError):
        normalize(np.zeros(6), np.zeros((2, 6)))


def test_generated_dataset_split_is_clean():
    d = np.load('training/data/dataset.npz')
    assert set(d['y']) == {0, 1, 2} and len(d['train']) >= 200
    assert not set(d['train']) & set(d['val'])
    assert np.load('training/data/reference_clean.npy').shape == (300, 6)
