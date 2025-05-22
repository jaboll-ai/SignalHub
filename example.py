import numpy as np
from engine import Engine, Module, EngineMode
from modules import ConfigParser

import argparse


class TerminateAfter(Module):
    def __init__(self, count):
        super().__init__()
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


class Sender(Module):
    def __init__(self, signal):
        super().__init__(outputSchema={
            "type": "object",
            "properties" : {
                signal : { "type": "integer" }
            },
            "required": [signal]
        })

        self.name = f"Sender ({signal})"
        self.signal = signal
        self.value = 0
        pass

    def start(self, data):
        pass

    def step(self, data):
        self.value += 1
        result = { self.signal: self.value }

        return result

    def stop(self, data):
        pass


class Receiver(Module):
    def __init__(self):
        super().__init__(inputSignals=["A", "B", "config.video.width", "other"])
        self.name = f"Receiver"
        pass

    def start(self, data):
        pass

    def step(self, data):
        print(data)
        return { "other": "passed" }

    def stop(self, data):
        pass


parser = argparse.ArgumentParser("Example Program")
parser.add_argument("--mode", action="store", default="replay", required=True)
parser.add_argument("--video.width", required=False)
modules = [
    ConfigParser(parser),
    TerminateAfter(5),
    Sender("A"),
    Sender("B"),
    Receiver(),
]


engine = Engine(modules=modules, signals={})
signals = engine.run({})
