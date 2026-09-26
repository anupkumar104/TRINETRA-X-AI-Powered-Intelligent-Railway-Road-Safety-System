from datetime import datetime


class NotificationManager:

    def __init__(self):

        self.notification_log = (
            "logs/notifications.log"
        )

        self.notification_history = []

    # ==================================
    # SEND NOTIFICATION
    # ==================================

    def send_notification(
        self,
        event_id,
        mode,
        zone_id,
        risk_level,
        message,
        recipient_id=None,
        recipient_name=None,
        recipient_type=None,
        snapshot_path=None
    ):

        # ==================================
        # CREATE NOTIFICATION
        # ==================================

        notification = {

            "event_id":
                event_id,

            "time":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

            "mode":
                mode,

            "zone_id":
                zone_id,

            "risk_level":
                risk_level,

            "recipient_id":
                recipient_id,

            "recipient_name":
                recipient_name,

            "recipient_type":
                recipient_type,

            "message":
                message,

            "snapshot":
                snapshot_path
        }

        # ==================================
        # SAVE HISTORY
        # ==================================

        self.notification_history.append(
            notification
        )

        # ==================================
        # DISPLAY MESSAGE
        # ==================================

        print("\n")
        print("====================================")
        print("📱 SAFETY NOTIFICATION")
        print("====================================")

        print(
            f"Event ID      : "
            f"{event_id}"
        )

        print(
            f"Mode          : "
            f"{mode.upper()}"
        )

        print(
            f"Zone          : "
            f"{zone_id}"
        )

        print(
            f"Risk          : "
            f"{risk_level}"
        )

        print(
            f"Recipient ID  : "
            f"{recipient_id}"
        )

        print(
            f"Recipient     : "
            f"{recipient_name}"
        )

        print(
            f"Recipient Type: "
            f"{recipient_type}"
        )

        print(
            f"Message       : "
            f"{message}"
        )

        if snapshot_path:

            print(
                f"Snapshot      : "
                f"{snapshot_path}"
            )

        print("====================================")

        # ==================================
        # SAVE LOCAL LOG
        # ==================================

        try:

            from pathlib import Path

            log_path = Path(
                self.notification_log
            )

            log_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            with open(
                log_path,
                "a",
                encoding="utf-8"
            ) as file:

                file.write(
                    str(notification)
                    + "\n"
                )

            print(
                "[NOTIFICATION LOGGED]"
            )

        except Exception as error:

            print(
                f"[NOTIFICATION LOG ERROR] "
                f"{error}"
            )

        return notification

    # ==================================
    # GET NOTIFICATION HISTORY
    # ==================================

    def get_notification_history(
        self
    ):

        return (
            self.notification_history
        )