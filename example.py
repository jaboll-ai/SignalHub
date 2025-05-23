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
        super().__init__(outputSchema={"type": "object", "properties": {"image": {}}})

    def start(self, data):
        self.shape = (640, 480)
        self.image = np.float32(
            cv2.resize(cv2.imread("./image.jpg") / 255.0, self.shape)
        )
        self.counter = 0

        return {}

    def step(self, data):
        galy = GALY()
        galy.canvas("Main", self.shape, (0.0, 0.0, 0.0))
        galy.blit("image", (0, 0))

        galy.canvas("Clock", self.shape, (0.0, 0.0, 0.0))

        rad = self.counter / 10.0 * np.pi
        x0, x1 = 320, int(320.0 + 160.0 * np.cos(rad))
        y0, y1 = 240, int(240.0 + 160.0 * np.sin(rad))
        galy.line((x0, y0), (x1, y1), (1.0, 0.0, 0.0), 2)

        rad2 = self.counter / 60.0 * np.pi
        x0, x1 = 320, int(320.0 + 80.0 * np.cos(rad2))
        y0, y1 = 240, int(240.0 + 80.0 * np.sin(rad2))

        galy.line((x0, y0), (x1, y1), (1.0, 0.0, 0.0), 2)

        print(f"Step {self.counter}")
        self.counter += 1
        return {"image": self.image, "galy": galy}

    def stop(self, data):
        pass


parser = argparse.ArgumentParser("Example Program")
parser.add_argument("--mode", action="store", default="replay", required=True)
parser.add_argument("--engine.singlestep", action="store_true", default=False)
parser.add_argument("--webcam.width", required=False)
modules = [ConfigParser(parser), ImageSender()]


engine = Engine(modules=modules, signals={})
signals = engine.run({})
