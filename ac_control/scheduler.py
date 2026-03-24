# Scheduler module for AC control system

from __future__ import annotations

# Import necessary modules
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from ac_control.automation import ACController
from ac_control.state import StatusSnapshot, StatusStore

# Utility functions for time conversion
def _time_str_to_minutes(value: str) -> int:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError("Time must be in HH:MM format.")
    hour = int(parts[0])
    minute = int(parts[1])
    if not (0 <= hour < 24 and 0 <= minute < 60):
        raise ValueError("Hour must be 0-23 and minute must be 0-59.")
    return hour * 60 + minute

# Utility function to convert minutes since midnight back to HH:MM string
def _minutes_to_time_str(value: int) -> str:
    hours, minutes = divmod(value, 60)
    return f"{hours:02d}:{minutes:02d}"

# Data class representing a single schedule entry
@dataclass
class Schedule:

    # Member variables
    id: str
    name: str
    start_minutes: int
    end_minutes: int
    on_duration: int
    off_duration: int

    # Method to check if this schedule overlaps with another schedule
    def overlaps(self, other: "Schedule") -> bool:
        return not (self.end_minutes <= other.start_minutes or other.end_minutes <= self.start_minutes)

    # Method to check if this schedule is active at a given time (in minutes since midnight)
    def is_active_at(self, minutes_since_midnight: int) -> bool:
        return self.start_minutes <= minutes_since_midnight < self.end_minutes

    # Method to convert the schedule to a dictionary for JSON serialization
    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "start_time": _minutes_to_time_str(self.start_minutes),
            "end_time": _minutes_to_time_str(self.end_minutes),
            "on_duration_seconds": self.on_duration,
            "off_duration_seconds": self.off_duration,
        }

# Timetable class to manage multiple schedules and determine active schedule
# at any given time
class Timetable:

    def __init__(self) -> None:
        # Use a lock to ensure thread-safe access to schedules
        self._lock = threading.Lock()
        # Store schedules in a dictionary keyed by schedule ID
        self._schedules: Dict[str, Schedule] = {}

    # Method to add a new schedule, ensuring it does not overlap with existing
    # schedules
    def add_schedule(
        self,
        start_time: str,
        end_time: str,
        on_duration: int,
        off_duration: int,
        name: Optional[str] = None,
    ) -> Schedule:
        
        """
        Arguments:
            start_time: Start time in "HH:MM" format                    
            end_time: End time in "HH:MM" format
            on_duration: Duration in seconds for which AC should be ON during active period
            off_duration: Duration in seconds for which AC should be OFF during active period
            name: Optional name for the schedule (if not provided, a default name will be generated)
        Returns:
            The created Schedule object
        Raises:
            ValueError: If input values are invalid or if the new schedule overlaps with existing schedules
        """
        
        # Get inputs and do conversions
        start_minutes = _time_str_to_minutes(start_time)
        end_minutes = _time_str_to_minutes(end_time)

        # Validate inputs
        if end_minutes <= start_minutes:
            raise ValueError("End time must be after start time.")
        if on_duration <= 0:
            raise ValueError("On duration must be greater than zero.")
        if off_duration <= 0:
            raise ValueError("Off duration must be greater than zero.")

        # Generate a name if not provided
        schedule_name = name or f"Schedule {_minutes_to_time_str(start_minutes)}-{_minutes_to_time_str(end_minutes)}"
        
        # Create the schedule object
        schedule = Schedule(
            id = str(uuid.uuid4()),
            name = schedule_name,
            start_minutes = start_minutes,
            end_minutes = end_minutes,
            on_duration = on_duration,
            off_duration = off_duration,
        )

        # Add the schedule to the timetable, ensuring no overlaps
        with self._lock:
            for existing in self._schedules.values():
                if schedule.overlaps(existing):
                    raise ValueError("New schedule overlaps with an existing schedule.")
            self._schedules[schedule.id] = schedule
        return schedule

    # to remove a schedule by ID
    def remove_schedule(self, schedule_id: str) -> bool:
        with self._lock:
            return self._schedules.pop(schedule_id, None) is not None

    # to list all schedules sorted by start time
    def list_schedules(self) -> List[Schedule]:
        with self._lock:
            return sorted(self._schedules.values(), key = lambda s: s.start_minutes)

    # to get a list of schedule dictionaries for JSON serialization
    def list_schedule_dicts(self) -> List[Dict[str, object]]:
        return [schedule.to_dict() for schedule in self.list_schedules()]

    # to determine which schedule (if any) is active at a given timestamp
    # Returns the active Schedule object or None if no schedule is active
    def active_at(self, timestamp: datetime) -> Optional[Schedule]:
        minute_of_day = timestamp.hour * 60 + timestamp.minute
        with self._lock:
            for schedule in self._schedules.values():
                if schedule.is_active_at(minute_of_day):
                    return schedule
        return None

