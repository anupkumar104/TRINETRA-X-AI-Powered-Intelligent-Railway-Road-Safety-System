
import os
import sys
import cv2
import time
import threading

from werkzeug.utils import secure_filename

# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.chdir(PROJECT_ROOT)

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    Response,
    send_file,
    abort,
)

from main import (
    AISafetySystem,
    CAMERAS,
    ANIMAL_CLASSES,
    ALERT_COOLDOWN,
)

# ============================================================
# FLASK CONFIGURATION
# ============================================================

UI_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(UI_DIR, "templates"),
    static_folder=os.path.join(UI_DIR, "static"),
)

UPLOAD_FOLDER = os.path.join(
    PROJECT_ROOT,
    "uploads",
    "videos",
)

ALLOWED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".webm",
}

# Maximum upload size: 500 MB
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ============================================================
# INITIALIZE TRINETRA X
# ============================================================

print("\n========================================")
print("       INITIALIZING TRINETRA X AI")
print("========================================")

system = AISafetySystem()
system.register_cameras()

print("[UI BACKEND] Ready")

# ============================================================
# GLOBAL STATE
# ============================================================

camera_lock = threading.RLock()

active_camera_id = None
active_camera_open = False

ui_alerts = []
ui_alert_lock = threading.Lock()

last_ui_alert_id = None

# Uploaded video source overrides, keyed by camera ID.
camera_source_overrides = {}

# ============================================================
# GENERAL HELPERS
# ============================================================


def get_mode(zone_id):
    return system._get_mode(zone_id)


def get_camera_source_label(camera_id, config):
    """Return a human-readable source label for the UI."""

    override = camera_source_overrides.get(camera_id)

    if override:
        return os.path.basename(override)

    source = config.get("source", 0)

    if source == 0:
        return "Laptop Camera"

    if isinstance(source, int):
        return f"Camera Device {source}"

    return "RTSP / IP CAMERA"


def release_active_camera():
    """Release the currently active camera, if any."""

    global active_camera_id, active_camera_open

    if active_camera_id is not None:
        try:
            system.camera_manager.release_camera(
                active_camera_id
            )
        except Exception as exc:
            print(f"[CAMERA RELEASE ERROR] {exc}")

    active_camera_id = None
    active_camera_open = False


def start_camera(camera_id):
    """Open a registered camera without reopening it unnecessarily."""

    global active_camera_id, active_camera_open

    with camera_lock:

        if (
            active_camera_id is not None
            and active_camera_id != camera_id
        ):
            print(
                f"[CAMERA SWITCH] "
                f"{active_camera_id} -> {camera_id}"
            )
            release_active_camera()

        if (
            active_camera_id == camera_id
            and active_camera_open
        ):
            return True

        print(f"[CAMERA] Opening {camera_id}")

        if not system.camera_manager.open_camera(camera_id):
            print(
                f"[CAMERA ERROR] Could not open {camera_id}"
            )
            return False

        active_camera_id = camera_id
        active_camera_open = True

        print(f"[CAMERA OPENED] {camera_id}")

        return True


def _recipient_type_label(value):
    value = str(value or "").strip().lower()

    return {
        "pilot": "PILOT",
        "driver": "DRIVER",
        "zone_manager": "ZONE MANAGER",
        "manager": "ZONE MANAGER",
    }.get(
        value,
        value.replace("_", " ").upper() or "RECIPIENT",
    )


def _normalize_notification(notification, result):
    notification = notification or {}

    recipients = []

    for item in notification.get("recipients", []) or []:

        recipient_type = (
            item.get("recipient_type")
            or item.get("type")
        )

        recipients.append({
            "recipient_id": (
                item.get("recipient_id")
                or item.get("client_id")
                or item.get("id")
            ),
            "name": (
                item.get("recipient")
                or item.get("name")
                or item.get("recipient_name")
            ),
            "recipient_type": recipient_type,
            "recipient_type_label": (
                _recipient_type_label(recipient_type)
            ),
            "status": (
                item.get("status")
                or item.get("delivery_status")
                or "UNKNOWN"
            ),
            "delivery_status": (
                item.get("delivery_status")
                or item.get("status")
                or "UNKNOWN"
            ),
            "message": (
                item.get("message")
                or notification.get("message")
                or ""
            ),
        })

    message = notification.get("message") or ""

    if not message:
        for recipient in recipients:
            if recipient.get("message"):
                message = recipient["message"]
                break

    routing = (
        notification.get("routing")
        or result.get("routing")
        or ""
    )

    if not routing:
        routing = (
            "INDIVIDUAL"
            if len(recipients) <= 2
            else "ZONE_BROADCAST"
        )

    return {
        "routing": str(routing).upper(),
        "recipient_count": notification.get(
            "recipient_count",
            len(recipients),
        ),
        "recipients": recipients,
        "message": message,
    }


