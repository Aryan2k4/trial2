"""Process-local data revision for the single-worker demo deployment.

Every committed transaction invalidates analytics, including bulk writes and
tool handoffs. Model objects remain cached. Multiple workers would require a
shared revision source (for example Redis or a database revision table).
"""
from threading import Lock

_revision = 0
_lock = Lock()


def current_revision():
    with _lock:
        return _revision


def advance_revision(session):
    global _revision
    with _lock:
        _revision += 1
