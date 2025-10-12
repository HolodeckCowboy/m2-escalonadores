import threading


class Dispatcher(threading.Thread):
    def __init__(self, process_list, scheduler, clock, logger):
        super().__init__()
        self.process_list = sorted(process_list, key=lambda p: p.arrival_time)
        self.scheduler = scheduler
        self.clock = clock
        self.logger = logger
        self.running = True

    def run(self):
        while self.running:
            with self.clock.time_lock:

                self.clock.tick_condition.wait()
                current_time = self.clock.global_time

                while self.process_list and self.process_list[0].arrival_time <= current_time:
                    job = self.process_list.pop(0)
                    self.scheduler.add_job(job)

            if not self.process_list and self.running:
                self.stop()

    def stop(self):
        self.running = False