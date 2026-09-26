from modules.event_manager import EventManager
from modules.alarm_manager import AlarmManager
from modules.snapshot_manager import SnapshotManager
from modules.notification_manager import NotificationManager
from modules.broadcast_alert_manager import BroadcastAlertManager
from database.database import get_camera_client


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

                # ==================================
                # CAM001 = RAILWAY ZONE CAMERA
                # ZONE BROADCAST
                # ==================================

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

                # ==================================
                # CAM002 = TRAIN FRONT CAMERA
                # INDIVIDUAL
                # ==================================

                elif camera_id == "CAM002":

                    print(
                        "\n[ROUTING] "
                        "CAM002 → INDIVIDUAL"
                    )

                    # --------------------------------
                    # T001 = TRAIN PILOT
                    # M001 = RAILWAY ZONE MANAGER
                    # --------------------------------

                    recipients = []

                    # ==================================
                    # PILOT MESSAGE
                    # ==================================

                    pilot_message = (
                        f"🚨 CRITICAL ANIMAL ALERT | "
                        f"Railway Zone {zone_id}: "
                        f"{animal_name} detected by "
                        f"Train Front Camera CAM002. "
                        f"Immediate safety action required."
                    )

                    pilot_notification = (
                        self.notification_manager.send_notification(

                            event_id=event_id,

                            mode=mode,

                            zone_id=zone_id,

                            risk_level=(
                                risk_result["risk_level"]
                            ),

                            message=pilot_message,

                            recipient_id="T001",

                            recipient_name="Train 001",

                            recipient_type="pilot",

                            snapshot_path=snapshot_path
                        )
                    )

                    # Add ACTUAL returned notification
                    recipients.append({
                        "recipient_id":
                            pilot_notification.get(
                                "recipient_id",
                                "T001"
                            ),

                        "recipient_name":
                            pilot_notification.get(
                                "recipient_name",
                                "Train 001"
                            ),

                        "recipient_type":
                            pilot_notification.get(
                                "recipient_type",
                                "pilot"
                            ),

                        "status":
                            pilot_notification.get(
                                "status",
                                "SENT"
                            ),

                        "delivery_status":
                            pilot_notification.get(
                                "delivery_status",
                                pilot_notification.get(
                                    "status",
                                    "SENT"
                                )
                            ),

                        "message":
                            pilot_notification.get(
                                "message",
                                pilot_message
                            ),

                        "snapshot":
                            pilot_notification.get(
                                "snapshot",
                                snapshot_path
                            )
                    })

                    # ==================================
                    # MANAGER MESSAGE
                    # ==================================

                    manager_message = (
                        f"🚨 CRITICAL ANIMAL ALERT | "
                        f"Railway Zone {zone_id}: "
                        f"{animal_name} detected by "
                        f"Train Front Camera CAM002."
                    )

                    manager_notification = (
                        self.notification_manager.send_notification(

                            event_id=event_id,

                            mode=mode,

                            zone_id=zone_id,

                            risk_level=(
                                risk_result["risk_level"]
                            ),

                            message=manager_message,

                            recipient_id="M001",

                            recipient_name=(
                                "Railway Zone Manager"
                            ),

                            recipient_type="zone_manager",

                            snapshot_path=snapshot_path
                        )
                    )

                    # Add ACTUAL manager notification
                    recipients.append({
                        "recipient_id":
                            manager_notification.get(
                                "recipient_id",
                                "M001"
                            ),

                        "recipient_name":
                            manager_notification.get(
                                "recipient_name",
                                "Railway Zone Manager"
                            ),

                        "recipient_type":
                            manager_notification.get(
                                "recipient_type",
                                "zone_manager"
                            ),

                        "status":
                            manager_notification.get(
                                "status",
                                "SENT"
                            ),

                        "delivery_status":
                            manager_notification.get(
                                "delivery_status",
                                manager_notification.get(
                                    "status",
                                    "SENT"
                                )
                            ),

                        "message":
                            manager_notification.get(
                                "message",
                                manager_message
                            ),

                        "snapshot":
                            manager_notification.get(
                                "snapshot",
                                snapshot_path
                            )
                    })

                    # ==================================
                    # FINAL NOTIFICATION OBJECT
                    # ==================================

                    notification = {

                        "routing":
                            "INDIVIDUAL",

                        "recipient_count":
                            len(recipients),

                        "recipients":
                            recipients,

                        # Actual backend message
                        "message":
                            pilot_notification.get(
                                "message",
                                pilot_message
                            )
                    }

                # ==================================
                # UNKNOWN RAILWAY CAMERA
                # ==================================

                else:

                    print(
                        f"[WARNING] Unknown railway "
                        f"camera: {camera_id}"
                    )

            # ==================================
            # ROAD MODE
            # ==================================

            elif mode == "road":

                # ==================================
                # CAM003 = ROAD ZONE CAMERA
                # ZONE BROADCAST
                # ==================================

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

                # ==================================
                # CAM004 = VEHICLE FRONT CAMERA
                # INDIVIDUAL
                # ==================================

                elif camera_id == "CAM004":

                    print(
                        "\n[ROUTING] "
                        "CAM004 → INDIVIDUAL"
                    )

                    # --------------------------------
                    # V001 = DRIVER
                    # M002 = ROAD ZONE MANAGER
                    # --------------------------------

                    recipients = []

                    # ==================================
                    # DRIVER MESSAGE
                    # ==================================

                    driver_message = (
                        f"🚨 CRITICAL ANIMAL ALERT | "
                        f"Road Zone {zone_id}: "
                        f"{animal_name} detected by "
                        f"Vehicle Front Camera CAM004. "
                        f"Immediate safety action required."
                    )

                    driver_notification = (
                        self.notification_manager.send_notification(

                            event_id=event_id,

                            mode=mode,

                            zone_id=zone_id,

                            risk_level=(
                                risk_result["risk_level"]
                            ),

                            message=driver_message,

                            recipient_id="V001",

                            recipient_name="Vehicle 001",

                            recipient_type="driver",

                            snapshot_path=snapshot_path
                        )
                    )

                    # Add ACTUAL driver notification
                    recipients.append({
                        "recipient_id":
                            driver_notification.get(
                                "recipient_id",
                                "V001"
                            ),

                        "recipient_name":
                            driver_notification.get(
                                "recipient_name",
                                "Vehicle 001"
                            ),

                        "recipient_type":
                            driver_notification.get(
                                "recipient_type",
                                "driver"
                            ),

                        "status":
                            driver_notification.get(
                                "status",
                                "SENT"
                            ),

                        "delivery_status":
                            driver_notification.get(
                                "delivery_status",
                                driver_notification.get(
                                    "status",
                                    "SENT"
                                )
                            ),

                        "message":
                            driver_notification.get(
                                "message",
                                driver_message
                            ),

                        "snapshot":
                            driver_notification.get(
                                "snapshot",
                                snapshot_path
                            )
                    })

                    # ==================================
                    # MANAGER MESSAGE
                    # ==================================

                    manager_message = (
                        f"🚨 CRITICAL ANIMAL ALERT | "
                        f"Road Zone {zone_id}: "
                        f"{animal_name} detected by "
                        f"Vehicle Front Camera CAM004."
                    )

                    manager_notification = (
                        self.notification_manager.send_notification(

                            event_id=event_id,

                            mode=mode,

                            zone_id=zone_id,

                            risk_level=(
                                risk_result["risk_level"]
                            ),

                            message=manager_message,

                            recipient_id="M002",

                            recipient_name=(
                                "Road Zone Manager"
                            ),

                            recipient_type="zone_manager",

                            snapshot_path=snapshot_path
                        )
                    )

                    # Add ACTUAL manager notification
                    recipients.append({
                        "recipient_id":
                            manager_notification.get(
                                "recipient_id",
                                "M002"
                            ),

                        "recipient_name":
                            manager_notification.get(
                                "recipient_name",
                                "Road Zone Manager"
                            ),

                        "recipient_type":
                            manager_notification.get(
                                "recipient_type",
                                "zone_manager"
                            ),

                        "status":
                            manager_notification.get(
                                "status",
                                "SENT"
                            ),

                        "delivery_status":
                            manager_notification.get(
                                "delivery_status",
                                manager_notification.get(
                                    "status",
                                    "SENT"
                                )
                            ),

                        "message":
                            manager_notification.get(
                                "message",
                                manager_message
                            ),

                        "snapshot":
                            manager_notification.get(
                                "snapshot",
                                snapshot_path
                            )
                    })

                    # ==================================
                    # FINAL NOTIFICATION OBJECT
                    # ==================================

                    notification = {

                        "routing":
                            "INDIVIDUAL",

                        "recipient_count":
                            len(recipients),

                        "recipients":
                            recipients,

                        # Actual backend message
                        "message":
                            driver_notification.get(
                                "message",
                                driver_message
                            )
                    }

                # ==================================
                # UNKNOWN ROAD CAMERA
                # ==================================

                else:

                    print(
                        f"[WARNING] Unknown road "
                        f"camera: {camera_id}"
                    )

            print(
                "[NOTIFICATION SENT]"
            )

        # ==================================
        # 8. GET TOP LEVEL MESSAGE
        # ==================================

        top_message = ""

        if notification:

            top_message = (
                notification.get(
                    "message",
                    ""
                )
                if isinstance(notification, dict)
                else ""
            )

            # If broadcast manager has no top-level
            # message, try first recipient.
            if not top_message:

                for recipient in (
                    notification.get(
                        "recipients",
                        []
                    )
                    if isinstance(notification, dict)
                    else []
                ):

                    if recipient.get("message"):

                        top_message = (
                            recipient["message"]
                        )

                        break

        # ==================================
        # 9. RETURN COMPLETE EVENT INFORMATION
        # ==================================

        return {

            "event_id":
                event_id,

            "snapshot_path":
                snapshot_path,

            "risk_level":
                risk_result["risk_level"],

            "risk_score":
                risk_result.get(
                    "risk_score",
                    0
                ),

            "event_type":
                risk_result["event_type"],

            "reason":
                risk_result.get(
                    "reason",
                    ""
                ),

            # Actual generated message
            "message":
                top_message,

            # Complete notification data
            "notification":
                notification
        }