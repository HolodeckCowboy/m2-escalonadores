from enum import Enum


class JobStatus(Enum):
    NEW = 'NOVO'
    READY = 'PRONTO'
    RUNNING = 'EXECUTANDO'
    FINISHED = 'FINALIZADO'


class Job:
    def __init__(self, job_id, arrival_time, execution_time):
        self.job_id = job_id
        self.arrival_time = arrival_time
        self.execution_time = execution_time
        self.remaining_time = execution_time
        self.status = JobStatus.NEW

        # Métricas de desempenho
        self.wait_time = 0
        self.turnaround_time = 0
        self.context_switches = 0