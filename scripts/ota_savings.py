"""D2 bandwidth saving for 85 trucks, from REAL registry manifests (single-platform v2 manifests).
Get them with: curl -s -H 'Accept: application/vnd.docker.distribution.manifest.v2+json' \
  http://localhost:5000/v2/logibridge/manifests/cache-v1 > evidence/manifest_v1.json   (same for cache-v2)
This is payload accounting (compressed blob sizes + manifest), not a packet capture."""
import argparse
import json
from pathlib import Path


def blobs(m):
    if 'manifests' in m:
        raise ValueError('this is a multi-platform index: fetch the single-platform manifest')
    return {d['digest']: int(d['size']) for d in [m['config']] + m['layers']}


def compare(old, new, manifest_bytes, trucks=85, inr_per_mb=0.10):
    a, b = blobs(old), blobs(new)
    ol, nl = old['layers'], new['layers']
    model_only = len(ol) == len(nl) > 0 and ol[:-1] == nl[:-1] and ol[-1]['digest'] != nl[-1]['digest']
    full = sum(b.values()) + manifest_bytes
    incr = sum(v for k, v in b.items() if k not in a) + manifest_bytes
    return {'only_last_layer_changed': model_only, 'full_image_bytes': full, 'incremental_bytes': incr,
            'fleet_saved_MB': round((full - incr) * trucks / 1e6, 3),
            'fleet_saved_INR': round((full - incr) * trucks / 1e6 * inr_per_mb, 2),
            'saved_pct': round(100 * (1 - incr / full), 2), 'trucks': trucks,
            'excludes': 'HTTP/TLS overhead and retries; assumes trucks already hold the old layers'}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--old', default='evidence/manifest_v1.json')
    p.add_argument('--new', default='evidence/manifest_v2.json')
    a = p.parse_args()
    raw = Path(a.new).read_bytes()
    out = compare(json.loads(Path(a.old).read_text()), json.loads(raw), len(raw))
    Path('evidence/ota_savings.json').write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
