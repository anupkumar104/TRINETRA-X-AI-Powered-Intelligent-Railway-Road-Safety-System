# 🚆 TRINETRA X — AI-Powered Intelligent Railway & Road Safety System

> **See. Understand. Protect.**

TRINETRA X is an **AI-powered railway and road safety monitoring system** designed to detect potential hazards using computer vision, provide risk-based alerts, and intelligently route notifications to the appropriate personnel.

The system combines **YOLO-based object detection, camera monitoring, risk assessment, event management, zone-based broadcasting, and real-time alert routing** into a unified safety platform.

> ⚠️ **Project Status:** TRINETRA X is currently a software-based prototype/demo. It is intended for research, academic demonstration, and proof-of-concept purposes and is **not certified for real-world railway or road safety operations**.

---

## 🎯 Key Objectives

TRINETRA X aims to:

* Detect visible hazards using AI-powered computer vision.
* Monitor railway and highway zones through multiple cameras.
* Detect animals and other visible obstacles from front-facing cameras.
* Broadcast zone-level warnings to active vehicles/trains.
* Send front-camera alerts to the relevant driver/pilot.
* Assign risk levels based on detection persistence.
* Maintain event history and evidence snapshots.
* Provide a centralized monitoring dashboard.
* Support live camera input as well as prerecorded video.
* Improve visibility in low-light conditions through image enhancement.

---

# 🧠 System Overview

```text
                    ┌──────────────────────────┐
                    │       Camera Input       │
                    │  Webcam / Video / Stream │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │    Frame Processing      │
                    │  Low-Light Enhancement   │
                    │   Image Preprocessing    │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │     YOLO Detection       │
                    │ Animals / Vehicles /     │
                    │ Visible Obstacles        │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │   Risk Assessment Engine │
                    │ Duration + Confidence +  │
                    │     Detection Context    │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │    Event Management      │
                    │ Snapshot + Event ID +    │
                    │     Risk Information     │
                    └────────────┬─────────────┘
                                 │
                  ┌──────────────┴──────────────┐
                  ▼                             ▼
       ┌────────────────────┐        ┌────────────────────┐
       │ Zone Broadcast     │        │ Individual Alert   │
       │ Active Trains /    │        │ Pilot / Driver +   │
       │ Vehicles + Manager │        │ Zone Manager       │
       └────────────────────┘        └────────────────────┘
```

---

# 🚦 Supported Safety Zones

TRINETRA X currently models two monitored zones.

## 🚆 Z001 — Forest Railway Zone

**Zone Type:** Railway
**Risk Level:** HIGH

| Camera | Type               | Purpose                                    |
| ------ | ------------------ | ------------------------------------------ |
| CAM001 | Zone Camera        | Detect hazards across the railway zone     |
| CAM002 | Train Front Camera | Detect hazards directly ahead of the train |

### Railway Alert Flow

**Zone Camera**

```text
CAM001
   ↓
Hazard Detection
   ↓
Risk Assessment
   ↓
Zone Broadcast
   ↓
Active Trains + Zone Manager
```

**Train Front Camera**

```text
CAM002
   ↓
Visible Obstacle Detection
   ↓
Risk Assessment
   ↓
Individual Alert
   ↓
Assigned Pilot + Zone Manager
```

---

# 🛣️ Z002 — Forest Highway Zone

**Zone Type:** Road
**Risk Level:** HIGH

| Camera | Type                 | Purpose                                      |
| ------ | -------------------- | -------------------------------------------- |
| CAM003 | Zone Camera          | Detect hazards across the highway zone       |
| CAM004 | Vehicle Front Camera | Detect hazards directly ahead of the vehicle |

### Road Alert Flow

**Zone Camera**

```text
CAM003
   ↓
Hazard Detection
   ↓
Risk Assessment
   ↓
Zone Broadcast
   ↓
Active Vehicles + Zone Manager
```

**Vehicle Front Camera**

