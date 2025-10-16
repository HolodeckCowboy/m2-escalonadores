import threading
import os
import time


class ConsoleMonitor(threading.Thread):
    """
    Uma thread que exibe o estado atual do simulador no console
    a cada tick do clock.
    """

    def __init__(self, clock, queue_manager, num_cores):
        super().__init__()
        self.clock = clock
        self.queue_manager = queue_manager
        self.num_cores = num_cores
        self.running = True
        self.daemon = True

    def run(self):
        """Loop principal: espera um tick, limpa a tela e imprime o status."""
        while self.running:
            with self.clock.time_lock:
                self.clock.tick_condition.wait()
                if not self.running:
                    break

            time.sleep(0.001)
            self.print_status()

    def print_status(self):
        """Limpa o console e imprime o estado das CPUs e filas."""
        os.system('cls' if os.name == 'nt' else 'clear')

        current_time = self.clock.get_time()
        print(f"--- Simulador de Escalonamento Round Robin [Tempo Global: {current_time}] ---")
        print("Pressione [Barra de Espaço] para simular E/S | [Ctrl+C] para sair")

        print("\n== Estado das CPUs ==")
        cpu_states = self.queue_manager.get_cpu_states()
        for i in range(1, self.num_cores + 1):
            cpu_name = f"CPU-{i}"
            state = cpu_states.get(cpu_name, 'Initializing')
            print(f"  {cpu_name}: {state}")

        print("\n== Filas do Sistema ==")

        ready_jobs = self.queue_manager.get_ready_queue_snapshot()
        ready_ids = [job.job_id for job in ready_jobs]
        print(f"  Prontos     ({len(ready_ids)}): {ready_ids}")

        with self.queue_manager.blocked_lock:
            blocked_jobs = self.queue_manager.blocked_queue
            blocked_ids = [f"{job.job_id} (sai em T={job.io_block_end_time})" for job in blocked_jobs]
            print(f"  Bloqueados  ({len(blocked_ids)}): {blocked_ids}")

        with self.queue_manager.finish_lock:
            finished_count = len(self.queue_manager.finished_jobs)
            print(f"\nFinalizados: {finished_count}")

        print("\n" + "=" * 60)
        print("Logs detalhados estão sendo salvos em 'simulation.log'")

    def stop(self):
        """Sinaliza para a thread parar."""
        self.running = False