"""
Simple migration helper for the prototype: ensures DB tables exist.
Run: python scripts/migrate.py
"""
import sys, os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.database import init_db

if __name__ == '__main__':
    print('Running migration: ensuring DB tables exist...')
    init_db()
    print('Done.')
