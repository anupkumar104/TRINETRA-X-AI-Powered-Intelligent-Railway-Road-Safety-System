
from modules.event_manager import EventManager
from modules.alarm_manager import AlarmManager
from modules.snapshot_manager import SnapshotManager
from modules.notification_manager import NotificationManager
from modules.broadcast_alert_manager import BroadcastAlertManager


class CriticalEventHandler:

    def __init__(self):

        self.event_manager = EventManager()

        self.alarm_manager = AlarmManager()

        self.snapshot_manager = SnapshotManager()

        self.notification_manager = NotificationManager()

        self.broadcast_alert_manager = (
            BroadcastAlertManager()
        )

    # ==================================
    # HANDLE CRITICAL EVENT
    # ==================================

    def handle(
        self,
        frame,
        mode,
        zone_id,
        camera_id,
        animal_detection,
        risk_result
    ):

        # ==================================
        # 1. ANIMAL NAME
        # ==================================

        animal_name = (
            animal_detection["class_name"]
        )

        # ==================================
        # 2. SAVE SNAPSHOT
        # ==================================

        snapshot_path = (
            self.snapshot_manager.save_snapshot(
                frame=frame,
                mode=mode,
                zone_id=zone_id,
                object_name=animal_name
            )
        )

        print(
            f"[SNAPSHOT SAVED] "
            f"{snapshot_path}"
        )

        # ==================================
        # 3. CREATE EVENT
        # ==================================

        event_id = (
            self.event_manager.create_event(

                zone_id=zone_id,

                mode=mode,

                event_type=(
                    risk_result["event_type"]
                ),

                object_name=animal_name,

                camera_id=camera_id
            )
        )

        print(
            f"[EVENT CREATED] "
            f"{event_id}"
        )

        # ==================================
        # 4. SAVE RISK SCORE
        # ==================================

        self.event_manager.add_risk_score(

            event_id=event_id,

            risk_score=(
                risk_result["risk_score"]
            ),

            risk_level=(
                risk_result["risk_level"]
            ),

            reason=(
                risk_result["reason"]
            )
        )

        print(
            "[RISK SCORE SAVED]"
        )

        # ==================================
        # 5. CREATE ALERT
        # ==================================

        self.event_manager.create_alert(

            event_id=event_id,

            risk_level=(
                risk_result["risk_level"]
            ),

            message=(
                risk_result["reason"]
            ),

            snapshot_path=snapshot_path
        )

        print(
            "[ALERT RECORD CREATED]"
        )

        # ==================================
        # 6. START ALARM
        # ==================================

        if (
            risk_result["risk_level"]
            == "CRITICAL"
        ):

            self.alarm_manager.start_alarm(
                duration=5
            )

            print(
                "[ALARM STARTED]"
            )

        # ==================================
        # 7. SEND NOTIFICATION
        # ==================================

        notification = None

        if risk_result["risk_level"] == "CRITICAL":

            # ==================================
            # RAILWAY MODE
            # ==================================

            if mode == "railway":

                # --------------------------------
                # CAM001 = Railway Zone Camera
                # BROADCAST
                # --------------------------------

                if camera_id == "CAM001":

                    print(
                        "\n[ROUTING] "
                        "CAM001 → ZONE BROADCAST"
                    )

                    notification = (
                        self.broadcast_alert_manager.broadcast(

                            zone_id=zone_id,

                            zone_type="railway",

                            detection_type="animal",

                            detection_name=animal_name,

                            risk_level=(
                                risk_result["risk_level"]
                            ),

                            status="MOVING",

                            event_id=event_id
                        )
                    )

                # --------------------------------
                # CAM002 = Train Front Camera
                # INDIVIDUAL
                # --------------------------------

                elif camera_id == "CAM002":

                    print(
                        "\n[ROUTING] "
                        "CAM002 → INDIVIDUAL"
                    )

                    # CAM002 belongs to T001
                    # M001 is Railway Zone Manager

                    recipients = []

                    # ---- Train Pilot ----

                    pilot_notification = (
                        self.notification_manager.send_notification(

                            event_id=event_id,

                            mode=mode,

                            zone_id=zone_id,

                            risk_level=(
                                risk_result["risk_level"]
                            ),

                            message=(
                                f"🚨 CRITICAL ANIMAL ALERT | "
                                f"Railway Zone {zone_id}: "
                                f"{animal_name} detected by "
                                f"Train Front Camera CAM002. "
                                f"Immediate safety action required."
                            ),

                            recipient_id="T001",

                            recipient_name="Train 001",

                            recipient_type="pilot",

                            snapshot_path=snapshot_path
                        )
                    )

                    recipients.append({
                        "recipient_id": "T001",
                        "recipient_type": "pilot",
                        "status": "SENT"
                    })

                    # ---- Zone Manager ----

                    manager_notification = (
                        self.notification_manager.send_notification(

                            event_id=event_id,

                            mode=mode,

                            zone_id=zone_id,

                            risk_level=(
                                risk_result["risk_level"]
                            ),

                            message=(
                                f"🚨 CRITICAL ANIMAL ALERT | "
                                f"Railway Zone {zone_id}: "
                                f"{animal_name} detected by "
                                f"Train Front Camera CAM002."
                            ),

                            recipient_id="M001",

                            recipient_name=(
                                "Railway Zone Manager"
                            ),

                            recipient_type="zone_manager",

                            snapshot_path=snapshot_path
                        )
                    )

                    recipients.append({
                        "recipient_id": "M001",
                        "recipient_type": "zone_manager",
                        "status": "SENT"
                    })

                    notification = {

                        "routing":
                            "INDIVIDUAL",

                        "recipient_count":
                            len(recipients),

                        "recipients":
                            recipients
                    }

                # --------------------------------
                # UNKNOWN RAILWAY CAMERA
                # --------------------------------

                else:

                    print(
                        f"[WARNING] Unknown railway "
                        f"camera: {camera_id}"
                    )

            # ==================================
            # ROAD MODE
            # ==================================

            elif mode == "road":

                # --------------------------------
                # CAM003 = Road Zone Camera
                # BROADCAST
                # --------------------------------

                if camera_id == "CAM003":

                    print(
                        "\n[ROUTING] "
                        "CAM003 → ZONE BROADCAST"
                    )

                    notification = (
                        self.broadcast_alert_manager.broadcast(

                            zone_id=zone_id,

                            zone_type="road",

                            detection_type="animal",

                            detection_name=animal_name,

                            risk_level=(
                                risk_result["risk_level"]
                            ),

                            status="MOVING",

                            event_id=event_id
                        )
                    )

                # --------------------------------
                # CAM004 = Vehicle Front Camera
                # INDIVIDUAL
                # --------------------------------

                elif camera_id == "CAM004":

                    print(
                        "\n[ROUTING] "
                        "CAM004 → INDIVIDUAL"
                    )

                    # CAM004 belongs to V001
                    # M002 is Road Zone Manager

                    recipients = []

                    # ---- Driver ----

                    driver_notification = (
                        self.notification_manager.send_notification(

                            event_id=event_id,

                            mode=mode,

                            zone_id=zone_id,

                            risk_level=(
                                risk_result["risk_level"]
                            ),

                            message=(
                                f"🚨 CRITICAL ANIMAL ALERT | "
                                f"Road Zone {zone_id}: "
                                f"{animal_name} detected by "
                                f"Vehicle Front Camera CAM004. "
                                f"Immediate safety action required."
                            ),

                            recipient_id="V001",

                            recipient_name="Vehicle 001",

                            recipient_type="driver",

                            snapshot_path=snapshot_path
                        )
                    )

                    recipients.append({
                        "recipient_id": "V001",
                        "recipient_type": "driver",
                        "status": "SENT"
                    })

                    # ---- Zone Manager ----

                    manager_notification = (
                        self.notification_manager.send_notification(

                            event_id=event_id,

                            mode=mode,

                            zone_id=zone_id,

                            risk_level=(
                                risk_result["risk_level"]
                            ),

                            message=(
                                f"🚨 CRITICAL ANIMAL ALERT | "
                                f"Road Zone {zone_id}: "
                                f"{animal_name} detected by "
                                f"Vehicle Front Camera CAM004."
                            ),

                            recipient_id="M002",

                            recipient_name=(
                                "Road Zone Manager"
                            ),

                            recipient_type="zone_manager",

                            snapshot_path=snapshot_path
                        )
                    )

                    recipients.append({
                        "recipient_id": "M002",
                        "recipient_type": "zone_manager",
                        "status": "SENT"
                    })

                    notification = {

                        "routing":
                            "INDIVIDUAL",

                        "recipient_count":
                            len(recipients),

                        "recipients":
                            recipients
                    }

                # --------------------------------
                # UNKNOWN ROAD CAMERA
                # --------------------------------

                else:

                    print(
                        f"[WARNING] Unknown road "
                        f"camera: {camera_id}"
                    )

            print(
                "[NOTIFICATION SENT]"
            )

        # ==================================
        # 8. RETURN EVENT INFORMATION
        # ==================================

        return {

            "event_id":
                event_id,

            "snapshot_path":
                snapshot_path,

            "risk_level":
                risk_result["risk_level"],

            "event_type":
                risk_result["event_type"],

            "notification":
                notification
        }

