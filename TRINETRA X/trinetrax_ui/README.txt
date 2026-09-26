TRINETRA X AI - UI UPDATE
==========================

This UI update is designed to sit on top of the existing working TRINETRA X AI backend.
It keeps the existing YOLO detector, RiskEngine, ZoneClientRegistry and CriticalEventHandler.

Added:
1. Alert Routing Center using the REAL CriticalEventHandler result.
2. Individual routing and Zone Broadcast routing display.
3. Recipient ID, name, recipient type and actual delivery status.
4. Actual backend-generated safety message display.
5. Actual backend snapshot/evidence viewer.
6. Notification history per recipient.
7. Alert-flow visualization.
8. Railway / Road working mode switch.
9. Live/Simulation source indication (Laptop Camera for source 0, RTSP / IP CAMERA otherwise).
10. TRINETRA X AI logo in header, loader, empty state, footer and favicon.
11. Light professional UI (not dark theme).
12. Event detail modal.

IMPORTANT:
- Do NOT copy main.py into this UI folder.
- Run this folder from inside the main AI-Safety-System project so ../main.py and backend modules are available.
- yolo11n.pt must remain in the project root, exactly as your existing backend expects.

Run:
    cd C:\Users\anups\OneDrive\Desktop\AI-Safety-System\trinetrax_ui
    python ui_app.py

Then open:
    http://127.0.0.1:5000

The UI stores event details for the current UI session only. Clearing UI alerts does not delete backend/database records.