```text
CAM004
   ↓
Hazard Detection
   ↓
Risk Assessment
   ↓
Individual Alert
   ↓
Assigned Driver + Zone Manager
```

---

# 🤖 AI-Based Detection

TRINETRA X uses computer vision and object detection to identify visible objects in camera frames.

The system can be extended to support categories such as:

### Railway / Train Front

* 🐘 Animals
* 🚗 Vehicles
* 🌳 Fallen trees
* 🪨 Large rocks
* 🧱 Debris
* 🚧 Other visible obstructions

### Road / Vehicle Front

* Animals
* Vehicles
* Potholes
* Other visible road hazards

The exact detection classes depend on the trained model and available dataset.

---

# 🚆 Train Front Visible Obstacle Detection

One of the planned safety capabilities of TRINETRA X is detecting **visible obstacles in front of a moving train**.

The system follows this conceptual pipeline:

```text
Train Front Camera
        ↓
Frame Capture
        ↓
Image Preprocessing
        ↓
YOLO Object Detection
        ↓
Object Tracking
        ↓
Track / Danger Region Analysis
        ↓
Risk Assessment
        ↓
Pilot Alert
```

### Example

If an animal is detected repeatedly in the visible track region:

```text
Animal Detected
       ↓
Object Persists
       ↓
Track Region Check
       ↓
Risk Evaluation
       ↓
CRITICAL EVENT
       ↓
Pilot + Zone Manager Alert
```

### Important Limitation

Detecting an object in a camera frame does **not automatically prove that the object is on the railway track or that a collision will occur**.

A production-grade system would require additional validation such as:

* Camera calibration
* Accurate track-region estimation
* Object tracking
* Distance estimation
* Relative motion analysis
* Train speed information
* Robust testing under different weather and lighting conditions
* Safety validation and certification

Therefore, TRINETRA X treats this functionality as a **computer-vision prototype**, not as an autonomous train-control system.

---

# ⚠️ Risk Assessment

TRINETRA X uses detection persistence to determine the severity of an event.

The prototype uses the following conceptual thresholds:

| Detection Duration        | Risk Level |
| ------------------------- | ---------- |
| Short / initial detection | NORMAL     |
| Persistent detection      | MEDIUM     |
| ≥ 5 seconds               | CRITICAL   |

A **1-second grace period** is used to help handle temporary detection gaps.

### Example

```text
0–2 sec
   ↓
NORMAL

2–5 sec
   ↓
MEDIUM

≥5 sec
   ↓
CRITICAL
```

This approach helps reduce unnecessary alerts caused by brief or unstable detections.

---

# 📢 Intelligent Alert Routing

TRINETRA X does not simply generate one generic alert.

It determines **who should receive the alert based on the camera source and zone**.

## Zone Camera

A hazard detected by a zone camera can be broadcast to:

```text
Zone Camera
     ↓
Zone Manager
     +
All Active Trains / Vehicles
```

## Front Camera

A hazard detected by a front-facing camera can be routed to:

```text
Front Camera
     ↓
Assigned Pilot / Driver
     +
Zone Manager
```

This distinction prevents unnecessary alerts to unrelated users.

---

# 🆔 Event Management

Every critical event receives a unique **Event ID**.

An event can contain:

* Event ID
* Camera ID
* Zone ID
* Detection type
* Risk level
* Risk score
* Detection duration
* Detection source
* Event timestamp
* Notification recipients
* Alert message
* Evidence snapshot

Example:

```text
Event ID: EVT-00021

Zone: Z001
Camera: CAM002
Source: Train Front Camera

Detection: Animal
Risk: CRITICAL
Duration: 5.4 sec

Recipients:
✓ T001 — Pilot
✓ M001 — Zone Manager
```

---

# 📸 Evidence Capture

When a critical event occurs, TRINETRA X can capture an evidence frame.

The evidence can be associated with the corresponding Event ID and displayed in the dashboard.

This allows the operator to understand:

* What was detected
* Where it was detected
* Which camera detected it
* When it happened
* Why the alert was generated