def _get_duration(risk_result, event_result):
    """Extract duration from either result without assuming a field exists."""

    duration = risk_result.get(
        "duration",
        event_result.get("duration", 0),
    )

    try:
        return round(float(duration or 0), 2)
    except (TypeError, ValueError):
        return 0.0


# ============================================================
# ALERT MANAGEMENT
# ============================================================


def add_ui_alert(
    camera_id,
    config,
    animal_detections,
    risk_result,
    event_result,
):
    global last_ui_alert_id

    if not animal_detections or not event_result:
        return

    animal = max(
        animal_detections,
        key=lambda x: x.get("confidence", 0),
    )

    event_id = (
        event_result.get("event_id")
        or f"UI-{int(time.time() * 1000)}"
    )

    notification = _normalize_notification(
        event_result.get("notification"),
        event_result,
    )

    snapshot_path = event_result.get("snapshot_path") or ""

    snapshot_url = ""

    if snapshot_path:
        normalized_path = snapshot_path.replace("\\", "/")
        snapshot_url = (
            "/api/snapshot?path="
            + normalized_path
        )

    try:
        confidence = round(
            float(animal.get("confidence", 0)) * 100,
            1,
        )
    except (TypeError, ValueError):
        confidence = 0

    alert = {
        "event_id": event_id,
        "time": time.strftime("%H:%M:%S"),
        "camera_id": camera_id,
        "zone_id": config["zone_id"],
        "mode": get_mode(config["zone_id"]).upper(),

        "animal": animal.get("class_name", "Unknown"),
        "confidence": confidence,

        "risk": event_result.get(
            "risk_level",
            risk_result.get("risk_level", "CRITICAL"),
        ),

        "risk_score": event_result.get(
            "risk_score",
            risk_result.get("risk_score", 0),
        ),

        "duration": _get_duration(
            risk_result,
            event_result,
        ),

        "event_type": event_result.get(
            "event_type",
            risk_result.get("event_type", ""),
        ),

        "reason": event_result.get(
            "reason",
            risk_result.get("reason", ""),
        ),

        "snapshot_path": snapshot_path,
        "snapshot_url": snapshot_url,

        "routing": notification["routing"],
        "recipients": notification["recipients"],
        "recipient_count": notification["recipient_count"],
        "message": notification["message"],
    }

    with ui_alert_lock:

        if event_id == last_ui_alert_id:
            return

        last_ui_alert_id = event_id

        ui_alerts.insert(0, alert)

        # Keep the latest 30 UI alerts.
        del ui_alerts[30:]


def process_critical_event(
    frame,
    mode,
    zone_id,
    camera_id,
    animal_detections,
    risk_result,
):
    """
    Call the existing CriticalEventHandler and retain
    its actual result for the UI.
    """

    now = time.time()

    last = system.last_alert_time.get(
        camera_id,
        0,
    )

    cooldown = getattr(
        system,
        "ALERT_COOLDOWN",
        ALERT_COOLDOWN,
    )

    if now - last < cooldown:
        return None

    best = max(
        animal_detections,
        key=lambda x: x.get("confidence", 0),
    )

    system.last_alert_time[camera_id] = now

    try:
        result = system.event_handler.handle(
            frame=frame,
            mode=mode,
            zone_id=zone_id,
            camera_id=camera_id,
            animal_detection=best,
            risk_result=risk_result,
        )

        if result:
            print(
                f"[UI EVENT] "
                f"{result.get('event_id')} "
                f"captured from backend"
            )

        return result

    except Exception as exc:
        print(f"[UI EVENT ERROR] {exc}")
        return None


# ============================================================
# VIDEO FRAME GENERATOR
# ============================================================


