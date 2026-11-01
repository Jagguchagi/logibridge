"""Run a command, stream its output to the console and a log file, and keep its real exit code
(a shell `| tee` would hide failures)."""
import codecs
import subprocess
from pathlib import Path


def run(command, log):
    log = Path(log)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('w') as f:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        dec = codecs.getincrementaldecoder('utf-8')('replace')
        while chunk := proc.stdout.read1(4096):
            text = dec.decode(chunk)
            f.write(text)
            print(text, end='', flush=True)
        tail = dec.decode(b'', final=True)
        f.write(tail)
        return proc.wait()
