import numpy as np
from engine import Engine, Module

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
      return { "terminate": True }

    return { }

  def stop(self, data):
    pass


class Sender(Module):
  def __init__(self, signal):
    self.name = f"Sender ({signal})"
    self.signal = signal
    self.value = 0
    pass

  def start(self, data):
    pass

  def step(self, data):
    self.value += 1
    result = {
      self.signal: self.value
    }

    return result

  def stop(self, data):
    pass

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

modules = [
  TerminateAfter(100),
  Sender("A"),
  Sender("B"),
  Receiver()
]

engine = Engine(modules=modules, signals={})
signals = engine.run({})