def generate_frames(camera_id):
    global active_camera_id, active_camera_open

    config = CAMERAS[camera_id]

    zone_id = config["zone_id"]
    camera_type = config["camera_type"]

    mode = get_mode(zone_id)

    frame_count = 0
    active_targets = []

    if not start_camera(camera_id):
        return

    try:
        active_targets = system.client_registry.get_active_clients(
            zone_id=zone_id,
            client_type=(
                "train"
                if mode == "railway"
                else "vehicle"
            ),
        )
    except Exception:
        active_targets = []

    while True:

        with camera_lock:

            if (
                active_camera_id != camera_id
                or not active_camera_open
            ):
                break

            frame = system.camera_manager.read_frame(
                camera_id
            )

        if frame is None:
            print(f"[FRAME ERROR] {camera_id}")
            break

        frame_count += 1

        # Refresh active clients periodically.
        if frame_count % 30 == 0:
            try:
                active_targets = (
                    system.client_registry.get_active_clients(
                        zone_id=zone_id,
                        client_type=(
                            "train"
                            if mode == "railway"
                            else "vehicle"
                        ),
                    )
                )
            except Exception:
                active_targets = []

        # ----------------------------------------------------
        # DETECTION
        # ----------------------------------------------------

        try:
            detections = system.detector.detect(frame)
        except Exception as exc:
            print(f"[YOLO ERROR] {exc}")
            detections = []

        animal_detections = []

        for detection in detections:
            try:
                class_name = (
                    detection["class_name"]
                    .lower()
                    .strip()
                )

                if class_name in ANIMAL_CLASSES:
                    animal_detections.append(detection)

            except Exception:
                pass

        # ----------------------------------------------------
        # DEFAULT RISK
        # ----------------------------------------------------

        risk_result = {
            "risk_score": 0,
            "risk_level": "NORMAL",
            "event_type": "NO_ANIMAL",
            "reason": "No animal detected.",
            "duration": 0,
        }

        # ----------------------------------------------------
        # RISK EVALUATION
        # ----------------------------------------------------

        if animal_detections:

            if camera_type in (
                "train_front",
                "vehicle_front",
            ):

                risk_result = system._front_camera_risk(
                    mode=mode,
                    zone_id=zone_id,
                    camera_id=camera_id,
                    camera_type=camera_type,
                    animal_detections=animal_detections,
                    active_targets=active_targets,
                )

            elif camera_type == "zone":

                risk_result = system._zone_camera_risk(
                    mode=mode,
                    zone_id=zone_id,
                    camera_id=camera_id,
                    animal_detections=animal_detections,
                    active_targets=active_targets,
                )

            # ------------------------------------------------
            # CRITICAL EVENT
            # ------------------------------------------------

            if risk_result.get("risk_level") == "CRITICAL":

                event_result = process_critical_event(
                    frame=frame,
                    mode=mode,
                    zone_id=zone_id,
                    camera_id=camera_id,
                    animal_detections=animal_detections,
                    risk_result=risk_result,
                )

                if event_result:
                    add_ui_alert(
                        camera_id=camera_id,
                        config=config,
                        animal_detections=animal_detections,
                        risk_result=risk_result,
                        event_result=event_result,
                    )

        # ----------------------------------------------------
        # DRAW ANIMAL BOXES
        # ----------------------------------------------------

        display_frame = frame.copy()

        for animal in animal_detections:
            try:
                x1, y1, x2, y2 = animal["bbox"]

                confidence = float(
                    animal["confidence"]
                )

                label = (
                    f'{animal["class_name"]} '
                    f'{confidence:.2f}'
                )

                critical = (
                    risk_result.get("risk_level")
                    == "CRITICAL"
                )

                box_color = (
                    (0, 0, 255)
                    if critical
                    else (0, 180, 80)
                )

                cv2.rectangle(
                    display_frame,
                    (x1, y1),
                    (x2, y2),
                    box_color,
                    2,
                )

                cv2.putText(
                    display_frame,
                    label,
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    box_color,
                    2,
                )

            except Exception:
                pass

        # ----------------------------------------------------
        # TRANSPARENT INFORMATION PANEL
        # ----------------------------------------------------

        overlay = display_frame.copy()

        panel_height = 135

        cv2.rectangle(
            overlay,
            (0, 0),
            (
                display_frame.shape[1],
                panel_height,
            ),
            (20, 25, 35),
            -1,
        )

        display_frame = cv2.addWeighted(
            overlay,
            0.40,
            display_frame,
            0.60,
            0,
        )

        # ----------------------------------------------------
        # CAMERA INFORMATION
        # ----------------------------------------------------

        cv2.putText(
            display_frame,
            f"TRINETRA X AI | {camera_id}",
            (20, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.70,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            display_frame,
            (
                f"{mode.upper()} | {zone_id} | "
                f"ACTIVE TARGETS: {len(active_targets)}"
            ),
            (20, 62),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (230, 240, 255),
            2,
        )

        # ----------------------------------------------------
        # RISK INFORMATION
        # ----------------------------------------------------

        risk_level = risk_result.get(
            "risk_level",
            "NORMAL",
        )

        risk_score = risk_result.get(
            "risk_score",
            0,
        )

        duration = risk_result.get(
            "duration",
            0,
        )

        risk_color = (
            (0, 0, 255)
            if risk_level == "CRITICAL"
            else (0, 200, 0)
        )

        cv2.putText(
            display_frame,
            (
                f"RISK: {risk_level} | "
                f"SCORE: {risk_score} | "
                f"DURATION: {duration}s"
            ),
            (20, 95),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            risk_color,
            2,
        )

        # ----------------------------------------------------
        # CRITICAL EVENT OVERLAY
        # ----------------------------------------------------

        if risk_level == "CRITICAL":

            cv2.putText(
                display_frame,
                (
                    "CRITICAL: "
                    f"{risk_result.get('event_type', '')}"
                ),
                (20, 122),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 0, 255),
                2,
            )

        # ----------------------------------------------------
        # STREAM FRAME
        # ----------------------------------------------------

        ok, buffer = cv2.imencode(
            ".jpg",
            display_frame,
        )

        if ok:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes()
                + b"\r\n"
            )


