import queue
from collections import Counter, OrderedDict
import random
import matplotlib.pyplot as plt

class Simulator:
    def __init__(self, filename):
        self.filename = filename
        itemList = []
        with open(filename, "r") as fp:
            lines = fp.readlines()
            for l in lines:
                itemList.append(Line(l.split(",")))
        self.lines = itemList
    
    def simulate(self, bufferPolicy):
        self.hits = 0
        self.misses = 0
        self.total = 0
        self.seen_misses = 0
        self.worst_case = 0
        self.seen = []
        for l in self.lines:
            frame_id = l.frame_id
            if l.fix:
                self.total += 1
                hit = bufferPolicy.fix(l.frame_id)
                self.hits += hit
                self.misses += not hit
                self.seen_misses += (not hit) and (frame_id in self.seen)
                self.worst_case += (frame_id in self.seen)
                self.seen.append(frame_id)
            else:
                bufferPolicy.unfix(l.frame_id)
        # print(f"Hits: {self.hits}\nMisses: {self.misses}\nSeen Misses: {self.seen_misses}\nWorst Case: {self.worst_case}\nTotal: {self.total}")
        
            
class Line:
    def __init__(self, itemList):
        self.frame_id = itemList[2]
        self.fix = itemList[1] == "True"
        self.timestamp = itemList[2]

class Policy():

    def __init__(self):
        self.name = "BasePolicy"
    
    def fix(self, frame_id):
        raise NotImplementedError
        # return bool
    
    def unfix(self, frame_id):
        raise NotImplementedError
        # No Return

class TestPolicy1(Policy):
    def __init__(self):
        self.name = "TestPolicy1"
        self.counter = 0

    def fix(self, frame_id):
        return False
    
    def unfix(self, frame_id):
        # count calls
        self.counter += 1 

class TestPolicy2(Policy):
    def __init__(self):
        self.name = "TestPolicy2"
        self.counter = 0

    def fix(self, frame_id):
        return True
    
    def unfix(self, frame_id):
        # count calls
        self.counter += 1

class FIFO(Policy):
    "Notice that things close to 0 are closer to being evicted"
    def __init__(self, buffer_size):
        self.name = "FIFO"
        self.size = buffer_size
        self.queue = []
        self.fixed = Counter()

    def fix(self, frame_id):
        if frame_id in self.queue:
            self.fixed[frame_id] += 1
            return True
        else:
            if len(self.queue) == self.size:
                for id in self.queue:
                    if self.fixed[id] == 0:
                        self.queue.remove(id)
                        self.queue.append(frame_id)
                        self.fixed[frame_id] += 1
                        break
                else:
                    raise Exception("All items in queue are fixed")
            else:
                self.fixed[frame_id] += 1
                self.queue.append(frame_id)
            return False

    def unfix(self, frame_id):
        self.fixed[frame_id] -= 1

class LRU(Policy):
    def __init__(self, buffer_size):
        self.name = "LRU"
        self.size = buffer_size
        self.queue = OrderedDict()
        self.fixed = Counter()

    def fix(self, frame_id):
        if frame_id in self.queue:
            self.fixed[frame_id] += 1
            self.queue.move_to_end(frame_id)
            return True
        else:
            if len(self.queue) == self.size:
                for id in self.queue:
                    if self.fixed[id] == 0:
                        del self.queue[id]
                        self.queue[frame_id] = None
                        self.fixed[frame_id] += 1
                        break
                else:
                    raise Exception("All items in queue are fixed")
            else:
                self.fixed[frame_id] += 1
                self.queue[frame_id] = None
            return False

    def unfix(self, frame_id):
        self.fixed[frame_id] -= 1

