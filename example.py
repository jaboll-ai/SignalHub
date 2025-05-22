import numpy as np
from engine import Engine, Module, EngineMode, GALY, get_nested_key
from modules import ConfigParser, Webcam
import numpy as np
import argparse
import cv2


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
            return {}, EngineMode.TERMINATE

        return {}

    def stop(self, data):
        pass

class ImageSender(Module):
    def __init__(self):
        super().__init__(outputSchema={
            "type": "object",
            "properties": {
                "image": { }
            }
        })

    def start(self, data):
        self.shape = (640, 480)
        self.image = np.float32(cv2.resize(cv2.imread("./image.jpg") / 255.0, self.shape))
        

    def step(self, data):
        galy = GALY()
        galy.canvas("Main", self.shape, (0.0, 0.0, 0.0))
        galy.blit("image", (0,0))
        print(".")
        return {
            "image": self.image,
            "galy": galy
        }

    def stop(self, data):
        pass

parser = argparse.ArgumentParser("Example Program")
parser.add_argument("--mode", action="store", default="replay", required=True)
parser.add_argument("--webcam.width", required=False)
modules = [ConfigParser(parser), TerminateAfter(20), ImageSender()]


engine = Engine(modules=modules, signals={})
signals = engine.run({})