# ============================================================
# DASHBOARD
# ============================================================


@app.get("/")
def dashboard():
    return render_template("dashboard.html")


# ============================================================
# CAMERA API
# ============================================================


@app.get("/api/cameras")
def cameras_api():

    requested_mode = (
        request.args.get("mode") or "all"
    ).strip().lower()

    result = []

    for camera_id, config in CAMERAS.items():

        mode = get_mode(
            config["zone_id"]
        ).lower()

        if (
            requested_mode in ("railway", "road")
            and mode != requested_mode
        ):
            continue

        result.append({
            "id": camera_id,
            "type": config["camera_type"],
            "zone": config["zone_id"],
            "mode": mode.upper(),
            "source": get_camera_source_label(
                camera_id,
                config,
            ),
        })

    return jsonify(result)


@app.post("/api/camera/select")
def select_camera():

    data = request.get_json(silent=True) or {}

    camera_id = data.get("camera_id")

    if camera_id not in CAMERAS:
        return jsonify({
            "ok": False,
            "message": "Unknown camera",
        }), 400

    if not start_camera(camera_id):
        return jsonify({
            "ok": False,
            "message": "Camera could not be opened",
        }), 500

    return jsonify({
        "ok": True,
        "camera_id": camera_id,
    })


@app.post("/api/camera/upload")
def upload_camera_video():

    camera_id = (
        request.form.get("camera_id") or ""
    ).strip()

    if camera_id not in CAMERAS:
        return jsonify({
            "ok": False,
            "message": "Unknown camera.",
        }), 400

    video = request.files.get("video")

    if not video or not video.filename:
        return jsonify({
            "ok": False,
            "message": "Please select a video file.",
        }), 400

    original_name = secure_filename(
        video.filename
    )

    extension = os.path.splitext(
        original_name
    )[1].lower()

    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        return jsonify({
            "ok": False,
            "message": (
                "Unsupported video format. "
                "Use MP4, AVI, MOV, MKV, or WEBM."
            ),
        }), 400

    filename = (
        f"{camera_id}_{int(time.time() * 1000)}"
        f"{extension}"
    )

    save_path = os.path.abspath(
        os.path.join(
            UPLOAD_FOLDER,
            filename,
        )
    )

    try:
        video.save(save_path)

        # ----------------------------------------------------
        # ASSIGN VIDEO TO CAMERA
        # ----------------------------------------------------

        with camera_lock:

            # Release the active camera first.
            if active_camera_id is not None:
                release_active_camera()

            updated = (
                system.camera_manager.set_camera_source(
                    camera_id,
                    save_path,
                )
            )

            # Some implementations return None on success.
            if updated is False:

                try:
                    os.remove(save_path)
                except OSError:
                    pass

                return jsonify({
                    "ok": False,
                    "message": (
                        "Camera source could not be updated."
                    ),
                }), 500

            camera_source_overrides[camera_id] = (
                save_path
            )

            # Open the camera using its new source.
            if not start_camera(camera_id):
                return jsonify({
                    "ok": False,
                    "message": (
                        "Video saved, but the camera "
                        "could not open it."
                    ),
                }), 500

        print(
            f"[VIDEO UPLOAD] {filename} assigned "
            f"to {camera_id}"
        )

        return jsonify({
            "ok": True,
            "camera_id": camera_id,
            "filename": filename,
            "message": (
                "Video uploaded and camera started."
            ),
        })

    except Exception as exc:

        print(f"[VIDEO UPLOAD ERROR] {exc}")

        return jsonify({
            "ok": False,
            "message": (
                "Video upload failed. "
                "Check the server console."
            ),
        }), 500


