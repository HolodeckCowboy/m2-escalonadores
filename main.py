import math
from queue import Queue

from queue_manager import QueueManager
from scheduler import Scheduler
from job import Job, JobStatus

def setup_job_queue(queue_data, quantum):

    new_queue = Queue()

    for process in queue_data:
        remaining_quantum = math.ceil(process.get('execution_time') / quantum)
        job = Job(
            process.get('id'),
            process.get('arrival_time'),
            process.get('execution_time'),
            process.get('execution_time'),
            remaining_quantum,
            JobStatus.READY.value
        )
        new_queue.put(job)

    return new_queue

def emulate():
    return True

if __name__ == "__main__":

    process_queue = [
        {'id': 1, 'burst_time': 10, 'arrival_time': 0},
        {'id': 2, 'burst_time': 10, 'arrival_time': 1},
        {'id': 3, 'burst_time': 10, 'arrival_time': 2}
    ]

    quantum = 2

    scheduler = Scheduler(process_queue)
    scheduler.findavgTime(quantum)

    manager = QueueManager(process_queue, emulate)

