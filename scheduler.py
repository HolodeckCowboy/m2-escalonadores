from queue import Queue
from job import JobStatus

BASE_QUANTUM = 6
MIN_QUANTUM = 2

class Scheduler:
    def __init__(self, logger, clock, dynamic_quantum=False, fixed_quantum=4):
        self.ready_queue = Queue()
        self.finished_jobs = []
        self.logger = logger
        self.clock = clock
        self.dynamic_quantum = dynamic_quantum
        self.fixed_quantum = fixed_quantum

    def calculate_quantum(self):
        if not self.dynamic_quantum:
            return self.fixed_quantum
        else:
            num_ready = self.ready_queue.qsize()
            quantum = BASE_QUANTUM - num_ready
            return max(MIN_QUANTUM, quantum)

    def add_job(self, job):
        job.status = JobStatus.READY
        self.ready_queue.put(job)
        self.logger.log(f"Scheduler: Processo {job.job_id} adicionado à fila de prontos.", self.clock.get_time())

    def get_next_job(self):
        if not self.ready_queue.empty():
            return self.ready_queue.get()
        return None

    def finish_job(self, job):
        current_time = self.clock.get_time()
        job.status = JobStatus.FINISHED
        job.turnaround_time = current_time - job.arrival_time
        job.wait_time = job.turnaround_time - job.execution_time
        self.finished_jobs.append(job)

    def is_idle(self):
        return self.ready_queue.empty()