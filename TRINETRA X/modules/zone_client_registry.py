import sqlite3
from config import DATABASE_PATH


class ZoneClientRegistry:

    def __init__(self, db_path=DATABASE_PATH):

        self.db_path = db_path

    # ==================================
    # DATABASE CONNECTION
    # ==================================

    def _connect(self):

        return sqlite3.connect(
            self.db_path
        )

    # ==================================
    # REGISTER CLIENT
    # ==================================

    def register_client(
        self,
        client_id,
        zone_id,
        client_type,
        name=None,
        role=None,
        contact=None
    ):

        name = name if name else client_id

        connection = self._connect()
        cursor = connection.cursor()

        # Check if client already exists
        cursor.execute(
            """
            SELECT client_id
            FROM clients
            WHERE client_id = ?
            """,
            (client_id,)
        )

        existing = cursor.fetchone()

        if existing:

            cursor.execute(
                """
                UPDATE clients
                SET zone_id = ?,
                    client_type = ?,
                    name = ?,
                    role = ?,
                    contact = ?,
                    status = 'ONLINE',
                    last_seen = CURRENT_TIMESTAMP
                WHERE client_id = ?
                """,
                (
                    zone_id,
                    client_type,
                    name,
                    role,
                    contact,
                    client_id
                )
            )

        else:

            cursor.execute(
                """
                INSERT INTO clients (
                    client_id,
                    client_type,
                    name,
                    zone_id,
                    status,
                    role,
                    contact
                )
                VALUES (?, ?, ?, ?, 'ONLINE', ?, ?)
                """,
                (
                    client_id,
                    client_type,
                    name,
                    zone_id,
                    role,
                    contact
                )
            )

        connection.commit()
        connection.close()

        print(
            f"[CLIENT REGISTERED] "
            f"{client_id} → {zone_id}"
        )

    # ==================================
    # REMOVE CLIENT
    # ==================================

    def remove_client(
        self,
        client_id,
        zone_id=None
    ):

        connection = self._connect()
        cursor = connection.cursor()

        if zone_id:

            cursor.execute(
                """
                UPDATE clients
                SET status = 'OFFLINE'
                WHERE client_id = ?
                AND zone_id = ?
                """,
                (
                    client_id,
                    zone_id
                )
            )

        else:

            cursor.execute(
                """
                UPDATE clients
                SET status = 'OFFLINE'
                WHERE client_id = ?
                """,
                (client_id,)
            )

        connection.commit()
        connection.close()

        print(
            f"[CLIENT OFFLINE] "
            f"{client_id}"
        )

    # ==================================
    # UPDATE STATUS
    # ==================================

    def update_status(
            self,
            client_id,
            status,
            zone_id=None
    ):
        """
        Update client status.

        Supports both:
            update_status(client_id, status)
            update_status(client_id, status, zone_id)

        Also supports the old format:
            update_status(client_id, zone_id, status)
        """

        # ----------------------------------
        # Backward compatibility
        # Old format:
        # update_status(client_id, zone_id, status)
        # ----------------------------------

        valid_statuses = {
            "ONLINE",
            "OFFLINE",
            "ACTIVE",
            "INACTIVE"
        }

        if status not in valid_statuses:

            if zone_id in valid_statuses:
                old_zone = status
                old_status = zone_id

                status = old_status
                zone_id = old_zone

        connection = self._connect()
        cursor = connection.cursor()

        if zone_id:

            cursor.execute(
                """
                UPDATE clients
                SET status = ?,
                    last_seen = CURRENT_TIMESTAMP
                WHERE client_id = ?
                AND zone_id = ?
                """,
                (
                    status,
                    client_id,
                    zone_id
                )
            )

        else:

            cursor.execute(
                """
                UPDATE clients
                SET status = ?,
                    last_seen = CURRENT_TIMESTAMP
                WHERE client_id = ?
                """,
                (
                    status,
                    client_id
                )
            )

        updated = cursor.rowcount > 0

        connection.commit()
        connection.close()

        if updated:

            print(
                f"[STATUS UPDATED] "
                f"{client_id} → {status}"
            )

        else:

            print(
                f"[STATUS UPDATE FAILED] "
                f"{client_id}"
            )

        return updated

        connection = self._connect()
        cursor = connection.cursor()

        if zone_id:

            cursor.execute(
                """
                UPDATE clients
                SET status = ?,
                    last_seen = CURRENT_TIMESTAMP
                WHERE client_id = ?
                AND zone_id = ?
                """,
                (
                    status,
                    client_id,
                    zone_id
                )
            )

        else:

            cursor.execute(
                """
                UPDATE clients
                SET status = ?,
                    last_seen = CURRENT_TIMESTAMP
                WHERE client_id = ?
                """,
                (
                    status,
                    client_id
                )
            )

        updated = cursor.rowcount > 0

        connection.commit()
        connection.close()

        return updated

    # ==================================
    # MOVE CLIENT TO NEW ZONE
    # ==================================

    def move_client(
        self,
        client_id,
        old_zone,
        new_zone
    ):

        connection = self._connect()
        cursor = connection.cursor()

        # Check current client
        cursor.execute(
            """
            SELECT client_id
            FROM clients
            WHERE client_id = ?
            AND zone_id = ?
            """,
            (
                client_id,
                old_zone
            )
        )

        client = cursor.fetchone()

        if client is None:

            connection.close()

            print(
                f"[MOVE FAILED] "
                f"{client_id} not found in {old_zone}"
            )

            return False

        # Update current zone
        cursor.execute(
            """
            UPDATE clients
            SET zone_id = ?,
                status = 'ONLINE',
                last_seen = CURRENT_TIMESTAMP
            WHERE client_id = ?
            """,
            (
                new_zone,
                client_id
            )
        )

        # Save zone history
        cursor.execute(
            """
            INSERT INTO client_zone_history (
                client_id,
                old_zone_id,
                new_zone_id
            )
            VALUES (?, ?, ?)
            """,
            (
                client_id,
                old_zone,
                new_zone
            )
        )

        connection.commit()
        connection.close()

        print(
            f"[CLIENT MOVED] "
            f"{client_id}: "
            f"{old_zone} → {new_zone}"
        )

        return True

    # ==================================
    # GET ACTIVE CLIENTS
    # ==================================

    def get_active_clients(
        self,
        zone_id,
        client_type=None
    ):

        connection = self._connect()
        cursor = connection.cursor()

        if client_type:

            cursor.execute(
                """
                SELECT
                    client_id,
                    client_type,
                    name,
                    zone_id,
                    status,
                    role,
                    contact
                FROM clients
                WHERE zone_id = ?
                AND status = 'ONLINE'
                AND client_type = ?
                ORDER BY client_id
                """,
                (
                    zone_id,
                    client_type
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    client_id,
                    client_type,
                    name,
                    zone_id,
                    status,
                    role,
                    contact
                FROM clients
                WHERE zone_id = ?
                AND status = 'ONLINE'
                ORDER BY client_id
                """,
                (zone_id,)
            )

        rows = cursor.fetchall()

        connection.close()

        return [
            {
                "client_id": row[0],
                "client_type": row[1],
                "name": row[2],
                "zone_id": row[3],
                "status": row[4],
                "role": row[5],
                "contact": row[6]
            }
            for row in rows
        ]

    # ==================================
    # GET ALL CLIENTS
    # ==================================

    def get_all_clients(
        self,
        zone_id
    ):

        connection = self._connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                client_id,
                client_type,
                name,
                zone_id,
                status,
                role,
                contact
            FROM clients
            WHERE zone_id = ?
            ORDER BY client_id
            """,
            (zone_id,)
        )

        rows = cursor.fetchall()

        connection.close()

        return [
            {
                "client_id": row[0],
                "client_type": row[1],
                "name": row[2],
                "zone_id": row[3],
                "status": row[4],
                "role": row[5],
                "contact": row[6]
            }
            for row in rows
        ]

    # ==================================
    # GET CLIENT
    # ==================================

    def get_client(
        self,
        client_id
    ):

        connection = self._connect()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                client_id,
                client_type,
                name,
                zone_id,
                status,
                role,
                contact
            FROM clients
            WHERE client_id = ?
            """,
            (client_id,)
        )

        row = cursor.fetchone()

        connection.close()

        if row is None:

            return None

        return {
            "client_id": row[0],
            "client_type": row[1],
            "name": row[2],
            "zone_id": row[3],
            "status": row[4],
            "role": row[5],
            "contact": row[6]
        }

    # ==================================
    # DISPLAY ZONE CLIENTS
    # ==================================

    def display_zone_clients(
        self,
        zone_id
    ):

        clients = self.get_all_clients(
            zone_id
        )

        print(
            f"\n========== "
            f"{zone_id} CLIENTS =========="
        )

        if not clients:

            print(
                "No clients registered."
            )

            return

        for client in clients:

            print(
                f'{client["client_id"]} | '
                f'{client["name"]} | '
                f'{client["client_type"]} | '
                f'{client["status"]} | '
                f'{client["role"]}'
            )