import sqlite3
from pathlib import Path
from config import DATABASE_PATH


def get_connection():
    """Create and return a SQLite database connection."""
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Create all required database tables."""

    connection = get_connection()
    cursor = connection.cursor()

    # =========================
    # ZONES
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS zones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zone_id TEXT UNIQUE NOT NULL,
            zone_name TEXT NOT NULL,
            zone_type TEXT NOT NULL,
            danger_level TEXT DEFAULT 'MEDIUM',
            roi_json TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =========================
    # CAMERAS
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cameras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT UNIQUE NOT NULL,
            camera_name TEXT NOT NULL,
            camera_type TEXT NOT NULL,
            mode TEXT NOT NULL,
            zone_id TEXT,
            video_source TEXT,
            status TEXT DEFAULT 'offline',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(zone_id) REFERENCES zones(zone_id)
        )
    """)

    # =========================
    # DETECTIONS
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT,
            zone_id TEXT,
            object_type TEXT,
            object_name TEXT,
            confidence REAL,
            x1 REAL,
            y1 REAL,
            x2 REAL,
            y2 REAL,
            direction TEXT,
            snapshot_path TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(camera_id) REFERENCES cameras(camera_id),
            FOREIGN KEY(zone_id) REFERENCES zones(zone_id)
        )
    """)

    # =========================
    # EVENTS
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            zone_id TEXT,
            mode TEXT NOT NULL,
            event_type TEXT,
            object_name TEXT,
            start_time DATETIME,
            end_time DATETIME,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(zone_id) REFERENCES zones(zone_id)
        )
    """)

    # =========================
    # RISK SCORES
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT,
            risk_score REAL,
            risk_level TEXT,
            reason TEXT,
            calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(event_id) REFERENCES events(event_id)
        )
    """)

    # =========================
    # ALERTS
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT,
            alert_type TEXT,
            risk_level TEXT,
            message TEXT,
            alarm_status TEXT DEFAULT 'pending',
            notification_status TEXT DEFAULT 'pending',
            snapshot_path TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(event_id) REFERENCES events(event_id)
        )
    """)

    # =========================
    # TRACK ANALYSIS
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS track_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT,
            zone_id TEXT,
            track_status TEXT,
            fault_type TEXT,
            confidence REAL,
            snapshot_path TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(camera_id) REFERENCES cameras(camera_id),
            FOREIGN KEY(zone_id) REFERENCES zones(zone_id)
        )
    """)
    # =========================
    # CLIENTS
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT UNIQUE NOT NULL,
            client_type TEXT NOT NULL,
            name TEXT,
            zone_id TEXT,
            status TEXT DEFAULT 'offline',
            role TEXT,
            contact TEXT,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(zone_id) REFERENCES zones(zone_id)
        )
    """)
    # =========================
    # CAMERA CLIENT ASSIGNMENTS
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS camera_client_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT NOT NULL,
            client_id TEXT NOT NULL,
            assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(camera_id, client_id),

            FOREIGN KEY(camera_id)
                REFERENCES cameras(camera_id),

            FOREIGN KEY(client_id)
                REFERENCES clients(client_id)
        )
    """)
    # =========================
    # CLIENT ZONE HISTORY
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS client_zone_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            old_zone_id TEXT,
            new_zone_id TEXT NOT NULL,
            changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(client_id) REFERENCES clients(client_id)
        )
    """)

    # =========================
    # NOTIFICATION LOGS
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT,
            recipient_id TEXT,
            recipient_type TEXT,
            zone_id TEXT,
            message TEXT,
            notification_type TEXT,
            status TEXT DEFAULT 'pending',
            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            delivered_at DATETIME,
            FOREIGN KEY(event_id) REFERENCES events(event_id),
            FOREIGN KEY(zone_id) REFERENCES zones(zone_id)
        )
    """)
    connection.commit()
    connection.close()

    print("Database initialized successfully.")


# ============================================================
# ZONE FUNCTIONS
# ============================================================

def add_zone(zone_id, zone_name, zone_type,
             danger_level="MEDIUM",
             roi_json=None,
             description=None):

    connection = get_connection()

    connection.execute("""
        INSERT OR IGNORE INTO zones
        (zone_id, zone_name, zone_type, danger_level, roi_json, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        zone_id,
        zone_name,
        zone_type,
        danger_level,
        roi_json,
        description
    ))

    connection.commit()
    connection.close()


