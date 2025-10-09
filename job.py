from enum import Enum


class JobStatus(Enum):
    READY = 'ready'
    RUNNING = 'running'
    BLOCKED = 'blocked'
    FINISHED = 'finished'

class Job:
    def __init__(self, job_id, arrival_time, execution_time, remaining_time, remaining_quantum, status):
        self.job_id = job_id
        self.arrival_time = arrival_time
        self.execution_time = execution_time
        self.remaining_time = remaining_time
        self.remaining_quantum = remaining_quantum
        self.status = status