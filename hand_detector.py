import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from SignalHub.galy import GALY
from SignalHub.misc import get_nested_key
from SignalHub.module import Module
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
mp_hand = mp.tasks.vision.HandLandmarksConnections

def _darken_color(color, factor):
    return tuple(int(c * factor) for c in color)

def draw_hand_landmarks(hand_landmarks, handedness, galy: GALY):
    lm = {
        "thumb":         {"color": (0,0,255)},
        "index_finger":  {"color": (0,255,0)},
        "middle_finger": {"color": (255,0,0)},
        "ring_finger":   {"color": (0,255,255)},
        "pinky_finger":  {"color": (255,0,255)},
        "palm":          {"color": (200,200,200)},
    }
    x = np.inf
    y = np.inf
    for key in lm.keys():
        pts = set()
        for conn in getattr(mp_hand, f"HAND_{key.upper()}_CONNECTIONS"):
            start = (hand_landmarks[conn.start].x,
                    hand_landmarks[conn.start].y)
            end = (hand_landmarks[conn.end].x,
                hand_landmarks[conn.end].y)
            x = min(x, start[0], end[0])
            y = min(y, start[1], end[1])
            galy.line(start, end, _darken_color(lm[key]["color"], 0.7), 2)
            pts.update([conn.start, conn.end])
        for pt in pts:
            galy.circle((hand_landmarks[pt].x, hand_landmarks[pt].y), 5, (255,255,255), 1)
            galy.circle((hand_landmarks[pt].x, hand_landmarks[pt].y), 4, lm[key]["color"], -1)
    # galy.putText(f"{handedness[0].display_name}", (x, y), color=(1.0, 1.0, 1.0), fontScale=2, fontFace=cv2.FONT_HERSHEY_PLAIN, thickness=2)


class HandDetector(Module):
    def __init__(self, outputSignal="detector"):
        super().__init__(
            inputSignals=["config", "webcam"],
            outputSchema={"type": "object", "properties": {outputSignal: {}}},
            name="Hand Detector",
        )

        self.outputSignal = outputSignal

    def start(self, data):
        base_options = python.BaseOptions(model_asset_path='data/hand_landmarker.task')
        options = vision.HandLandmarkerOptions(base_options=base_options,
                                            num_hands=2)
        self.detector = vision.HandLandmarker.create_from_options(options)
        return {}

    def step(self, data):
        arr: np.ndarray = data["webcam"]
        image = mp.Image(mp.ImageFormat.SRGB, cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))
        detection_result = self.detector.detect(image)
        hand_landmarks_list = detection_result.hand_landmarks
        handedness_list = detection_result.handedness
        galy = GALY()
        galy.canvas("Main", (0,0), (0.0, 0.0, 0.0))
        galy.layer("Hands")
        galy.set_layer_affine_mapping(np.array([
            [get_nested_key("config.webcam.width", data), 0.0, 0.0],
            [0.0, get_nested_key("config.webcam.height", data), 0.0]
        ]))
        for idx in range(len(hand_landmarks_list)): # 1 or 2 Hands
            hand_landmarks = hand_landmarks_list[idx]
            handedness = handedness_list[idx]
            draw_hand_landmarks(hand_landmarks, handedness, galy)
        return {self.outputSignal: detection_result, "galy": galy}
        # return {self.outputSignal: image, "galy": galy}

    def stop(self, data):
        pass
