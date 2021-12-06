
import queue
from collections import Counter 

import queue
from collections import Counter, OrderedDict
import random
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
        self.name = "First In First Out"
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
        self.name = "Least Recently Used"
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
        self.name = "Random Replacement"
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
        self.name = "Two Queue"
        self.size = buffer_size
        self.fifo = []
        self.fifo_fixed = Counter()
        self.lru = OrderedDict()
        self.lru_fixed = Counter()

    def fix(self, frame_id):
        if frame_id in self.lru:
            self.lru_fixed[frame_id] += 1
            self.lru.move_to_end(frame_id)
            return True
        ## Try to add to lru
        if frame_id in self.fifo:
            if len(self.lru) == self.size:
                for id in self.lru:
                    if self.lru_fixed[id] == 0:
                        del self.lru[id]
                        self.lru[frame_id] = None
                        self.lru_fixed[frame_id] += 1
                        break
                else:
                    raise Exception("All items in queue are fixed")
            else:
                self.lru_fixed[frame_id] = 1 + self.fifo_fixed[frame_id]
                self.lru[frame_id] = None
            self.fifo_fixed[frame_id] = 0
            return True
        ## Add to FIFO
        if len(self.fifo) == self.size:
            for id in self.fifo:
                if self.fifo_fixed[id] == 0:
                    self.fifo.remove(id)
                    self.fifo.append(frame_id)
                    self.fifo_fixed[frame_id] += 1
                    break
            else:
                raise Exception("All items in queue are fixed")
        else:
            self.fifo_fixed[frame_id] += 1
            self.fifo.append(frame_id)
        return False
        
    def unfix(self, frame_id):
        if self.fifo_fixed[frame_id] == 0:
            self.lru_fixed[frame_id] -= 1
        else:
            self.fifo_fixed[frame_id] -= 1
                


class LFU(Policy):
    def __init__(self, buffer_size):
        self.name = "Least Frequently Used"
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
    pass
    # raise Exception
    # hit_rate = []
    # for i in range(6, 400):
    #     try:
    #         policy = FIFO(i)
    #         simulator = Simulator('overall_trace.csv')
    #         simulator.simulate(policy)
    #         hit_rate.append(float(simulator.hits)/simulator.total)
    #     except Exception as e:
    #         print(e)
    #         print(i)
    #         hit_rate.append(0)

    # import matplotlib.pyplot as plt
    # print(hit_rate)
    # plt.scatter(range(6, 400), hit_rate)
    # plt.title("Buffer Size versus Hit Rate using FIFO")
    # plt.xlabel("Buffer Size (# Video Frames)")
    # plt.ylabel("Hit Rate (proportion)")

    # plt.savefig('results')

# raise Exception
    hit_rate = []
    for i in range(6, 400):
        try:
            policy = LRU(i)
            simulator = Simulator('ftrace_combined.csv')
            simulator.simulate(policy)
            hit_rate.append(float(simulator.hits)/simulator.total)
        except Exception as e:
            print(e)
            print(i)
            hit_rate.append(0)

    import matplotlib.pyplot as plt
    print(hit_rate)
    plt.scatter(range(6, 400), hit_rate)
    plt.title("Buffer Size versus Hit Rate using LRU")
    plt.xlabel("Buffer Size (# Video Frames)")
    plt.ylabel("Hit Rate (proportion)")

    plt.savefig('results')
