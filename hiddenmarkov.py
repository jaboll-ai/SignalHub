from collections import deque
import cv2
import numpy as np

from SignalHub.galy import GALY
from SignalHub.misc import get_nested_key
from SignalHub.module import Module
from HMMBasedRecognition import HMMBasedRecognition

class Preprocessor(Module):
    def __init__(self, outputSignal="preprocessor"):
        super().__init__(
            inputSignals=["config", "detector"],
            outputSchema={"type": "object", "properties": {outputSignal: {}}},
            name="Preprocessor",
        )

        self.outputSignal = outputSignal
        self.lastState = None
        self.lastVelo = None
        self.emptyCounter = 0

    def start(self, data):
        return {}

    def step(self, data):
        landmarks = data["detector"].hand_landmarks
        has_hand = len(landmarks) > 0
        # ---- No hand detected ----
        if not has_hand:
            return {self.outputSignal: None}
        if self.lastState is None:
            self.lastState = landmarks
            return {self.outputSignal: None}

        dx = landmarks[0][0].x - self.lastState[0][0].x
        dy = landmarks[0][0].y - self.lastState[0][0].y

        self.lastVelo = (dx, dy)
        self.lastState = landmarks

        return {self.outputSignal: self.lastVelo}

    def stop(self, data):
        pass

class HMMModule(Module):
    def __init__(self, outputSignal="markov", **kwargs):
        super().__init__(
            inputSignals=["config", "preprocessor"],
            outputSchema={"type": "object", "properties": {outputSignal: {}}},
            name="Hidden Markov",
            **kwargs
        )

        self.outputSignal = outputSignal
        self.buffer = deque(maxlen=20)

    def start(self, data):
        self.hmm = HMMBasedRecognition.load("data/hmm.pkl")
        return {}

    def step(self, data):
        threshold = 40.0
        print(data["preprocessor"])
        if data["preprocessor"] is None:
            if len(self.buffer) > 0:
                self.buffer.popleft()
            return {}
        self.buffer.append(data["preprocessor"])
        if len(self.buffer)<10:
            return {}
        arr = np.asarray(self.buffer)
        decision = self.hmm.decision_function(arr)[0]
        best_idx = decision.argmax()
        best_score = decision[best_idx]
        best_label = self.hmm.classes_[best_idx]
        print(best_label)
        if best_score < threshold:
            return {}
        galy = GALY()
        galy.layer("Decision")
        galy.set_layer_affine_mapping(np.array([
            [get_nested_key("config.webcam.width", data), 0.0, 0.0],
            [0.0, get_nested_key("config.webcam.height", data), 0.0]
        ]))
        galy.putText("{:.2f}".format(best_score), (0, 0.1), color=(0, 0, 1), fontScale=2, fontFace=cv2.FONT_HERSHEY_SIMPLEX, thickness=2)
        galy.putText(best_label, (0, 0.2), color=(0, 0, 1), fontScale=2, fontFace=cv2.FONT_HERSHEY_SIMPLEX, thickness=2)
        return {self.outputSignal: {"best_label": best_label, "best_score": best_score}, "galy": galy}

    def stop(self, data):
        pass


