import threading
from queue import Queue
from job import JobStatus

BASE_QUANTUM = 6
MIN_QUANTUM = 2


class QueueManager:
    def __init__(self, job_queue, process_job_func, logger, clock, io_request_flag, dynamic_quantum=False,
                 fixed_quantum=4):
        self.job_queue = job_queue
        self.process_job_func = process_job_func
        self.logger = logger
        self.clock = clock

        self.finished_jobs = []
        self.dynamic_quantum = dynamic_quantum
        self.fixed_quantum = fixed_quantum

        self.blocked_queue = []
        self.blocked_lock = threading.Lock()
        self.finish_lock = threading.Lock()

        self.io_request_flag = io_request_flag
        self.io_flag_lock = threading.Lock()

        self.running = True

        self.cpu_states = {}
        self.cpu_state_lock = threading.Lock()

    def calculate_quantum(self):
        if not self.dynamic_quantum:
            return self.fixed_quantum
        else:
            num_ready = self.job_queue.qsize()
            quantum = BASE_QUANTUM - num_ready
            return max(MIN_QUANTUM, quantum)

    def add_job(self, job):
        job.status = JobStatus.READY
        self.job_queue.put(job)
        self.logger.log(f"Scheduler: Processo {job.job_id} adicionado à fila de prontos.", self.clock.get_time())

    def finish_job(self, job):
        current_time = self.clock.get_time()
        job.status = JobStatus.FINISHED
        job.turnaround_time = current_time - job.arrival_time
        job.wait_time = job.turnaround_time - job.execution_time

        with self.finish_lock:
            self.finished_jobs.append(job)

    def block_job(self, job, io_duration):
        """Move um job para a fila de E/S (bloqueados)."""
        current_time = self.clock.get_time()
        job.status = JobStatus.BLOCKED
        job.io_block_end_time = current_time + io_duration

        with self.blocked_lock:
            self.blocked_queue.append(job)

        self.logger.log(f"Scheduler: Processo {job.job_id} movido para E/S (duração: {io_duration}).", current_time)

    def io_manager_worker(self):
        """Worker que verifica a fila de E/S e desbloqueia jobs."""
        while self.running:
            with self.clock.time_lock:
                self.clock.tick_condition.wait()
                if not self.running:
                    break

            current_time = self.clock.get_time()
            unblocked_jobs = []

            with self.blocked_lock:
                remaining_blocked = []
                for job in self.blocked_queue:
                    if current_time >= job.io_block_end_time:
                        unblocked_jobs.append(job)
                    else:
                        remaining_blocked.append(job)
                self.blocked_queue = remaining_blocked

            for job in unblocked_jobs:
                self.logger.log(f"IOManager: Processo {job.job_id} concluiu E/S.", current_time)
                self.add_job(job)

    def is_idle(self):
        """Verifica se não há jobs prontos ou bloqueados."""
        with self.blocked_lock:
            return self.job_queue.empty() and not self.blocked_queue

    def set_cpu_state(self, cpu_name, job_id_or_status):
        """Define o estado atual de uma CPU."""
        with self.cpu_state_lock:
            self.cpu_states[cpu_name] = job_id_or_status

    def get_cpu_states(self):
        """Retorna uma cópia dos estados das CPUs."""
        with self.cpu_state_lock:
            return self.cpu_states.copy()

    def get_ready_queue_snapshot(self):
        """Retorna um snapshot thread-safe da fila de prontos."""
        with self.job_queue.mutex:
            return list(self.job_queue.queue)

    def worker(self):
        """Função do worker (CPU) que consome da fila de jobs."""
        cpu_name = threading.current_thread().name
        self.set_cpu_state(cpu_name, 'Idle')

        while True:
            job = self.job_queue.get()

            if job is None:
                self.job_queue.task_done()
                self.set_cpu_state(cpu_name, 'Offline')
                break

            try:
                self.set_cpu_state(cpu_name, job.job_id)
                self.process_job_func(job, self)
            except Exception as e:
                self.logger.log(f"Erro processando {job.job_id}: {e}", self.clock.get_time())
            finally:
                self.set_cpu_state(cpu_name, 'Idle')
                self.job_queue.task_done()

    def start_workers(self, num_workers):
        """Inicia as threads dos workers (CPUs)."""
        threads = []
        for i in range(num_workers):
            thread = threading.Thread(target=self.worker, name=f"CPU-{i + 1}")
            thread.daemon = True
            thread.start()
            threads.append(thread)
        return threads

    def start_io_manager(self):
        """Inicia a thread do gerenciador de E/S."""
        thread = threading.Thread(target=self.io_manager_worker, name="IOManager")
        thread.daemon = True
        thread.start()
        return thread

    def stop(self):
        """Sinaliza para o IOManager parar."""
        self.running = False