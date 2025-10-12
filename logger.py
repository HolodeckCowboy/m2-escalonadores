import datetime


class Logger:
    def __init__(self, log_file="simulation.log"):
        self.log_file = log_file
        with open(self.log_file, "w") as f:
            f.write("Log da Simulação do Escalonador Round Robin\n")
            f.write("=" * 40 + "\n")

    def log(self, message, time=None):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_prefix = f"[Global Time: {time}]" if time is not None else ""
        log_message = f"[{timestamp}]{time_prefix} {message}\n"

        print(log_message.strip())
        with open(self.log_file, "a") as f:
            f.write(log_message)