class RR(Policy):
    def __init__(self, buffer_size):
        self.name = "RR"
        self.size = buffer_size
        self.queue = []
        self.fixed = Counter()

    def fix(self, frame_id):
        if frame_id in self.queue:
            self.fixed[frame_id] += 1
            return True
        else:
            if len(self.queue) == self.size:
                unfixed = []
                for id in self.queue:
                    if self.fixed[id] == 0:
                        unfixed.append(id)
                if unfixed:
                    id = random.choice(unfixed)
                    self.queue.remove(id)
                    self.queue.append(frame_id)
                    self.fixed[frame_id] += 1
                else:
                    raise Exception("All items in queue are fixed")

            
            else:
                self.fixed[frame_id] += 1
                self.queue.append(frame_id)
            return False

    def unfix(self, frame_id):
        self.fixed[frame_id] -= 1

class TwoQ(Policy):
    def __init__(self, buffer_size):
        self.name = "2Q"
        self.size = buffer_size
        self.fifo = []
        # self.queue = []
        self.fixed = Counter()
        self.lru = OrderedDict()
        self.lru_fixed = Counter()

    def fix(self, frame_id):
        if frame_id in self.lru:
            self.fixed[frame_id] += 1
            self.lru.move_to_end(frame_id)
            return True
        ## Try to add to lru
        if frame_id in self.fifo:
            self.fixed[frame_id] += 1
            self.lru[frame_id] = None
            self.fifo.remove(frame_id)
            return True
        ## Add to FIFO
        if len(self.fifo) + len(self.lru) >= self.size:
            inserted = False
            for id in self.fifo:
                if self.fixed[id] == 0:
                    self.fifo.remove(id)
                    self.fifo.append(frame_id)
                    self.fixed[frame_id] += 1
                    inserted = True
                    break
            if not inserted:
                for id in self.lru.keys():
                    if self.fixed[id] == 0:
                        del self.lru[id]
                        self.fifo.append(frame_id)
                        self.fixed[frame_id] += 1
                        inserted = True
                        break
                else:
                    raise Exception("All items in queue are fixed")
        else:
            self.fixed[frame_id] += 1
            self.fifo.append(frame_id)
        return False
        
    def unfix(self, frame_id):
        self.fixed[frame_id] -= 1 
                


class LFU(Policy):
    def __init__(self, buffer_size):
        self.name = "LFU"
        self.size = buffer_size
        self.queue = {}
        self.fixed = Counter()
        self.history = Counter()

    def fix(self, frame_id):
        if frame_id in self.queue:
            self.fixed[frame_id] += 1
            self.queue[frame_id] += 1
            self.queue = {k:v for k, v in sorted(self.queue.items(), key=lambda item: item[1])}
            return True
        else:
            if len(self.queue) == self.size:
                for id in self.queue.keys():
                    if self.fixed[id] == 0:
                        
                        self.history[id] = self.queue[id]
                        del self.queue[id]
                        self.queue[frame_id] = 1 + self.history[frame_id]
                        self.queue = {k:v for k, v in sorted(self.queue.items(), key=lambda item: item[1])}
                        self.fixed[frame_id] += 1
                        break
                else:
                    raise Exception("All items in queue are fixed")
            else:
                self.fixed[frame_id] += 1
                self.queue[frame_id] = 1 + self.history[frame_id]
                self.queue = {k:v for k, v in sorted(self.queue.items(), key=lambda item: item[1])}
                self.history[frame_id] = 0
            return False

    def unfix(self, frame_id):
        self.fixed[frame_id] -= 1


if __name__ == "__main__":
    # raise Exception
    hit_rate = []
    for file in ["ftrace_combined.csv"]:        
        for p in [TwoQ, RR, FIFO, LRU, LFU]:
            hit_rate = []
            for i in range(6, 400):
                try:
                    policy = p(i)
                    simulator = Simulator(file)
                    simulator.simulate(policy)
                    hit_rate.append(float(simulator.hits)/simulator.total)
                except Exception as e:
                    hit_rate.append(0)

            print(hit_rate)
            plt.scatter(range(6, 400), hit_rate, label=policy.name, s=3)

        plt.title("Buffer Size versus Hit Rate")
        plt.xlabel("Buffer Size (# Video Frames)")
        plt.ylabel("Hit Rate (proportion)")
        
        plt.legend()
        plt.savefig(f'{file[:-4]}-results')
        plt.clf()
        break