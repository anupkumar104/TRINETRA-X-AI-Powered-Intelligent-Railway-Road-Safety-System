import time


class RiskEngine:
    """
    Camera-wise animal presence timer.

    Rules:
    - Each camera has an independent timer.
    - Animal IDs are not required.
    - Same or different animals count as continuous presence.
    - A short detection miss is tolerated.
    - A longer absence resets the timer.
    - CRITICAL alert triggers only once per continuous episode.
    """

    NORMAL_LIMIT = 2.0
    CRITICAL_LIMIT = 5.0
    GRACE_PERIOD = 1.0

    def __init__(self):
        self.camera_states = {}

    def _get_state(self, camera_id):
        return self.camera_states.setdefault(
            camera_id,
            {
                "start_time": None,
                "last_seen": None,
                "critical_triggered": False,
            },
        )

    def evaluate(self, camera_id, animal_detected, now=None):
        """
        Evaluate animal presence for one camera.

        Args:
            camera_id: Unique camera identifier.
            animal_detected: True if an animal is detected in this frame.
            now: Optional monotonic timestamp for testing.

        Returns:
            Dictionary containing risk level, score, duration,
            reason, and one-time critical trigger flag.
        """

        if now is None:
            now = time.monotonic()

        state = self._get_state(camera_id)

        # Start or continue the presence episode.
        if animal_detected:
            if state["start_time"] is None:
                state["start_time"] = now
                state["critical_triggered"] = False

            state["last_seen"] = now

        else:
            last_seen = state["last_seen"]

            # Reset only after the detection has been absent
            # longer than the grace period.
            if (
                last_seen is not None
                and now - last_seen > self.GRACE_PERIOD
            ):
                state["start_time"] = None
                state["last_seen"] = None
                state["critical_triggered"] = False

        # Calculate elapsed time for the current episode.
        if state["start_time"] is None:
            duration = 0.0
        else:
            duration = max(
                0.0,
                now - state["start_time"],
            )

        # Determine risk level.
        if duration >= self.CRITICAL_LIMIT:
            risk_level = "CRITICAL"
        elif duration >= self.NORMAL_LIMIT:
            risk_level = "MEDIUM"
        else:
            risk_level = "NORMAL"

        # Trigger only when:
        # 1. Risk is CRITICAL
        # 2. An animal is detected in the current frame
        # 3. Critical has not already triggered this episode
        trigger_critical = (
            animal_detected
            and risk_level == "CRITICAL"
            and not state["critical_triggered"]
        )

        if trigger_critical:
            state["critical_triggered"] = True

        risk_score = min(
            100,
            int(duration / self.CRITICAL_LIMIT * 100),
        )

        if state["start_time"] is None:
            reason = "No continuous animal presence"
        elif animal_detected:
            reason = (
                f"Animal presence for {duration:.1f} seconds"
            )
        else:
            reason = (
                f"Detection temporarily absent; "
                f"timer retained for grace period "
                f"({duration:.1f} seconds elapsed)"
            )

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "duration": round(duration, 2),
            "reason": reason,
            "trigger_critical": trigger_critical,
        }

    def reset(self, camera_id):
        """Reset the timer for one camera."""
        self.camera_states.pop(camera_id, None)

    def reset_all(self):
        """Reset timers for all cameras."""
        self.camera_states.clear()