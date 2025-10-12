import csv
import time
import threading
from scheduler import Scheduler
from job import Job
from logger import Logger
from plotter import plot_gantt_chart
from clock import Clock
from dispatcher import Dispatcher
from cpu import CPU


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
    print("\n--- Relatório Final da Simulação ---")
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


if __name__ == "__main__":
    NUM_CORES = 2
    QUANTUM = 5
    INPUT_CSV = "processes.csv"
    USE_DYNAMIC_QUANTUM = False

    simulation_end_event = threading.Event()

    logger = Logger()
    clock = Clock(time_unit=0.005)

    all_processes = load_jobs_from_csv(INPUT_CSV)
    total_jobs = len(all_processes)

    scheduler = Scheduler(logger, clock, dynamic_quantum=USE_DYNAMIC_QUANTUM, fixed_quantum=QUANTUM)
    dispatcher = Dispatcher(all_processes, scheduler, clock, logger)

    cpus = []
    for i in range(NUM_CORES):
        cpu = CPU(i + 1, scheduler, clock, logger, simulation_end_event)
        cpus.append(cpu)

    logger.log("Iniciando simulação...")
    clock.start()
    dispatcher.start()
    for cpu in cpus:
        cpu.start()

    try:
        while len(scheduler.finished_jobs) < total_jobs:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nInterrupção manual detectada. Encerrando simulação...")

    logger.log("Todos os processos foram concluídos ou a simulação foi interrompida.")
    simulation_end_event.set()

    dispatcher.stop()
    clock.stop()

    dispatcher.join()
    for cpu in cpus:
        cpu.join()
    clock.join()

    print_report(scheduler.finished_jobs, clock.get_time(), NUM_CORES)

    try:
        plot_gantt_chart("simulation.log", NUM_CORES)
    except Exception as e:
        print(f"\nNão foi possível gerar o gráfico: {e}")