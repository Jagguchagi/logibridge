"""C2/C3: causal 5-sample filter, 30 s windows every 10 s, six-feature fusion, frozen normalisation.

Safeguards: bounded buffers (a silent sensor cannot grow memory), state reset after a >10 s gap
in either numeric stream (no window spans an outage), duplicate/out-of-order messages ignored,
non-finite values rejected. Door state is kept as metadata, not a model feature.
"""
from collections import deque

import numpy as np

FEATURES = ['temperature_mean', 'temperature_std', 'temperature_roc',
            'vibration_rms', 'vibration_peak', 'vibration_kurtosis']
STREAMS = ('temperature', 'vibration_rms')
WINDOW_S, STEP_S, GAP_RESET_S = 30, 10, 10
MIN_TEMP, MIN_VIB = 25, 12


class Pipeline:
    def __init__(self):
        self.reset()
        self.door, self.door_since, self.last_door = 'CLOSE', None, float('-inf')

    def reset(self):
        self.ma = {k: deque(maxlen=5) for k in STREAMS}
        self.buf = {k: deque(maxlen=128) for k in STREAMS}
        self.last = {}
        self.next_end = None

    def push(self, stream, msg):
        t = float(msg['timestamp'])
        if not np.isfinite(t):
            raise ValueError('non-finite timestamp')
        if stream == 'door_event':
            if msg['value'] not in ('OPEN', 'CLOSE'):
                raise ValueError('invalid door state')
            if t > self.last_door:
                self.door, self.door_since, self.last_door = msg['value'], t, t
            return []
        if stream not in STREAMS or t <= self.last.get(stream, float('-inf')):
            return []
        v = float(msg['value'])
        if not np.isfinite(v):
            raise ValueError('non-finite sensor value')
        if stream in self.last and t - self.last[stream] > GAP_RESET_S:
            self.reset()
        self.last[stream] = t
        self.ma[stream].append(v)
        self.buf[stream].append((t, float(np.mean(self.ma[stream]))))
        if self.next_end is None:
            self.next_end = t + WINDOW_S
        out = []
        while len(self.last) == 2 and min(self.last.values()) >= self.next_end:
            end = self.next_end
            a = np.array([p for p in self.buf['temperature'] if end - WINDOW_S <= p[0] < end])
            b = np.array([p for p in self.buf['vibration_rms'] if end - WINDOW_S <= p[0] < end])
            if len(a) >= MIN_TEMP and len(b) >= MIN_VIB:
                out.append((end, features(a, b)))
            self.next_end += STEP_S
            for q in self.buf.values():
                while q and q[0][0] < self.next_end - WINDOW_S:
                    q.popleft()
        return out


def features(temp, vib):
    tv, vv = temp[:, 1], vib[:, 1]
    z = vv - vv.mean()
    var = float(np.mean(z ** 2))
    kurt = float(np.mean(z ** 4) / var ** 2) if var > 1e-12 else 0.0
    slope = float(np.polyfit(temp[:, 0] - temp[0, 0], tv, 1)[0] * 60)  # deg C per minute
    return np.array([tv.mean(), tv.std(), slope, np.sqrt(np.mean(vv ** 2)), vv.max(), kurt],
                    dtype=np.float32)


CLIP_Z = 10.0  # see docs/DISCLOSURES.md: saturate far-out-of-range z-scores


def normalize(x, stats, clip=CLIP_Z):
    """Frozen z-score plus disclosed saturation; clip=None/0 disables saturation.

    Saturation loses magnitude information beyond the cap. A +3 sigma change in
    statistics can change the clipped output; it is NOT guaranteed unaffected.
    Validate inputs before clipping so infinity cannot become a plausible value.
    """
    s = np.asarray(stats, dtype=np.float32)
    if s.shape != (2, 6) or not np.isfinite(s).all() or (s[1] <= 0).any():
        raise ValueError('invalid frozen statistics')
    a = np.asarray(x, dtype=np.float32)
    if a.ndim == 0 or a.shape[-1] != 6 or not np.isfinite(a).all():
        raise ValueError('expected finite six-feature inputs')
    if clip is not None and (type(clip) not in (int, float) or not np.isfinite(clip) or clip < 0):
        raise ValueError('clip must be finite nonnegative number or None')
    with np.errstate(over='ignore', invalid='ignore'):
        z = (a - s[0]) / s[1]
    if not np.isfinite(z).all():
        raise ValueError('non-finite normalized features')
    return np.clip(z, -clip, clip) if clip else z


def pipeline_sha256():
    """Source fingerprint: a preprocessing change invalidates old artifact contracts."""
    import hashlib
    from pathlib import Path
    # Line endings are normalised so a Windows (CRLF) checkout and a Linux/container (LF) copy agree.
    return hashlib.sha256(Path(__file__).read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def write_pipeline_contract(model_path, stats_path='data_pipeline/training_stats.npy'):
    import hashlib, json
    from pathlib import Path
    model, stats = Path(model_path), Path(stats_path)
    contract = {'schema': 1, 'pipeline_sha256': pipeline_sha256(),
                'model_sha256': hashlib.sha256(model.read_bytes()).hexdigest(),
                'stats_sha256': hashlib.sha256(stats.read_bytes()).hexdigest(),
                'clip_z': CLIP_Z}
    Path(str(model) + '.pipeline.json').write_text(json.dumps(contract, indent=2))
    return contract


def validate_pipeline_contract(model_path, stats_path='data_pipeline/training_stats.npy'):
    import hashlib, json
    from pathlib import Path
    model, stats = Path(model_path), Path(stats_path)
    try:
        c = json.loads(Path(str(model) + '.pipeline.json').read_text())
        expected = {'schema': 1, 'pipeline_sha256': pipeline_sha256(),
                    'model_sha256': hashlib.sha256(model.read_bytes()).hexdigest(),
                    'stats_sha256': hashlib.sha256(stats.read_bytes()).hexdigest(),
                    'clip_z': CLIP_Z}
        if not isinstance(c, dict) or any(c.get(k) != v for k, v in expected.items()):
            raise ValueError('contract mismatch')
    except (OSError, ValueError, TypeError) as exc:
        raise ValueError('Missing/stale preprocessing contract: rebuild models with this pipeline') from exc
    return c
