import numpy as np
from engine import Engine, Module, EngineMode, GALY
from modules import ConfigParser
import numpy as np
import argparse

class TerminateAfter(Module):
    def __init__(self, count):
        self.name = "TerminateAfter"
        self.counter = count
        self.count = 0
        pass

    def start(self, data):
        self.count = 0
        pass

    def step(self, data):
        self.count += 1
        if self.count >= self.counter:
            return { }, EngineMode.TERMINATE

        return { }

    def stop(self, data):
        pass


class RandomPositionSender(Module):
    def __init__(self):
        self.name = f"Random Position Sender"
        pass

    def start(self, data):
        pass

    def step(self, data):
        W, H = data["config"]["video"]["width"], data["config"]["video"]["height"]
        x, y = np.random.uniform(0.0, W, 2), np.random.uniform(0.0, H, 2)

        return { 
            "startPoint": (int(x[0]), int(y[0])), 
            "endPoint": (int(x[1]), int(y[1]))
        }

    def stop(self, data):
        pass

class GALYDrawer(Module):
    def __init__(self):
        self.name = f"GALY Drawer"

    def step(self, data):
        galy = GALY()
        shape = (data["config"]["video"]["width"], data["config"]["video"]["height"])
        galy.canvas("Main Canvas", shape, (1.0, 1.0, 1.0))
        galy.line(data["startPoint"], data["endPoint"], (0.0, 0.0, 0.0), 2)

        return { "xyz": galy }

class Receiver(Module):
    def __init__(self):
        self.name = f"Receiver"
        pass

    def start(self, data):
        pass

    def step(self, data):
        print(data)
        return {}

    def stop(self, data):
        pass


parser = argparse.ArgumentParser("Example Program")
parser.add_argument("--mode", action="store", default="replay", required=True)
parser.add_argument("--video.width", required=False)
modules = [
    ConfigParser(parser),
    TerminateAfter(5),
    RandomPositionSender(),
    GALYDrawer(),
    Receiver(),
]



engine = Engine(modules=modules, signals={})
signals = engine.run({})
