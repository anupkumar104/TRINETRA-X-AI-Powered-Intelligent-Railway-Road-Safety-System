from pathlib import Path
from datetime import datetime

from config import SNAPSHOT_DIR


class SnapshotManager:

    def __init__(self):
        self.base_dir = Path(SNAPSHOT_DIR)

    def save_snapshot(self, frame, mode, zone_id, object_name):
        """
        Save detected frame locally and return its relative path.
        """

        date_folder = datetime.now().strftime("%Y-%m-%d")

        safe_object_name = object_name.replace(" ", "_").lower()

        folder = (
            self.base_dir
            / mode
            / zone_id
            / date_folder
        )

        folder.mkdir(
            parents=True,
            exist_ok=True
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )[:-3]

        filename = (
            f"{safe_object_name}_{timestamp}.jpg"
        )

        file_path = folder / filename

        import cv2

        success = cv2.imwrite(
            str(file_path),
            frame
        )

        if not success:
            raise RuntimeError(
                f"Could not save snapshot: {file_path}"
            )

        # Store relative path in database
        relative_path = file_path.relative_to(
            self.base_dir.parent
        )

        return str(relative_path)