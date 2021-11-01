
import queue
from collections import Counter 

class Simulator:
    def __init__(self, filename):
        self.filename = filename
        itemList = []
        with open(filename, "r") as fp:
            lines = fp.readlines()
            for l in lines:
                itemList.append(Line(l.split(",")))
        self.lines = itemList
    
    def printTrace(self):
        for l in self.lines:
            l.printLine()

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
    def printLine(self):
        print(f"Frame Id: {self.frame_id}, { 'Fixed' if self.fix else 'Unfixed'}")

class Policy():

    def __init__(self):
        self.name = "BasePolicy"
    
    def fix(self, frame_id):
        raise NotImplementedError
        # return bool
    
    def unfix(self, frame_id):
        raise NotImplementedError
        # No Return

class FIFO(Policy):
    "Notice that things close to 0 are closer to being evicted"
    def __init__(self, buffer_size):
        self.name = "FIFOPolicy"
        self.size = buffer_size
        self.queue = []
        self.fixed = Counter()

    def fix(self, frame_id):
        self.fixed[frame_id] += 1
        if frame_id in self.queue:
            return True
        else:
            if len(self.queue) == self.size:
                for id in self.queue:
                    if self.fixed[id] == 0:
                        self.queue.remove(id)
                        self.queue.append(frame_id)
                        break
                else:
                    raise Exception("All items in queue are fixed")
            else:
                self.queue.append(frame_id)
            return False

    def unfix(self, frame_id):
        self.fixed[frame_id] -= 1

    def printQueue(self):
        for i in self.queue:
            print(f"Item: {i}, Fixed: {self.fixed[i]}\n")

# raise Exception
hit_rate = []
simulator = Simulator('new_trace.csv')
for i in range(6, 1025):
    try:
        policy = FIFO(i)
        simulator.simulate(policy)
        hit_rate.append(float(simulator.hits)/simulator.total)
    except Exception as e:
        hit_rate.append(0)

import matplotlib.pyplot as plt
print(hit_rate)
plt.scatter(range(6, 1025), hit_rate)
plt.title("Hit Rate (proportion) Versus Buffer Size (in Video Frames)")
plt.savefig('results')