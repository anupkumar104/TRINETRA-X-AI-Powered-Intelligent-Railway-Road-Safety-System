
from modules.zone_client_registry import ZoneClientRegistry

import sqlite3
from config import DATABASE_PATH
from datetime import datetime


class BroadcastAlertManager:

    def __init__(self, registry=None):

        self.registry = (
            registry
            if registry
            else ZoneClientRegistry()
        )

        self.alert_history = []

    # ==================================
    # DATABASE CONNECTION
    # ==================================

    def _connect(self):

        return sqlite3.connect(
            DATABASE_PATH
        )

    # ==================================
    # GET ZONE MANAGER
    # ==================================

    def get_zone_manager(
        self,
        zone_id
    ):

        # Manager is identified using
        # client_type = "zone_manager"
        # instead of database role column.

        clients = (
            self.registry.get_all_clients(
                zone_id
            )
        )

        managers = []

        for client in clients:

            if (
                client["client_type"]
                == "zone_manager"
                and
                client["status"]
                == "ONLINE"
            ):

                managers.append(
                    {
                        "client_id":
                            client["client_id"],

                        "name":
                            client["name"],

                        "role":
                            "manager",

                        "contact":
                            client.get(
                                "contact"
                            ),

                        "status":
                            client["status"]
                    }
                )

        return managers

    # ==================================
    # CREATE MESSAGE
    # ==================================

    def create_message(
        self,
        zone_id,
        zone_type,
        detection_type,
        detection_name,
        risk_level,
        status
    ):

        # --------------------------------
        # ANIMAL
        # --------------------------------

        if detection_type == "animal":

            if zone_type == "railway":

                if status == "MOVING":

                    return (
                        f"🚨 CRITICAL ANIMAL ALERT | "
                        f"Railway Zone {zone_id}: "
                        f"{detection_name} detected "
                        f"while train movement is ACTIVE. "
                        f"Follow railway safety procedure."
                    )

                return (
                    f"⚠️ ANIMAL ALERT | "
                    f"Railway Zone {zone_id}: "
                    f"{detection_name} detected."
                )

            if zone_type == "road":

                if status == "MOVING":

                    return (
                        f"🚨 CRITICAL ANIMAL ALERT | "
                        f"Road Zone {zone_id}: "
                        f"{detection_name} detected "
                        f"while vehicle movement is ACTIVE."
                    )

                return (
                    f"⚠️ ANIMAL ALERT | "
                    f"Road Zone {zone_id}: "
                    f"{detection_name} detected."
                )

        # --------------------------------
        # TRACK DEFECT
        # --------------------------------

        if detection_type == "track_defect":

            return (
                f"🚨 TRACK DEFECT ALERT | "
                f"Railway Zone {zone_id}: "
                f"{detection_name} detected. "
                f"Immediate attention required."
            )

        # --------------------------------
        # TRACK ZIGZAG
        # --------------------------------

        if detection_type == "track_zigzag":

            return (
                f"🚨 TRACK ALIGNMENT ALERT | "
                f"Railway Zone {zone_id}: "
                f"Abnormal / zig-zag track condition "
                f"detected."
            )

        # --------------------------------
        # POTHOLE
        # --------------------------------

        if detection_type == "pothole":

            return (
                f"🚨 ROAD HAZARD ALERT | "
                f"Road Zone {zone_id}: "
                f"Large pothole detected. "
                f"Driver safety action required."
            )

        # --------------------------------
        # ROAD DAMAGE
        # --------------------------------

        if detection_type == "road_damage":

            return (
                f"🚨 ROAD DAMAGE ALERT | "
                f"Road Zone {zone_id}: "
                f"{detection_name} detected."
            )

        # --------------------------------
        # DEFAULT
        # --------------------------------

        return (
            f"⚠️ SAFETY ALERT | "
            f"{detection_name} detected in "
            f"Zone {zone_id}."
        )

    # ==================================
    # SAVE NOTIFICATION LOG
    # ==================================

    def save_notification_log(
        self,
        event_id,
        recipient_id,
        recipient_type,
        zone_id,
        message,
        notification_type,
        status="SENT"
    ):

        connection = self._connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO notification_logs (
                event_id,
                recipient_id,
                recipient_type,
                zone_id,
                message,
                notification_type,
                status,
                sent_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                recipient_id,
                recipient_type,
                zone_id,
                message,
                notification_type,
                status,
                datetime.now()
            )
        )

        connection.commit()
        connection.close()

    # ==================================
    # SEND INDIVIDUAL FRONT CAMERA ALERT
    # ==================================

    def send_individual_alert(
        self,
        zone_id,
        zone_type,
        client_id,
        detection_type="animal",
        detection_name=None,
        risk_level="HIGH",
        status="MOVING",
        event_id=None
    ):

        # --------------------------------
        # DEFAULT DETECTION NAME
        # --------------------------------

        if detection_name is None:

            detection_name = "Animal"

        # --------------------------------
        # FIND CLIENT
        # --------------------------------

        client = None

        clients = (
            self.registry.get_all_clients(
                zone_id
            )
        )

        for item in clients:

            if item["client_id"] == client_id:

                client = item

                break

        if client is None:

            print(
                f"[ERROR] Client "
                f"{client_id} not found "
                f"in zone {zone_id}"
            )

            return None

        # --------------------------------
        # CHECK ONLINE STATUS
        # --------------------------------

        if client["status"] != "ONLINE":

            print(
                f"[ALERT BLOCKED] "
                f"{client_id} is OFFLINE"
            )

            return None

        # --------------------------------
        # CREATE MESSAGE
        # --------------------------------

        message = self.create_message(

            zone_id=zone_id,

            zone_type=zone_type,

            detection_type=detection_type,

            detection_name=detection_name,

            risk_level=risk_level,

            status=status
        )

        # --------------------------------
        # RECIPIENT TYPE
        # --------------------------------

        if client["client_type"] == "train":

            recipient_type = "pilot"

        elif client["client_type"] == "vehicle":

            recipient_type = "driver"

        else:

            recipient_type = (
                client["client_type"]
            )

        # --------------------------------
        # FIND ZONE MANAGER
        # --------------------------------

        manager = None

        for item in clients:

            if (
                item["client_type"]
                == "zone_manager"
                and
                item["status"]
                == "ONLINE"
            ):

                manager = item

                break

        # --------------------------------
        # CREATE PRIMARY RECIPIENT
        # --------------------------------

        recipient = {

            "recipient_id":
                client["client_id"],

            "recipient_name":
                client["name"],

            "recipient_type":
                recipient_type,

            "status":
                "SENT"
        }

        # --------------------------------
        # CREATE RECIPIENT LIST
        # --------------------------------

        recipients = [
            recipient
        ]

        # --------------------------------
        # ADD ZONE MANAGER
        # --------------------------------

        if manager is not None:

            manager_recipient = {

                "recipient_id":
                    manager["client_id"],

                "recipient_name":
                    manager["name"],

                "recipient_type":
                    "zone_manager",

                "status":
                    "SENT"
            }

            recipients.append(
                manager_recipient
            )

        # --------------------------------
        # DISPLAY ALERT
        # --------------------------------

        print(
            "\n================================"
        )

        print(
            "     INDIVIDUAL FRONT ALERT"
        )

        print(
            "================================"
        )

        print(
            f"Zone          : {zone_id}"
        )

        print(
            f"Detection     : "
            f"{detection_name}"
        )

        print(
            f"Detection Type: "
            f"{detection_type}"
        )

        print(
            f"Risk          : {risk_level}"
        )

        print(
            f"Status        : {status}"
        )

        print(
            "--------------------------------"
        )

        print(
            f"🚨 SENT → "
            f"{client['client_id']} "
            f"({client['name']})"
        )

        print(
            f"   Recipient: "
            f"{recipient_type}"
        )

        print(
            f"   Message: "
            f"{message}"
        )

        # --------------------------------
        # DISPLAY MANAGER ALERT
        # --------------------------------

        if manager is not None:

            print(
                f"👨‍💼 SENT → "
                f"{manager['client_id']} "
                f"({manager['name']})"
            )

            print(
                "   Recipient: zone_manager"
            )

            print(
                f"   Message: {message}"
            )

        # --------------------------------
        # SAVE NOTIFICATION LOG
        # --------------------------------

        for item in recipients:

            self.save_notification_log(

                event_id=event_id,

                recipient_id=
                    item["recipient_id"],

                recipient_type=
                    item["recipient_type"],

                zone_id=zone_id,

                message=message,

                notification_type=
                    "FRONT_CAMERA",

                status="SENT"
            )

        # --------------------------------
        # CREATE EVENT
        # --------------------------------

        event = {

            "event_id":
                event_id,

            "zone_id":
                zone_id,

            "zone_type":
                zone_type,

            "detection_type":
                detection_type,

            "detection":
                detection_name,

            "risk_level":
                risk_level,

            "status":
                status,

            "routing":
                "INDIVIDUAL",

            "recipient_count":
                len(recipients),

            "recipients":
                recipients,

            "message":
                message
        }

        # --------------------------------
        # SAVE HISTORY
        # --------------------------------

        self.alert_history.append(
            event
        )

        print(
            "--------------------------------"
        )

        print(
            f"Total Recipients: "
            f"{len(recipients)}"
        )

        print(
            "Routing         : INDIVIDUAL"
        )

        print(
            "================================\n"
        )

        return event

    # ==================================
    # BROADCAST ZONE ALERT
    # ==================================

    def broadcast(
        self,
        zone_id,
        zone_type,
        detection_type="animal",
        detection_name=None,
        risk_level="HIGH",
        status="MOVING",
        event_id=None,
        animal_name=None
    ):

        # --------------------------------
        # BACKWARD COMPATIBILITY
        # --------------------------------

        if detection_name is None:

            detection_name = (
                animal_name
                if animal_name
                else "Animal"
            )

        # --------------------------------
        # GET ACTIVE CLIENTS
        # --------------------------------

        if zone_type == "railway":

            clients = (
                self.registry
                .get_active_clients(
                    zone_id,
                    "train"
                )
            )

        elif zone_type == "road":

            clients = (
                self.registry
                .get_active_clients(
                    zone_id,
                    "vehicle"
                )
            )

        else:

            clients = []

        # --------------------------------
        # GET ONLINE ZONE MANAGERS
        # --------------------------------

        managers = self.get_zone_manager(
            zone_id
        )

        # --------------------------------
        # CREATE MESSAGE
        # --------------------------------

        message = self.create_message(

            zone_id=zone_id,

            zone_type=zone_type,

            detection_type=detection_type,

            detection_name=detection_name,

            risk_level=risk_level,

            status=status
        )

        # --------------------------------
        # PRINT ALERT HEADER
        # --------------------------------

        print(
            "\n================================"
        )

        print(
            "       ZONE BROADCAST ALERT"
        )

        print(
            "================================"
        )

        print(
            f"Zone          : {zone_id}"
        )

        print(
            f"Zone Type     : {zone_type}"
        )

        print(
            f"Detection     : {detection_name}"
        )

        print(
            f"Detection Type: {detection_type}"
        )

        print(
            f"Risk          : {risk_level}"
        )

        print(
            f"Status        : {status}"
        )

        print(
            "--------------------------------"
        )

        recipients = []

        # --------------------------------
        # SEND TO ACTIVE CLIENTS
        # --------------------------------

        for client in clients:

            recipient_type = (

                "pilot"

                if client["client_type"]
                == "train"

                else "driver"
            )

            print(
                f"🚨 SENT → "
                f"{client['client_id']} "
                f"({client['name']})"
            )

            print(
                f"   Recipient: "
                f"{recipient_type}"
            )

            print(
                f"   Message: "
                f"{message}"
            )

            recipients.append(
                {
                    "recipient_id":
                        client["client_id"],

                    "recipient_name":
                        client["name"],

                    "recipient_type":
                        recipient_type,

                    "status":
                        "SENT"
                }
            )

            self.save_notification_log(

                event_id=event_id,

                recipient_id=
                    client["client_id"],

                recipient_type=
                    recipient_type,

                zone_id=zone_id,

                message=message,

                notification_type=
                    "ZONE_BROADCAST",

                status="SENT"
            )

        # --------------------------------
        # SEND TO ZONE MANAGER
        # --------------------------------

        for manager in managers:

            print(
                f"👨‍💼 SENT → "
                f"{manager['client_id']} "
                f"({manager['name']})"
            )

            print(
                "   Recipient: zone_manager"
            )

            print(
                f"   Message: {message}"
            )

            recipients.append(
                {
                    "recipient_id":
                        manager["client_id"],

                    "recipient_name":
                        manager["name"],

                    "recipient_type":
                        "zone_manager",

                    "status":
                        "SENT"
                }
            )

            self.save_notification_log(

                event_id=event_id,

                recipient_id=
                    manager["client_id"],

                recipient_type=
                    "zone_manager",

                zone_id=zone_id,

                message=message,

                notification_type=
                    "ZONE_BROADCAST",

                status="SENT"
            )

        # --------------------------------
        # SAVE HISTORY
        # --------------------------------

        event = {

            "event_id":
                event_id,

            "zone_id":
                zone_id,

            "zone_type":
                zone_type,

            "detection_type":
                detection_type,

            "detection":
                detection_name,

            "risk_level":
                risk_level,

            "status":
                status,

            "routing":
                "ZONE_BROADCAST",

            "recipient_count":
                len(recipients),

            "recipients":
                recipients,

            "message":
                message
        }

        self.alert_history.append(
            event
        )

        print(
            "--------------------------------"
        )

        print(
            f"Total Recipients: "
            f"{len(recipients)}"
        )

        print(
            "Routing         : ZONE_BROADCAST"
        )

        print(
            "================================\n"
        )

        return event

