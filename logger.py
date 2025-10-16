import datetime
import threading


class Logger:
    def __init__(self, log_file="simulation.log", log_to_console=True):
        self.log_file = log_file
        self.lock = threading.Lock()
        self.log_to_console = log_to_console
        with open(self.log_file, "w") as f:
            f.write("Log da Simulação do Escalonador Round Robin\n")
            f.write("=" * 40 + "\n")

    def log(self, message, time=None):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_prefix = f"[Global Time: {time}]" if time is not None else ""
        log_message = f"[{timestamp}]{time_prefix} {message}\n"

        if self.log_to_console:
            print(log_message.strip())

        with self.lock:
            with open(self.log_file, "a") as f:
                f.write(log_message)