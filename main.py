import csv
import time
import threading
import queue
from queue_manager import QueueManager
from job import Job, JobStatus
from logger import Logger
from plotter import plot_gantt_chart
from clock import Clock
from dispatcher import Dispatcher
from pynput import keyboard
from console_monitor import ConsoleMonitor

NUM_CORES = 2
QUANTUM = 5
INPUT_CSV = "processes.csv"
USE_DYNAMIC_QUANTUM = True
IO_BLOCK_DURATION = 10

io_request_flag = threading.Event()


def load_jobs_from_csv(file_path):
    jobs = []
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            job_id, arrival_time, execution_time = row
            jobs.append(Job(job_id, int(arrival_time), int(execution_time)))
    return jobs


def print_report(finished_jobs, total_time, num_cores):
    print("\n\n" + "=" * 60)
    print("--- Relatório Final da Simulação ---")
    if not finished_jobs:
        print("Nenhum processo foi finalizado.")
        return

    total_wait_time = sum(j.wait_time for j in finished_jobs)
    total_turnaround_time = sum(j.turnaround_time for j in finished_jobs)
    total_context_switches = sum(j.context_switches for j in finished_jobs)

    num_jobs = len(finished_jobs)
    avg_wait_time = total_wait_time / num_jobs
    avg_turnaround_time = total_turnaround_time / num_jobs

    total_cpu_time_available = total_time * num_cores
    total_cpu_time_used = sum(j.execution_time for j in finished_jobs)
    cpu_utilization = (total_cpu_time_used / total_cpu_time_available) * 100 if total_cpu_time_available > 0 else 0

    print(f"Tempo total da simulação: {total_time} unidades")
    print(f"Utilização total da CPU: {cpu_utilization:.2f}%")
    print(f"Tempo médio de espera: {avg_wait_time:.2f}")
    print(f"Tempo médio de turnaround: {avg_turnaround_time:.2f}")
    print(f"Total de trocas de contexto: {total_context_switches}")
    print("-" * 35)

    for job in sorted(finished_jobs, key=lambda x: int(x.job_id.replace('P', ''))):
        print(
            f"Processo {job.job_id}: Turnaround={job.turnaround_time}, Espera={job.wait_time}, Trocas={job.context_switches}")


def process_job_cpu(job: Job, q_manager: QueueManager):
    """
    Esta função é a lógica de execução da CPU.
    Ela é chamada por um worker do QueueManager.
    """

    logger = q_manager.logger
    clock = q_manager.clock
    cpu_name = threading.current_thread().name

    job.status = JobStatus.RUNNING
    job.context_switches += 1
    logger.log(f"{cpu_name}: Processo {job.job_id} iniciou execução.", clock.get_time())

    quantum = q_manager.calculate_quantum()
    time_slice = min(quantum, job.remaining_time)

    start_time = clock.get_time()
    logger.log(
        f"{cpu_name}: Executando {job.job_id} (faltam {job.remaining_time}). Quantum={quantum}.",
        start_time)

    for _ in range(time_slice):
        if job.remaining_time > 0:
            with clock.time_lock:
                clock.tick_condition.wait()

            if not clock.running:
                logger.log(f"{cpu_name}: Clock parou. Interrompendo {job.job_id}.", clock.get_time())
                q_manager.add_job(job)
                return

            is_io_request = False
            with q_manager.io_flag_lock:
                if q_manager.io_request_flag.is_set():
                    q_manager.io_request_flag.clear()
                    is_io_request = True

            if is_io_request:
                logger.log(f"{cpu_name}: Processo {job.job_id} solicitou E/S.", clock.get_time())
                q_manager.block_job(job, IO_BLOCK_DURATION)
                return

            job.remaining_time -= 1
        else:
            break

    end_time = clock.get_time()

    if job.remaining_time <= 0:
        q_manager.finish_job(job)
        logger.log(f"{cpu_name}: Processo {job.job_id} finalizado.", end_time)
    else:
        q_manager.add_job(job)
        logger.log(f"{cpu_name}: Processo {job.job_id} sofreu preempção.", end_time)



def on_press(key, logger, clock):
    """Callback quando uma tecla é pressionada."""
    global io_request_flag
    if key == keyboard.Key.space:
        if not io_request_flag.is_set():
            logger.log("--- [EVENTO] Solicitação de E/S recebida (Barra de Espaço) ---", clock.get_time())
            io_request_flag.set()


def start_keyboard_listener(logger, clock):
    """Inicia o listener de teclado em uma thread separada."""
    listener = keyboard.Listener(on_press=lambda key: on_press(key, logger, clock))
    listener.daemon = True
    listener.start()
    logger.log("Listener de teclado iniciado. Pressione [Barra de Espaço] para simular E/S.")
    return listener




if __name__ == "__main__":
    logger = Logger(log_to_console=True)
    clock = Clock(time_unit=0.005)

    all_processes = load_jobs_from_csv(INPUT_CSV)
    total_jobs = len(all_processes)

    ready_queue = queue.Queue()

    queue_manager = QueueManager(
        job_queue=ready_queue,
        process_job_func=process_job_cpu,
        logger=logger,
        clock=clock,
        io_request_flag=io_request_flag,
        dynamic_quantum=USE_DYNAMIC_QUANTUM,
        fixed_quantum=QUANTUM
    )

    dispatcher = Dispatcher(all_processes, queue_manager, clock, logger)

    monitor = ConsoleMonitor(clock, queue_manager, NUM_CORES)

    logger.log("Iniciando simulação...")

    clock.start()
    dispatcher.start()
    io_manager_thread = queue_manager.start_io_manager()
    queue_manager.start_workers(NUM_CORES)
    listener = start_keyboard_listener(logger, clock)
    monitor.start()

    try:
        while len(queue_manager.finished_jobs) < total_jobs:
            time.sleep(0.5)
            if not dispatcher.is_alive() and queue_manager.is_idle():
                if len(queue_manager.finished_jobs) < total_jobs:
                    time.sleep(0.5)

                if len(queue_manager.finished_jobs) == total_jobs:
                    break
                else:
                    logger.log(
                        f"Dispatcher terminou, mas {total_jobs - len(queue_manager.finished_jobs)} jobs ainda não concluídos. Verificando...")
                    if not queue_manager.is_idle():
                        continue
                    else:
                        break

    except KeyboardInterrupt:
        print("\nInterrupção manual detectada. Encerrando simulação...")
        logger.log("--- Interrupção manual ---")

    logger.log("Todos os processos foram concluídos ou a simulação foi interrompida.")

    monitor.stop()
    queue_manager.stop()
    dispatcher.stop()

    for _ in range(NUM_CORES):
        ready_queue.put(None)

    clock.stop()

    dispatcher.join()
    io_manager_thread.join()
    clock.join()
    monitor.join()

    ready_queue.join()

    print_report(queue_manager.finished_jobs, clock.get_time(), NUM_CORES)

    try:
        plot_gantt_chart("simulation.log", NUM_CORES)
    except Exception as e:
        print(f"\nNão foi possível gerar o gráfico: {e}")