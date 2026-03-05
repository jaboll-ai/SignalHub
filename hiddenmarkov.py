from collections import deque
import cv2
import numpy as np

from SignalHub.galy import GALY
from SignalHub.misc import get_nested_key, bgr
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
        self.lastStates = deque(maxlen=4)
        self.prevVelo = None
        self.prevSpeed = None

    def start(self, data):
        self.aspect = get_nested_key("config.webcam.height", data) / get_nested_key("config.webcam.width", data)
        self.finger_idx = get_nested_key("config.preprocessor.finger_idx", data)
        return {}

    def step(self, data):
        landmarks = data["detector"].hand_landmarks
        has_hand = len(landmarks) > 0
        # ---- No hand detected ----
        if not has_hand:
            self.lastStates.clear()
            return {self.outputSignal: None}
        # store current frame
        self.lastStates.append(landmarks)
        # need at least 2 frames
        if len(self.lastStates) < 2:
            return {self.outputSignal: None}

        xs = [lm[0][self.finger_idx].x for lm in self.lastStates]
        ys = [lm[0][self.finger_idx].y for lm in self.lastStates]
        t = np.arange(len(xs))
        dx = np.polyfit(t, xs, 1)[0]
        dy = np.polyfit(t, ys, 1)[0] * self.aspect
        speed = np.sqrt(dx**2 + dy**2)
        if self.prevVelo is None:
            dtheta = 0
        else:
            dtheta = np.atan2(np.cross(self.prevVelo, (dx, dy)), np.dot(self.prevVelo, (dx, dy)))
        if self.prevSpeed is None:
            dspeed = 0
        else:
            dspeed = speed - self.prevSpeed
        self.prevVelo = (dx, dy)
        self.prevSpeed = speed
        return {self.outputSignal: (dx, dy, dtheta, speed, dspeed*1000)}

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
        self.lost = 0

    def start(self, data):
        self.hmm = HMMBasedRecognition.load("data/hmm.pkl")
        self.buffer = deque(maxlen=get_nested_key("config.markov.buffer_size", data))
        self.max_lost = get_nested_key("config.markov.max_lost", data)
        self.min_steps = get_nested_key("config.markov.min_steps", data)
        return {}

    def step(self, data):
        if data["preprocessor"] is None:
            self.lost += 1
            if self.lost > self.max_lost:
                self.buffer.clear()
            return {}
        self.lost = 0
        self.buffer.append(data["preprocessor"])
        if len(self.buffer) < self.min_steps:
            return {}
        arr = np.asarray(self.buffer)
        decision = self.hmm.decision_function(arr)[0]
        best_idx = decision.argmax()
        best_score = decision[best_idx]
        best_label = self.hmm.classes_[best_idx]
        galy = GALY()
        galy.layer("Decision")
        galy.set_layer_affine_mapping(np.array([
            [get_nested_key("config.webcam.width", data), 0.0, 0.0],
            [0.0, get_nested_key("config.webcam.height", data), 0.0]
        ]))
        galy.putText("{:.2f}".format(best_score), org=(0, 0.1), color=bgr("#8349C6"), fontScale=2, fontFace=cv2.FONT_HERSHEY_SIMPLEX, thickness=2)
        galy.putText(best_label, org=(0, 0.2), color=bgr("#8349C6"), fontScale=1.2, fontFace=cv2.FONT_HERSHEY_SIMPLEX, thickness=2)
        return {self.outputSignal: {"best_label": best_label, "best_score": best_score}, "galy": galy}

    def stop(self, data):
        pass


