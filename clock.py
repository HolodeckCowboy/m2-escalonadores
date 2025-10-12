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

    def run(self):
        while self.running:
            time.sleep(self.time_unit)
            with self.time_lock:
                self.global_time += 1
                self.tick_condition.notify_all()
                
    def get_time(self):
        with self.time_lock:
            return self.global_time

    def stop(self):
        self.running = False