def get_all_zones():

    connection = get_connection()

    rows = connection.execute("""
        SELECT * FROM zones
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    return rows


# ============================================================
# CAMERA FUNCTIONS
# ============================================================

def add_camera(camera_id, camera_name, camera_type,
               mode, zone_id=None,
               video_source=None,
               status="offline"):

    connection = get_connection()

    connection.execute("""
        INSERT OR IGNORE INTO cameras
        (camera_id, camera_name, camera_type, mode,
         zone_id, video_source, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        camera_id,
        camera_name,
        camera_type,
        mode,
        zone_id,
        video_source,
        status
    ))

    connection.commit()
    connection.close()


def get_all_cameras():

    connection = get_connection()

    rows = connection.execute("""
        SELECT * FROM cameras
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    return rows


# ============================================================
# DETECTION FUNCTION
# ============================================================

def add_detection(
    camera_id,
    zone_id,
    object_type,
    object_name,
    confidence,
    x1=None,
    y1=None,
    x2=None,
    y2=None,
    direction=None,
    snapshot_path=None
):

    connection = get_connection()

    cursor = connection.execute("""
        INSERT INTO detections
        (
            camera_id,
            zone_id,
            object_type,
            object_name,
            confidence,
            x1,
            y1,
            x2,
            y2,
            direction,
            snapshot_path
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        camera_id,
        zone_id,
        object_type,
        object_name,
        confidence,
        x1,
        y1,
        x2,
        y2,
        direction,
        snapshot_path
    ))

    connection.commit()

    detection_id = cursor.lastrowid

    connection.close()

    return detection_id


# ============================================================
# TEST DATA
# ============================================================

def insert_test_data():

    # Railway zone
    add_zone(
        zone_id="Z001",
        zone_name="Forest Railway Zone",
        zone_type="railway",
        danger_level="HIGH",
        description="High-risk animal crossing railway zone"
    )

    # Road zone
    add_zone(
        zone_id="Z002",
        zone_name="Forest Highway Zone",
        zone_type="road",
        danger_level="HIGH",
        description="Animal crossing road zone"
    )

    # Railway zone camera
    add_camera(
        camera_id="CAM001",
        camera_name="Railway Zone Camera",
        camera_type="zone",
        mode="railway",
        zone_id="Z001",
        video_source="videos/railway/zone_camera.mp4"
    )

    # Train front camera
    add_camera(
        camera_id="CAM002",
        camera_name="Train Front Camera",
        camera_type="train_front",
        mode="railway",
        zone_id="Z001",
        video_source="videos/railway/train_front.mp4"
    )

    # Road zone camera
    add_camera(
        camera_id="CAM003",
        camera_name="Road Zone Camera",
        camera_type="zone",
        mode="road",
        zone_id="Z002",
        video_source="videos/road/zone_camera.mp4"
    )

    # Vehicle front camera
    add_camera(
        camera_id="CAM004",
        camera_name="Vehicle Front Camera",
        camera_type="vehicle_front",
        mode="road",
        zone_id="Z002",
        video_source="videos/road/vehicle_front.mp4"
    )

    print("Test data inserted successfully.")


# ============================================================
# DISPLAY DATA
# ============================================================

def show_test_data():

    print("\n========== ZONES ==========")

    zones = get_all_zones()

    for zone in zones:
        print(
            f"{zone['zone_id']} | "
            f"{zone['zone_name']} | "
            f"{zone['zone_type']} | "
            f"{zone['danger_level']}"
        )

    print("\n========== CAMERAS ==========")

    cameras = get_all_cameras()

    for camera in cameras:
        print(
            f"{camera['camera_id']} | "
            f"{camera['camera_name']} | "
            f"{camera['camera_type']} | "
            f"{camera['mode']} | "
            f"Zone: {camera['zone_id']}"
        )
# ============================================================
# CAMERA CLIENT ASSIGNMENT FUNCTIONS
# ============================================================

