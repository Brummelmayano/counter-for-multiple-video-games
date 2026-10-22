"""Essais du vrai processus parent/enfant avec périphérique simulé, hors carte SD."""
import csv
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
FAKE_CV2 = '''
import os, time
CAP_V4L2=1
CAP_PROP_BUFFERSIZE=2
CAP_PROP_FRAME_WIDTH=3
CAP_PROP_FRAME_HEIGHT=4
CAP_PROP_FPS=5
IMWRITE_JPEG_QUALITY=6
def setNumThreads(n): pass
class Frame:
    size=12
    shape=(2,2,3)
class Jpeg:
    def tobytes(self): return b"\\xff\\xd8FAKE_JPEG_TEST_ONLY\\xff\\xd9"
def imencode(*args): return True, Jpeg()
class VideoCapture:
    def __init__(self,*args): pass
    def isOpened(self): return True
    def set(self,*args): return True
    def get(self,*args): return 30
    def grab(self):
        time.sleep(60 if os.environ.get("FAKE_HANG") else 0.01)
        return True
    def retrieve(self): return True,Frame()
    def release(self): pass
'''


class ProcessTests(unittest.TestCase):
    def prepare(self, directory):
        directory = Path(directory)
        shutil.copyfile(ROOT / 'capture.py', directory / 'capture.py')
        (directory / 'cv2.py').write_text(FAKE_CV2)
        cfg = json.loads((ROOT / 'config.json').read_text())
        cfg.update(device='/dev/null', interval_min_s=0.05, interval_max_s=0.08,
                   reserve_free_gib=0.001, retry_s=0.05, request_timeout_s=2)
        (directory / 'config.json').write_text(json.dumps(cfg))
        return directory

    def test_real_parent_child_scheduler_and_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = self.prepare(tmp)
            result = subprocess.run([sys.executable, str(folder/'capture.py'), '--max-images', '3'],
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            sessions = list((folder/'dataset').glob('session_*'))
            self.assertEqual(len(sessions), 1)
            rows = list(csv.DictReader((sessions[0]/'captures.csv').read_text().splitlines()))
            self.assertEqual(len(rows), 3)
            self.assertEqual(json.loads((sessions[0]/'status.json').read_text())['state'], 'stopped')
            for row in rows[1:]:
                self.assertGreaterEqual(float(row['delta_t_s'])+1e-6, float(row['requested_interval_s']))
            check = subprocess.run([sys.executable, str(ROOT/'verify_dataset.py'), str(folder/'dataset')],
                                   capture_output=True, text=True)
            self.assertEqual(check.returncode, 0, check.stdout+check.stderr)

    def test_hung_video_timeout_and_clean_shutdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = self.prepare(tmp)
            cfg = json.loads((folder/'config.json').read_text())
            cfg['request_timeout_s'] = 0.4
            (folder/'config.json').write_text(json.dumps(cfg))
            env = dict(os.environ, FAKE_HANG='1')
            process = subprocess.Popen([sys.executable, str(folder/'capture.py')], env=env,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                deadline = time.monotonic()+8
                timed_out = False
                while time.monotonic() < deadline:
                    for file in (folder/'dataset').glob('session_*/events.jsonl'):
                        if 'dépassé' in file.read_text():
                            timed_out = True
                            break
                    if timed_out: break
                    time.sleep(0.05)
                self.assertTrue(timed_out)
                process.send_signal(signal.SIGTERM)
                _, stderr = process.communicate(timeout=6)
                self.assertEqual(process.returncode, 0, stderr)
                self.assertEqual(list((folder/'dataset').rglob('*.jpg')), [])
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()


if __name__ == '__main__':
    unittest.main()
