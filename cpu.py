import threading
from job import JobStatus


class CPU(threading.Thread):
    def __init__(self, cpu_id, scheduler, clock, logger, simulation_end_event):
        super().__init__()
        self.cpu_id = cpu_id
        self.scheduler = scheduler
        self.clock = clock
        self.logger = logger
        self.current_job = None
        self.running = True
        self.simulation_end_event = simulation_end_event

    def run(self):
        while self.running:
            if self.current_job is None:
                self.current_job = self.scheduler.get_next_job()
                if self.current_job:
                    self.current_job.status = JobStatus.RUNNING
                    self.current_job.context_switches += 1
                    self.logger.log(f"CPU-{self.cpu_id}: Processo {self.current_job.job_id} iniciou execução.",
                                    self.clock.get_time())
                else:
                    # Se não há trabalho e a simulação terminou, a thread pode parar
                    if self.simulation_end_event.is_set():
                        self.stop()
                    continue  # Fica ociosa esperando por trabalho

            if self.current_job:
                quantum = self.scheduler.calculate_quantum()
                time_slice = min(quantum, self.current_job.remaining_time)

                start_time = self.clock.get_time()
                self.logger.log(
                    f"CPU-{self.cpu_id}: Executando {self.current_job.job_id} (faltam {self.current_job.remaining_time}). Quantum={quantum}.",
                    start_time)

                # Executa por uma unidade de tempo por vez
                for _ in range(time_slice):
                    if self.current_job.remaining_time > 0:
                        with self.clock.time_lock:
                            self.clock.tick_condition.wait()  # Espera um pulso do clock para executar
                        self.current_job.remaining_time -= 1
                    else:
                        break  # O processo terminou antes do fim da fatia de tempo

                end_time = self.clock.get_time()

                if self.current_job.remaining_time <= 0:
                    self.scheduler.finish_job(self.current_job)
                    self.logger.log(f"CPU-{self.cpu_id}: Processo {self.current_job.job_id} finalizado.", end_time)
                else:
                    # Preempção: devolve o processo para a fila de prontos
                    self.scheduler.add_job(self.current_job)
                    self.logger.log(f"CPU-{self.cpu_id}: Processo {self.current_job.job_id} sofreu preempção.",
                                    end_time)

                self.current_job = None  # Libera a CPU

    def stop(self):
        self.running = False