---

# 🌙 Low-Light Detection

TRINETRA X includes a low-light processing pipeline to improve visibility during dark or poorly illuminated conditions.

```text
Camera Frame
      ↓
Brightness Analysis
      ↓
Low-Light Detection
      ↓
CLAHE Enhancement
      ↓
YOLO Detection
```

The system can determine whether a frame is sufficiently dark and apply image enhancement before running object detection.

### Important

Low-light enhancement improves image visibility but **does not guarantee better AI detection accuracy** in every environment.

---

# 🎥 Camera Input

TRINETRA X is designed to support:

* Laptop webcam
* Configured camera sources
* Prerecorded video files
* Other compatible OpenCV video sources

This makes the system suitable for demonstrations without requiring dedicated railway or road cameras.

---

# 🖥️ Web Dashboard

The TRINETRA X dashboard provides a centralized interface for monitoring the system.

### Dashboard Features

* Camera selection
* Live video feed
* Video-file testing
* Detection visualization
* Risk status
* Alert notifications
* Event history
* Evidence snapshots
* Active train/vehicle information
* Zone information
* Alert recipients
* Event-specific notification cards

Example dashboard flow:

```text
┌─────────────────────────────────────────────┐
│              TRINETRA X                     │
├─────────────────────────────────────────────┤
│                                             │
│  LIVE CAMERA FEED                           │
│  ┌───────────────────────────────────────┐  │
│  │                                       │  │
│  │        AI DETECTION VIEW              │  │
│  │                                       │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  Risk: CRITICAL                             │
│  Camera: CAM002                             │
│  Zone: Z001                                 │
│                                             │
├─────────────────────────────────────────────┤
│ Event History                               │
│                                             │
│ EVT-00021                                   │
│ Animal detected                             │
│ Recipients: T001 Pilot, M001 Manager        │
│ Duration: 5.4 sec                           │
│                                             │
└─────────────────────────────────────────────┘
```

---

# 🏗️ Project Architecture

```text
TRINETRA X
│
├── main.py
│
├── modules/
│   ├── camera_manager.py
│   ├── risk_engine.py
│   ├── event_handler.py
│   ├── low_light_enhancer.py
│   └── ...
│
├── ui/
│   ├── app.py
│   ├── templates/
│   │   └── dashboard.html
│   └── static/
│       ├── dashboard.js
│       └── dashboard.css
│
├── models/
│   └── *.pt
│
├── uploads/
│   └── videos/
│
├── snapshots/
│
├── requirements.txt
│
└── README.md
```

> The exact directory structure may change as development continues.

---

# 🛠️ Technology Stack

### Programming

* Python
* JavaScript
* HTML
* CSS

### AI / Computer Vision

* YOLO
* OpenCV
* NumPy
* Computer Vision
* Object Detection
* Object Tracking
* Image Enhancement

### Backend

* Flask
* REST APIs

### Frontend

* HTML5
* CSS3
* JavaScript
* Dashboard-based monitoring UI

### Development

* Python 3.10
* PyCharm
* Git
* GitHub

---

# 💻 Installation

## 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/TRINETRA-X.git
cd TRINETRA-X
```

## 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
```

Activate it:

```bash
.venv\Scripts\activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Run the application

Depending on the project entry point:

```bash
python main.py
```

or:

```bash
python ui/app.py
```

Open the local dashboard in your browser.

---

# 🎬 Demo Workflow

A typical demonstration can be performed using a prerecorded video.

### Railway Example

```text
Select CAM002
      ↓
Select Video File
      ↓
Upload / Load Video
      ↓
Start Processing
      ↓
YOLO Detection
      ↓
Object Tracking
      ↓
Risk Assessment
      ↓
Critical Event
      ↓
Pilot + Manager Notification
```

### Zone Broadcast Example

```text
Select CAM001
      ↓
Animal Detected
      ↓
Risk becomes CRITICAL
      ↓
Zone Broadcast
      ↓
Active Trains receive alert
      +