def assign_camera_to_client(camera_id, client_id):
    """
    Assign a specific camera to a specific client.

    Example:
        CAM002 -> T001
        CAM004 -> V001
    """

    connection = get_connection()

    # Check camera
    camera = connection.execute(
        """
        SELECT camera_id, zone_id
        FROM cameras
        WHERE camera_id = ?
        """,
        (camera_id,)
    ).fetchone()

    if camera is None:
        connection.close()

        print(
            f"[ASSIGNMENT FAILED] "
            f"Camera {camera_id} not found."
        )

        return False

    # Check client
    client = connection.execute(
        """
        SELECT client_id, zone_id
        FROM clients
        WHERE client_id = ?
        """,
        (client_id,)
    ).fetchone()

    if client is None:
        connection.close()

        print(
            f"[ASSIGNMENT FAILED] "
            f"Client {client_id} not found."
        )

        return False

    # Check same zone
    if camera["zone_id"] != client["zone_id"]:

        connection.close()

        print(
            f"[ASSIGNMENT FAILED] "
            f"{camera_id} and {client_id} "
            f"are in different zones."
        )

        return False

    # Insert assignment
    connection.execute(
        """
        INSERT OR IGNORE INTO camera_client_assignments
        (
            camera_id,
            client_id
        )
        VALUES (?, ?)
        """,
        (
            camera_id,
            client_id
        )
    )

    connection.commit()
    connection.close()

    print(
        f"[CAMERA ASSIGNED] "
        f"{camera_id} -> {client_id}"
    )

    return True


def remove_camera_assignment(
    camera_id,
    client_id
):
    """
    Remove a camera-client assignment.
    """

    connection = get_connection()

    cursor = connection.execute(
        """
        DELETE FROM camera_client_assignments
        WHERE camera_id = ?
        AND client_id = ?
        """,
        (
            camera_id,
            client_id
        )
    )

    connection.commit()
    deleted = cursor.rowcount > 0

    connection.close()

    if deleted:

        print(
            f"[ASSIGNMENT REMOVED] "
            f"{camera_id} -> {client_id}"
        )

    else:

        print(
            f"[REMOVE FAILED] "
            f"No assignment found for "
            f"{camera_id} -> {client_id}"
        )

    return deleted


def get_camera_clients(camera_id):
    """
    Get all clients assigned to a camera.
    """

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            c.client_id,
            c.client_type,
            c.name,
            c.zone_id,
            c.status,
            c.role,
            c.contact
        FROM clients c
        INNER JOIN camera_client_assignments a
            ON c.client_id = a.client_id
        WHERE a.camera_id = ?
        ORDER BY c.client_id
        """,
        (camera_id,)
    ).fetchall()

    connection.close()

    return [
        {
            "client_id": row["client_id"],
            "client_type": row["client_type"],
            "name": row["name"],
            "zone_id": row["zone_id"],
            "status": row["status"],
            "role": row["role"],
            "contact": row["contact"]
        }
        for row in rows
    ]


def get_camera_client(camera_id):
    """
    Get the first assigned client for a camera.

    Useful for:
        CAM002 -> T001
        CAM004 -> V001
    """

    clients = get_camera_clients(camera_id)

    if not clients:
        return None

    return clients[0]


def display_camera_assignments():
    """
    Display all camera-client assignments.
    """

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            a.camera_id,
            a.client_id,
            c.name,
            c.client_type,
            c.zone_id,
            c.status
        FROM camera_client_assignments a
        INNER JOIN clients c
            ON a.client_id = c.client_id
        ORDER BY a.camera_id
        """
    ).fetchall()

    connection.close()

    print(
        "\n========================================"
    )

    print(
        "CAMERA CLIENT ASSIGNMENTS"
    )

    print(
        "========================================"
    )

    if not rows:

        print(
            "No camera-client assignments found."
        )

        return

    for row in rows:

        print(
            f"{row['camera_id']} | "
            f"{row['client_id']} | "
            f"{row['name']} | "
            f"{row['client_type']} | "
            f"Zone {row['zone_id']} | "
            f"{row['status']}"
        )

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    init_db()

    insert_test_data()

    # ========================================
    # CAMERA → CLIENT ASSIGNMENTS
    # ========================================

    assign_camera_to_client(
        camera_id="CAM002",
        client_id="T001"
    )

    assign_camera_to_client(
        camera_id="CAM004",
        client_id="V001"
    )

    # ========================================
    # DISPLAY DATA
    # ========================================

    show_test_data()

    display_camera_assignments()