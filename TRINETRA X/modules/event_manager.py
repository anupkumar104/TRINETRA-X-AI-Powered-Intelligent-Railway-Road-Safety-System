import uuid
from datetime import datetime

from database.database import get_connection
from modules.risk_engine import RiskEngine


class EventManager:

    def __init__(self):

        self.risk_engine = RiskEngine()

        self.last_event = None

    # ==================================
    # CREATE EVENT
    # ==================================

    def create_event(
        self,
        zone_id,
        mode,
        event_type,
        object_name,
        status="active",
        camera_id=None
    ):

        event_id = (
            "EVT-"
            + uuid.uuid4().hex[:8].upper()
        )

        connection = get_connection()

        connection.execute(
            """
            INSERT INTO events
            (
                event_id,
                zone_id,
                mode,
                event_type,
                object_name,
                start_time,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                zone_id,
                mode,
                event_type,
                object_name,
                datetime.now(),
                status
            )
        )

        connection.commit()
        connection.close()

        self.last_event = {

            "event_id":
                event_id,

            "zone_id":
                zone_id,

            "mode":
                mode,

            "event_type":
                event_type,

            "object_name":
                object_name,

            "status":
                status,

            "camera_id":
                camera_id,

            "created_at":
                datetime.now()
        }

        return event_id

    # ==================================
    # GET LAST EVENT
    # ==================================

    def get_last_event(self):

        return getattr(
            self,
            "last_event",
            None
        )

    # ==================================
    # ADD RISK SCORE
    # ==================================

    def add_risk_score(
        self,
        event_id,
        risk_score,
        risk_level,
        reason
    ):

        connection = get_connection()

        connection.execute(
            """
            INSERT INTO risk_scores
            (
                event_id,
                risk_score,
                risk_level,
                reason
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                event_id,
                risk_score,
                risk_level,
                reason
            )
        )

        connection.commit()
        connection.close()

    # ==================================
    # CREATE ALERT
    # ==================================

    def create_alert(
        self,
        event_id,
        risk_level,
        message,
        snapshot_path=None
    ):

        connection = get_connection()

        connection.execute(
            """
            INSERT INTO alerts
            (
                event_id,
                alert_type,
                risk_level,
                message,
                alarm_status,
                notification_status,
                snapshot_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                "SAFETY_ALERT",
                risk_level,
                message,
                "pending",
                "pending",
                snapshot_path
            )
        )

        connection.commit()
        connection.close()

    # ==================================
    # PROCESS RISK RESULT
    # ==================================

    def process_risk_result(
        self,
        zone_id,
        mode,
        risk_result,
        object_name,
        camera_id=None,
        status="active"
    ):

        # --------------------------------
        # GET RISK INFORMATION
        # --------------------------------

        risk_score = risk_result.get(
            "risk_score",
            0
        )

        risk_level = risk_result.get(
            "risk_level",
            "NORMAL"
        )

        event_type = risk_result.get(
            "event_type",
            "UNKNOWN"
        )

        reason = risk_result.get(
            "reason",
            ""
        )

        # --------------------------------
        # NORMAL = NO CRITICAL EVENT
        # --------------------------------

        if risk_level == "NORMAL":

            print(
                "[RISK ENGINE] "
                "No critical event detected."
            )

            return {

                "event_id": None,

                "risk_score":
                    risk_score,

                "risk_level":
                    risk_level,

                "event_type":
                    event_type,

                "reason":
                    reason,

                "alert_created":
                    False
            }

        # --------------------------------
        # CREATE EVENT
        # --------------------------------

        event_id = self.create_event(

            zone_id=zone_id,

            mode=mode,

            event_type=event_type,

            object_name=object_name,

            status=status,

            camera_id=camera_id
        )

        # --------------------------------
        # SAVE RISK SCORE
        # --------------------------------

        self.add_risk_score(

            event_id=event_id,

            risk_score=risk_score,

            risk_level=risk_level,

            reason=reason
        )

        # --------------------------------
        # CREATE ALERT MESSAGE
        # --------------------------------

        message = (
            f"🚨 {risk_level} SAFETY ALERT | "
            f"{event_type} | "
            f"Zone {zone_id}: "
            f"{object_name} detected. "
            f"{reason}"
        )

        # --------------------------------
        # CREATE ALERT
        # --------------------------------

        self.create_alert(

            event_id=event_id,

            risk_level=risk_level,

            message=message
        )

        print(
            "\n================================"
        )

        print(
            "       EVENT CREATED"
        )

        print(
            "================================"
        )

        print(
            f"Event ID   : {event_id}"
        )

        print(
            f"Zone       : {zone_id}"
        )

        print(
            f"Mode       : {mode}"
        )

        print(
            f"Event Type : {event_type}"
        )

        print(
            f"Risk Score : {risk_score}"
        )

        print(
            f"Risk Level : {risk_level}"
        )

        print(
            f"Object     : {object_name}"
        )

        print(
            "--------------------------------"
        )

        print(
            f"Reason     : {reason}"
        )

        print(
            "================================\n"
        )

        return {

            "event_id":
                event_id,

            "zone_id":
                zone_id,

            "mode":
                mode,

            "event_type":
                event_type,

            "object_name":
                object_name,

            "risk_score":
                risk_score,

            "risk_level":
                risk_level,

            "reason":
                reason,

            "alert_created":
                True
        }