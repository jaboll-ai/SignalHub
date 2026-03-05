from collections import deque

import numpy as np

from SignalHub.galy import GALY
from SignalHub.misc import bgr, get_nested_key
from SignalHub.module import Module


class FingerPaint(Module):
    def __init__(self, outputSignal="fingerpaint"):
        super().__init__(
            inputSignals=["config", "detector", "preprocessor"],
            outputSchema={"type": "object", "properties": {outputSignal: {}}},
            name="Finger Paint",
        )

        self.outputSignal = outputSignal
        self.trail = deque(maxlen=40)

    def start(self, data):
        self.finger_idx = get_nested_key("config.preprocessor.finger_idx", data)
        return {}

    def step(self, data):
        detector = data["detector"]
        pre = data["preprocessor"]

        galy = GALY()
        galy.layer("FingerPaint")
        galy.set_layer_affine_mapping(np.array([
            [get_nested_key("config.webcam.width", data), 0.0, 0.0],
            [0.0, get_nested_key("config.webcam.height", data), 0.0]
        ]))

        if len(detector.hand_landmarks) == 0:
            self.trail.clear()
            return {}

        lm = detector.hand_landmarks[0][self.finger_idx]
        x, y = lm.x, lm.y
        self.trail.append((x, y))
        for i in range(len(self.trail)-1):
            galy.line(self.trail[i], self.trail[i+1], color=bgr("#3EC1FF"), thickness=2)
        if pre is not None:
            dx, dy, _, speed, *_ = pre
            scale = speed*100
            end = (x + dx * scale, y + dy * scale)
            galy.line((x, y), end, color=bgr("#FFAA00"), thickness=3)

        return {self.outputSignal: {"pos": (x, y)}, "galy": galy}

    def stop(self, data):
        pass