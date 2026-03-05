import numpy as np
from SignalHub import (
    Engine,
    Module,
    EngineMode,
    GALY,
    get_nested_key,
    ConfigParser,
    Webcam,
    Recorder,
    Replay,
)
import numpy as np
import argparse
import cv2

from fingerpainter import FingerPaint
from hand_detector import HandDetector
from hiddenmarkov import Preprocessor, HMMModule


class TerminateAfter(Module):
    def __init__(self, count):
        super().__init__(name="Terminate After")
        self.counter = count
        self.count = 0
        pass

    def start(self, data):
        self.count = 0
        return {}

    def step(self, data):
        self.count += 1
        if self.count >= self.counter:
            return {}, EngineMode.TERMINATE

        return {}

    def stop(self, data):
        pass


class ImageSender(Module):
    def __init__(self):
        super().__init__(
            outputSchema={
                "type": "object",
                "properties": {"image": {}, "A": {"exclusive": False}},
            }
        )

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

        # print(f"Step {self.counter}")
        self.counter += 1
        return {"image": self.image, "galy": galy, "A": 1}

    def stop(self, data):
        pass


class Clock(Module):
    def __init__(self):
        super().__init__(outputSchema={"type": "object", "properties": {"A": {}}})

    def start(self, data):
        self.counter = 0
        return {}

    def step(self, data):
        galy = GALY()

        galy.canvas("Clock", (640, 480), (0.0, 0.0, 0.0))

        rad = -np.pi / 2.0 + 5.0 * self.counter / 99.0 * np.pi * 2.0
        x0, x1 = 320, int(320.0 + 160.0 * np.cos(rad))
        y0, y1 = 240, int(240.0 + 160.0 * np.sin(rad))
        galy.layer("Minute Hand")
        galy.line((x0, y0), (x1, y1), (1.0, 0.0, 0.0), 2)

        rad2 = -np.pi / 2.0 + self.counter / 99.0 * np.pi * 2.0
        x0, x1 = 320, int(320.0 + 80.0 * np.cos(rad2))
        y0, y1 = 240, int(240.0 + 80.0 * np.sin(rad2))

        galy.layer("Hour Hand")
        galy.line((x0, y0), (x1, y1), (1.0, 0.0, 0.0), 2)

        self.counter += 1
        return {"clock": galy, "A": 3}

    def stop(self, data):
        pass


parser = argparse.ArgumentParser("Example Program")
parser.add_argument("--mode", action="store", default="none")
parser.add_argument("--recorder.file", action="store")
parser.add_argument("--engine.singlestep", action="store_true", default=False)
parser.add_argument("--webcam.width", required=False)
modules = [ConfigParser(parser), Webcam(), HandDetector(), Preprocessor(), TerminateAfter(600)]
modules.extend([HMMModule(), FingerPaint()])
engine = Engine(modules=modules, signals={})
signals = engine.run({})
