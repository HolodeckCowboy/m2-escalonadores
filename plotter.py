import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import re
from collections import defaultdict


def plot_gantt_chart(log_file, num_cores):
    """
    Gera um gráfico de Gantt a partir de um arquivo de log da simulação.
    """
    start_pattern = re.compile(r"\[Global Time: (\d+)\] CPU-(\d+): Processo (\S+) iniciou a execução.")
    preempt_pattern = re.compile(r"\[Global Time: (\d+)\] CPU-(\d+): Processo (\S+) sofreu preempção.*")
    finish_pattern = re.compile(r"\[Global Time: (\d+)\] CPU-(\d+): Processo (\S+) finalizado.")

    cpu_events = defaultdict(list)
    active_jobs = {}

    with open(log_file, 'r') as f:
        for line in f:
            start_match = start_pattern.search(line)
            preempt_match = preempt_pattern.search(line)
            finish_match = finish_pattern.search(line)

            if start_match:
                time, cpu, job = start_match.groups()
                active_jobs[cpu] = (job, int(time))

            elif preempt_match or finish_match:
                match = preempt_match or finish_match
                time, cpu, job = match.groups()
                if cpu in active_jobs and active_jobs[cpu][0] == job:
                    start_job, start_time = active_jobs.pop(cpu)
                    duration = int(time) - start_time
                    if duration > 0:
                        cpu_events[f"CPU-{cpu}"].append((start_time, duration, job))

    fig, ax = plt.subplots(figsize=(15, 2 * num_cores))

    y_labels = sorted(cpu_events.keys())
    y_ticks = [i * 10 for i in range(len(y_labels))]

    process_ids = sorted(list(set(job for cpu in cpu_events.values() for _, _, job in cpu)))
    colors = plt.cm.get_cmap('viridis', len(process_ids))
    color_map = {pid: colors(i) for i, pid in enumerate(process_ids)}

    max_time = 0
    for i, cpu_label in enumerate(y_labels):
        for start, duration, job in cpu_events[cpu_label]:
            ax.broken_barh([(start, duration)], (y_ticks[i] - 4, 8),
                           facecolors=(color_map[job]), edgecolor='black')
            ax.text(start + duration / 2, y_ticks[i], job, ha='center', va='center', color='white', weight='bold')
            max_time = max(max_time, start + duration)

    ax.set_ylim(-5, len(y_labels) * 10)
    ax.set_xlim(0, max_time + 5)
    ax.set_xlabel('Unidades de Tempo')
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    plt.title("Gráfico de Gantt da Execução dos Processos")
    plt.tight_layout()
    plt.savefig("gantt_chart.png")
    print("\nGráfico de Gantt salvo como 'gantt_chart.png'")
    # plt.show()