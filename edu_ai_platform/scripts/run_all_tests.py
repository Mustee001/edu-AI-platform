"""
Run the Option A–D test scripts sequentially and stop on failure.
Run: python scripts/run_all_tests.py
"""
import subprocess
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TEST_SCRIPTS = [
    'scripts/test_optionA_client.py',
    'scripts/test_optionB_client.py',
    'scripts/test_optionC_client.py',
    'scripts/test_optionD_client.py',
]

def run_script(path):
    print('\n=== Running:', path)
    p = subprocess.run([sys.executable, os.path.join(ROOT, path)], cwd=ROOT)
    return p.returncode

if __name__ == '__main__':
    for t in TEST_SCRIPTS:
        rc = run_script(t)
        if rc != 0:
            print(f"Test {t} failed with exit code {rc}")
            sys.exit(rc)
    print('\nAll tests passed successfully')
    sys.exit(0)
