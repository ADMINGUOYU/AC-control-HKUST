# This module defines the StatusSnapshot dataclass to represent
# the current state of the AC system, and the StatusStore class
# to manage thread-safe access to the current status snapshot.

from __future__ import annotations

import threading
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

# The StatusSnapshot dataclass represents the current state of
# the AC system, including time, balance, status, schedule info,
# and on/off times.
@dataclass
class StatusSnapshot:
    # Basic status fields
    current_time: str = "nil"
    balance: str = "nil"
    status: str = "nil"
    # Schedule-related fields
    active_schedule_id: Optional[str] = None
    active_schedule_name: Optional[str] = None
    schedule_phase: Optional[str] = None
    next_switch_time: Optional[str] = None
    schedules: List[Dict[str, object]] = field(default_factory = list)

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)

# The StatusStore class provides thread-safe access to the current
# status snapshot, allowing multiple threads to read and update
# the AC status without conflicts.
class StatusStore:

    """
    Thread-safe storage for AC status snapshots.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot = StatusSnapshot()

    def set_snapshot(self, snapshot: StatusSnapshot) -> None:
        with self._lock:
            self._snapshot = snapshot

    def get_snapshot(self) -> StatusSnapshot:
        with self._lock:
            return self._snapshot