import time
import threading

try:
    import winsound
except ImportError:
    winsound = None


class AlarmManager:

    def __init__(self):
        self.is_running = False

    def _alarm_loop(self, duration=5):

        self.is_running = True

        start_time = time.time()

        while (
            self.is_running
            and time.time() - start_time < duration
        ):

            if winsound:

                winsound.Beep(
                    1200,
                    500
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

        thread = threading.Thread(
            target=self._alarm_loop,
            args=(duration,),
            daemon=True
        )

        thread.start()

    def stop_alarm(self):

        self.is_running = False

        print("Alarm stopped.")