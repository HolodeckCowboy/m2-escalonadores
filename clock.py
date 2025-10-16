import threading
import time


class Clock(threading.Thread):
    def __init__(self, time_unit=0.01):
        super().__init__()
        self.global_time = 0
        self.time_unit = time_unit
        self.running = True
        self.time_lock = threading.Lock()
        self.tick_condition = threading.Condition(self.time_lock)


        self.pause_event = threading.Event()
        self.pause_event.set()

    def run(self):
        while self.running:
            self.pause_event.wait()

            time.sleep(self.time_unit)

            with self.time_lock:
                if not self.running:
                    break
                if not self.pause_event.is_set():
                    continue

                self.global_time += 1
                self.tick_condition.notify_all()

    def get_time(self):
        with self.time_lock:
            return self.global_time

    def stop(self):
        self.running = False
        self.resume()
        with self.time_lock:
            self.tick_condition.notify_all()

    def pause(self):
        """Pausa o clock. O evento é limpo (clear), fazendo o wait() bloquear."""
        self.pause_event.clear()

    def resume(self):
        """Retoma o clock. O evento é definido (set), liberando o wait()."""
        self.pause_event.set()