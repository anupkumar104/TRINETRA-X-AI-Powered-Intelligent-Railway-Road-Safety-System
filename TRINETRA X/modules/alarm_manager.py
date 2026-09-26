import time
import threading
import os

try:
    import winsound
except ImportError:
    winsound = None


class AlarmManager:

    def __init__(self):
        self.is_running = False

        # Keep the WAV file in the same folder as this alarm_manager.py
        self.wav_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "front_camera_alarm"
            ".wav"
        )

    def _alarm_loop(self, duration=5):

        self.is_running = True
        start_time = time.time()

        while (
            self.is_running
            and time.time() - start_time < duration
        ):

            if winsound:

                # 1. Existing beep
                winsound.Beep(
                    1200,
                    500
                )

                # 2. New WAV sound
                if os.path.exists(self.wav_file):
                    winsound.PlaySound(
                        self.wav_file,
                        winsound.SND_FILENAME
                    )

                time.sleep(0.2)

            else:
                print("\a")
                time.sleep(0.7)

        self.is_running = False

    def start_alarm(self, duration=5):

        if self.is_running:
            print("Alarm is already running.")
            return

        print("🚨 CRITICAL ALARM STARTED")
        print("🔊 Existing Beep + 2× WAV sound")

        thread = threading.Thread(
            target=self._alarm_loop,
            args=(duration,),
            daemon=True
        )

        thread.start()

    def stop_alarm(self):

        self.is_running = False

        if winsound:
            try:
                winsound.PlaySound(
                    None,
                    winsound.SND_PURGE
                )
            except Exception:
                pass

        print("Alarm stopped.")
