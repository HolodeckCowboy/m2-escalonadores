class Scheduler:

    def __init__(self, process_queue):
        self.process_queue = process_queue
        self.job_amount = len(process_queue)

    def findWaitingTime(self, quantum):

        remaining_burst_time = [0] * self.job_amount

        for i in range(self.job_amount):
            remaining_burst_time[i] = self.process_queue[i].get('burst_time')

        time = 0

        for i in range(self.job_amount):
            while remaining_burst_time[i] > 0:
                self.emulate_execution(remaining_burst_time, i, quantum, time)

    def emulate_execution(self, remaining_burst_time, i, quantum, time):
        if remaining_burst_time[i] > quantum:
            time += quantum
            remaining_burst_time[i] -= quantum

        else:
            time = time + remaining_burst_time[i]
            self.process_queue[i].wait_time = time - self.process_queue[i].get('burst_time')
            remaining_burst_time[i] = 0

    def findTurnAroundTime(self):
        for i in range(self.job_amount):
            self.process_queue[i].turnaround_time = self.process_queue[i].get('burst_time') + self.process_queue[i].get(
                'wait_time')

    def findavgTime(self, quantum):
        self.findWaitingTime(quantum)

        self.findTurnAroundTime()

        total_wt = 0
        total_tat = 0
        for i in range(self.job_amount):
            total_wt = total_wt + self.process_queue[i].get('wait_time')
            total_tat = total_tat + self.process_queue[i].get('turnaround_time')

        return total_wt, total_tat
