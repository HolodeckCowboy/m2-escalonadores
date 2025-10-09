import threading

class QueueManager:
    def __init__(self, job_queue, process_job_func):
        self.job_queue = job_queue
        self.job_status = {}
        self.job_lock = threading.Lock()
        self.job_locks = {}
        self.process_job_func = process_job_func

    def get_lock(self, job_id: str) -> threading.Lock:
        if job_id not in self.job_locks:
            self.job_locks[job_id] = threading.Lock()
        return self.job_locks[job_id]

    def worker(self):
        while True:
            job_details = self.job_queue.get()
            if job_details is None:
                break
            try:
                self.process_job_func(job_details, self.get_lock)
            except Exception as e:
                raise Exception(e)
            finally:
                self.job_queue.task_done()

    def start_workers(self, num_workers):
        threads = []
        for i in range(num_workers):
            thread = threading.Thread(target=self.worker, name=f"Worker-{i + 1}")
            thread.daemon = True
            thread.start()
            threads.append(thread)
        return threads

    def get_job_status(self, job_id):
        with self.job_lock:
            status = self.job_status.get(job_id, {}).copy()
        return status