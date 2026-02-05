from enum import Enum, auto
import threading
import time

class MatchState(Enum):
    NOT_STARTED = auto()
    ODDS_SCRAPED = auto()
    LIVE = auto()
    FINISHED = auto()

class StateManager:
    """
    Central State Manager for the Virtual Sports Scraper.
    Enforces the strict state transition:
    NOT_STARTED -> ODDS_SCRAPED -> LIVE -> FINISHED
    """
    def __init__(self):
        self._state_lock = threading.RLock()
        self.current_state = MatchState.NOT_STARTED
        self.last_transition_time = time.time()
        self.match_id = None
    
    def get_state(self):
        with self._state_lock:
            return self.current_state

    def reset_for_new_round(self, match_id=None):
        """Resets state for a new round. Only allowed if previous was FINISHED or forced."""
        with self._state_lock:
            self.current_state = MatchState.NOT_STARTED
            self.match_id = match_id
            self.last_transition_time = time.time()
            print(f"[STATE] Reset to NOT_STARTED (Match ID: {match_id})")

    def transition_to_odds_scraped(self):
        """Transition to ODDS_SCRAPED state."""
        with self._state_lock:
            if self.current_state == MatchState.NOT_STARTED:
                self.current_state = MatchState.ODDS_SCRAPED
                self.last_transition_time = time.time()
                print("[STATE] Transitioned to ODDS_SCRAPED")
                return True
            return False

    def transition_to_live(self):
        """Transition to LIVE state. One-way only."""
        with self._state_lock:
            if self.current_state in [MatchState.NOT_STARTED, MatchState.ODDS_SCRAPED]:
                self.current_state = MatchState.LIVE
                self.last_transition_time = time.time()
                print("[STATE] Transitioned to LIVE")
                return True
            return False

    def transition_to_finished(self):
        """Transition to FINISHED state."""
        with self._state_lock:
            if self.current_state == MatchState.LIVE:
                self.current_state = MatchState.FINISHED
                self.last_transition_time = time.time()
                print("[STATE] Transitioned to FINISHED")
                return True
            return False

    def is_odds_scraping_allowed(self, time_remaining):
        """Strict rule: Allowed only if NOT_STARTED/ODDS_SCRAPED AND time > 10s."""
        with self._state_lock:
            if self.current_state == MatchState.LIVE or self.current_state == MatchState.FINISHED:
                return False
            if time_remaining <= 10:
                print("[STATE] Odds scraping BLOCKED: Timer <= 10s")
                return False
            return True
