"""What the System page adds to strata-python's `GET /api/system` (versions, start time, each folder's disk): how many
greetings are kept and how much the app's own folder holds, which the page draws against its disk."""

import contextlib
import os

from strata_python.contracts import ApiModel


class AppNumbers(ApiModel):
    """The app's own fields in `GET /api/system`."""

    greetings: int
    home_bytes: int


def folder_bytes(path: str) -> int:
    """Total size of the files under `path` (files that vanish or cannot be read mid-walk are skipped)."""
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            with contextlib.suppress(OSError):
                total += os.path.getsize(os.path.join(root, name))
    return total
