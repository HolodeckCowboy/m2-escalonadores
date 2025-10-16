import threading


class Dispatcher(threading.Thread):
    def __init__(self, process_list, queue_manager, clock, logger):
        super().__init__()
        self.process_list = sorted(process_list, key=lambda p: p.arrival_time)
        self.queue_manager = queue_manager
        self.clock = clock
        self.logger = logger
        self.running = True

    def run(self):
        while self.running:
            current_time = 0

            with self.clock.time_lock:
                self.clock.tick_condition.wait()
                if not self.running:
                    break

                current_time = self.clock.global_time

            jobs_to_add = []

            while self.process_list and self.process_list[0].arrival_time <= current_time:
                jobs_to_add.append(self.process_list.pop(0))

            for job in jobs_to_add:
                self.queue_manager.add_job(job)

            if not self.process_list:
                self.stop()

    def stop(self):
        self.running = False
        with self.clock.time_lock:
            self.clock.tick_condition.notify_all()