Zone Manager receives alert
```

---

# 👥 Test Entities

The prototype can simulate multiple trains, vehicles and managers.

### Railway Zone — Z001

```text
T001 — ONLINE
T002 — OFFLINE
T003 — ONLINE
M001 — Zone Manager
```

### Highway Zone — Z002

```text
V001 — ONLINE
V002 — OFFLINE
V003 — ONLINE
M002 — Zone Manager
```

This allows the zone-broadcast logic to be tested using realistic active/inactive clients.

---

# 🔔 Alert Routing Examples

### Example 1 — Railway Zone Camera

```text
Detection:
Elephant

Camera:
CAM001

Zone:
Z001

Risk:
CRITICAL

Recipients:
T001 — Pilot
T003 — Pilot
M001 — Zone Manager
```

T002 is excluded because it is offline.

---

### Example 2 — Train Front Camera

```text
Detection:
Cow

Camera:
CAM002

Zone:
Z001

Risk:
CRITICAL

Recipients:
T001 — Pilot
M001 — Zone Manager
```

The alert is **not broadcast to unrelated trains** because the detection originated from a specific train's front camera.

---

# 🔐 Safety & Limitations

TRINETRA X is an **academic/research prototype**.

It should not be used as a replacement for certified railway signalling, train protection, driver-assistance, or road safety systems.

The prototype has limitations including:

* Camera-dependent detection
* Lighting and weather sensitivity
* Motion blur at high speeds
* Occlusion
* False positives
* False negatives
* Limited training datasets
* Approximate distance estimation
* No certified railway hardware integration
* No direct braking/control capability
* No guarantee of collision prediction

### Particularly for railway applications

A camera-based prototype cannot independently establish that a detected object will collide with a train. Production deployment would require extensive validation, calibrated sensing, safety engineering, redundancy and regulatory certification.

---

# 🚀 Future Scope

TRINETRA X can be extended with:

### AI & Computer Vision

* Multi-object tracking
* Improved railway-obstacle datasets
* Track-region segmentation
* Depth estimation
* Distance estimation
* Relative speed estimation
* Night vision enhancement
* Weather-aware detection
* Thermal-camera integration
* Multi-camera fusion

### Railway Safety

* Obstacle trajectory prediction
* Time-to-collision estimation
* Track geometry analysis
* Level-crossing monitoring
* Platform safety monitoring
* Railway trespassing detection

### Road Safety

* Lane detection
* Vehicle collision-risk estimation
* Pothole detection
* Pedestrian detection
* Wrong-way vehicle detection
* Driver-assistance features

### System

* Edge AI deployment
* GPU acceleration
* Cloud monitoring
* Mobile application
* Central command dashboard
* Historical analytics
* Automated incident reports

---

# 📊 Project Vision

TRINETRA X is designed around a simple principle:

> **Detect early → Understand risk → Notify the right person → Preserve evidence.**

Instead of generating a generic alarm, the system attempts to understand:

```text
WHAT happened?
     ↓
WHERE did it happen?
     ↓
WHICH camera detected it?
     ↓
HOW serious is it?
     ↓
WHO needs to know?
     ↓
WHAT evidence should be stored?
```

---

# 👨‍💻 Author

**Anup Kumar**

B.Tech — Computer Science & Engineering
Artificial Intelligence & Machine Learning

Bansal Institute of Engineering and Technology, Lucknow
Affiliated with Dr. A.P.J. Abdul Kalam Technical University (AKTU)

---

# 📜 Project Disclaimer

TRINETRA X is developed for **educational, research, and demonstration purposes**.

The system is not intended to provide certified safety assurance or directly control railway or road vehicles. Any real-world deployment would require domain-specific hardware, extensive testing, independent validation, cybersecurity assessment, safety certification, and approval from the relevant authorities.

---

# ⭐ Support the Project

If you find TRINETRA X interesting, consider giving the repository a ⭐ on GitHub.

Contributions, suggestions, research collaboration, and technical feedback are welcome.