# Thread class to run the scheduler in the background, periodically checking the
# active schedule and toggling the AC state accordingly
# (controller)
class ScheduleRunner(threading.Thread):

    RETRY_DELAY_SECONDS = 5  # seconds to wait before retrying a failed toggle

    def __init__(
        self,
        controller: ACController,
        timetable: Timetable,
        status_store: StatusStore,
        poll_interval: float = 1.0,
        retry_delay_seconds: Optional[int] = None,
    ) -> None:
        
        """
        Arguments:
            controller: An instance of ACController to interact with the AC unit
            timetable: An instance of Timetable to manage schedules
            status_store: An instance of StatusStore to store status snapshots
            poll_interval: How often (in seconds) to check the active schedule and AC status
            retry_delay_seconds: How long to wait (in seconds) before retrying a failed toggle (if None, defaults to RETRY_DELAY_SECONDS)
        """
        
        super().__init__(daemon = True)

        self.controller = controller
        self.timetable = timetable
        self.status_store = status_store
        self.poll_interval = poll_interval
        self.retry_delay_seconds = (
            retry_delay_seconds if retry_delay_seconds is not None else self.RETRY_DELAY_SECONDS
        )

        self._stop_event = threading.Event()
        self._active_schedule: Optional[Schedule] = None
        self._phase: Optional[str] = None
        self._next_switch_at: Optional[datetime] = None

    # Method to signal the thread to stop
    def stop(self) -> None:
        self._stop_event.set()

    # Main loop of the thread, which periodically checks the active schedule and
    # toggles the AC state as needed
    def run(self) -> None:
        # While thread should be running
        while not self._stop_event.is_set():
            # Run one tick of the scheduler logic
            self._tick()
            # Wait for the specified poll interval or until stop event is set
            self._stop_event.wait(self.poll_interval)

    # Internal method to perform one tick of the scheduler logic
    def _tick(self) -> None:

        # Get the current time, AC status, and balance from the controller
        now = datetime.now()
        status = self.controller.get_status()
        balance = self.controller.get_balance()

        # Determine the active schedule based on the current time
        active_schedule = self.timetable.active_at(now)

        # If there is no active schedule, reset the state and clear any
        # pending switches
        if not active_schedule:
            self._active_schedule = None
            self._phase = None
            self._next_switch_at = None
        else:
            # If the active schedule has changed since the last tick,
            # reset the state
            if not self._active_schedule or self._active_schedule.id != active_schedule.id:
                self._active_schedule = active_schedule
                self._phase = None
                self._next_switch_at = None
            # If there is an active schedule and the AC status is not "nil",
            # apply the schedule logic to determine if we need to toggle the
            # AC state
            if status != "nil":
                status = self._apply_schedule(now, status)

        # After processing the schedule logic, calculate next switch time
        next_switch_time = self._next_switch_at.strftime("%Y-%m-%d %H:%M:%S") if self._next_switch_at else None

        # Create a status snapshot and store it in the status store
        snapshot = StatusSnapshot(
            current_time = now.strftime("%Y-%m-%d %H:%M:%S"),
            balance = balance,
            status = status,
            active_schedule_id = self._active_schedule.id if self._active_schedule else None,
            active_schedule_name = self._active_schedule.name if self._active_schedule else None,
            schedule_phase = self._phase,
            next_switch_time = next_switch_time,
            schedules = self.timetable.list_schedule_dicts(),
        )
        # Update the status store with the new snapshot
        self.status_store.set_snapshot(snapshot)

    # Internal method to apply the active schedule logic and determine if we need
    # to toggle the AC state. Returns the updated status after applying the schedule.
    def _apply_schedule(self, now: datetime, status: str) -> str:

        # If there is no active schedule, just return the current status without
        # making any changes
        if not self._active_schedule:
            return status

        # If we have an activate schedule, but we haven't yet determined the phase
        # or next switch time, we initialize it (turn it ON)
        if self._next_switch_at is None:
            success, status = self._ensure_state("ON", status)
            if success:
                self._phase = "on"
                self._next_switch_at = now + timedelta(seconds = self._active_schedule.on_duration)
            return status

        # If the next switch time has not yet arrived, do nothing
        if now < self._next_switch_at:
            return status

        # HERE, the next switch time has arrived
        # Determine the desired state based on the current phase 
        # (if we are currently in the "on" phase, we want to switch to "OFF", 
        # and vice versa)
        desired_state = "OFF" if self._phase == "on" else "ON"
        success, status = self._ensure_state(desired_state, status)
        if success:
            self._phase = "off" if self._phase == "on" else "on"
            interval = (
                self._active_schedule.off_duration if self._phase == "off" else self._active_schedule.on_duration
            )
            self._next_switch_at = now + timedelta(seconds = interval)
        else:
            self._next_switch_at = now + timedelta(seconds = self.retry_delay_seconds)

        return status

    # Internal method to ensure the AC is in the desired state, toggling it if necessary.
    # Returns a tuple of (success, updated_status) where success is a boolean indicating
    # whether the AC is now in the desired state, and updated_status is the current status
    # after attempting to toggle if needed.
    # NOTE: this method toggles the AC switch
    def _ensure_state(self, desired_state: str, current_status: str) -> Tuple[bool, str]:
        if desired_state not in ("ON", "OFF"):
            return False, current_status
        if current_status == desired_state:
            return True, current_status
        if current_status == "nil":
            return False, current_status

        success = self.controller.toggle_power()
        if not success:
            return False, current_status

        updated_status = self.controller.get_status()
        return updated_status == desired_state, updated_status