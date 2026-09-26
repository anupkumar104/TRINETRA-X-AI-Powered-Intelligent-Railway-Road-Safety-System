from modules.alarm_manager import AlarmManager


class AlertManager:

    def __init__(self):

        self.alarm_manager = (
            AlarmManager()
        )

    def process_risk(
        self,
        risk_result,
        snapshot_path=None
    ):

        risk_level = (
            risk_result["risk_level"]
        )

        print(
            "\n========== ALERT MANAGER =========="
        )

        print(
            "Risk Level:",
            risk_level
        )

        print(
            "Reason:",
            risk_result["reason"]
        )

        if snapshot_path:

            print(
                "Snapshot:",
                snapshot_path
            )

        # =================================
        # CRITICAL ALERT
        # =================================

        if risk_level == "CRITICAL":

            print(
                "🚨 CRITICAL SAFETY ALERT"
            )

            self.alarm_manager.start_alarm(
                duration=5
            )

            return {
                "alert": True,
                "alarm": True,
                "risk_level": "CRITICAL"
            }

        # =================================
        # MEDIUM
        # =================================

        if risk_level == "MEDIUM":

            print(
                "⚠️ MEDIUM RISK"
            )

            return {
                "alert": True,
                "alarm": False,
                "risk_level": "MEDIUM"
            }

        # =================================
        # NORMAL
        # =================================

        print(
            "System status: NORMAL"
        )

        return {
            "alert": False,
            "alarm": False,
            "risk_level": "NORMAL"
        }