@app.post("/api/camera/stop")
def stop_camera():

    with camera_lock:
        release_active_camera()

    return jsonify({
        "ok": True,
    })


@app.get("/video_feed/<camera_id>")
def video_feed(camera_id):

    if camera_id not in CAMERAS:
        return "Unknown camera", 404

    return Response(
        generate_frames(camera_id),
        mimetype=(
            "multipart/x-mixed-replace; boundary=frame"
        ),
    )


# ============================================================
# STATUS API
# ============================================================


@app.get("/api/status")
def status_api():

    try:
        railway_targets = (
            system.client_registry.get_active_clients(
                "Z001",
                "train",
            )
        )
    except Exception:
        railway_targets = []

    try:
        road_targets = (
            system.client_registry.get_active_clients(
                "Z002",
                "vehicle",
            )
        )
    except Exception:
        road_targets = []

    with ui_alert_lock:
        alert_count = len(ui_alerts)

    return jsonify({
        "system": "ONLINE",
        "active_camera": active_camera_id,
        "railway_targets": len(railway_targets),
        "road_targets": len(road_targets),
        "alerts": alert_count,
        "total_cameras": len(CAMERAS),
    })


# ============================================================
# ACTIVE TARGETS API
# ============================================================


@app.get("/api/targets")
def targets_api():

    requested_mode = (
        request.args.get("mode") or "all"
    ).strip().lower()

    def clean(target):
        return {
            "client_id": target.get("client_id"),
            "name": target.get("name"),
            "client_type": target.get("client_type"),
            "status": target.get("status"),
            "zone_id": target.get("zone_id"),
        }

    railway = []
    road = []

    if requested_mode in ("all", "railway"):
        try:
            railway = (
                system.client_registry.get_active_clients(
                    "Z001",
                    "train",
                )
            )
        except Exception:
            railway = []

    if requested_mode in ("all", "road"):
        try:
            road = (
                system.client_registry.get_active_clients(
                    "Z002",
                    "vehicle",
                )
            )
        except Exception:
            road = []

    return jsonify({
        "railway": [
            clean(target)
            for target in railway
        ],
        "road": [
            clean(target)
            for target in road
        ],
    })


# ============================================================
# ALERT API
# ============================================================


@app.get("/api/alerts")
def alerts_api():

    with ui_alert_lock:
        return jsonify(list(ui_alerts))


@app.get("/api/alerts/<event_id>")
def alert_detail_api(event_id):

    with ui_alert_lock:

        for alert in ui_alerts:

            if alert["event_id"] == event_id:
                return jsonify(alert)

    return jsonify({
        "ok": False,
        "message": (
            "Event not found in current UI session"
        ),
    }), 404


@app.post("/api/alerts/clear")
def clear_alerts():

    global last_ui_alert_id

    with ui_alert_lock:
        ui_alerts.clear()
        last_ui_alert_id = None

    return jsonify({
        "ok": True,
    })


# ============================================================
# SNAPSHOT API
# ============================================================


@app.get("/api/snapshot")
def snapshot_api():

    raw = (
        request.args.get("path", "")
        .strip()
    )

    if not raw:
        abort(404)

    relative = (
        raw.replace("/", os.sep)
        .replace("\\", os.sep)
    )

    candidate = os.path.abspath(
        os.path.join(
            PROJECT_ROOT,
            relative,
        )
    )

    root = os.path.abspath(
        PROJECT_ROOT
    )

    try:
        if os.path.commonpath(
            [candidate, root]
        ) != root:
            abort(403)

    except ValueError:
        abort(403)

    if not os.path.isfile(candidate):
        abort(404)

    return send_file(candidate)


# ============================================================
# HEALTH API
# ============================================================


@app.get("/api/health")
def health_api():

    return jsonify({
        "ok": True,
        "system": "ONLINE",
        "active_camera": active_camera_id,
        "camera_open": active_camera_open,
    })


# ============================================================
# FILE TOO LARGE HANDLER
# ============================================================


@app.errorhandler(413)
def file_too_large(_error):

    return jsonify({
        "ok": False,
        "message": (
            "Video is too large. "
            "Maximum upload size is 500 MB."
        ),
    }), 413


# ============================================================
# RUN SERVER
# ============================================================


if __name__ == "__main__":

    print("\n========================================")
    print("       TRINETRA X AI - WEB UI")
    print("========================================")

    print(f"Project Root: {PROJECT_ROOT}")
    print("Open: http://127.0.0.1:5000")

    print("========================================\n")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        threaded=True,
    )