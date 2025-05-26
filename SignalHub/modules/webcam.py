import numpy as np
from SignalHub import Module, get_nested_key, GALY
import cv2

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Webcam(Module):
    def __init__(self, outputSignal="webcam"):
        super().__init__(
            inputSignals=["config"],
            outputSchema={"type": "object", "properties": {outputSignal: {}}},
            name="Webcam Capture"
        )

        self.outputSignal = outputSignal

    def start(self, data):
        # Open a video capture
        self.cam = cv2.VideoCapture(
            get_nested_key("config.webcam.deviceIndex", data) or 0
        )

        return { }

    def step(self, data):
        # Read next image from the Webcam
        _, frame = self.cam.read()

        # Retrieve the target shape from the configuration file
        W, H = (
            get_nested_key("config.webcam.width", data) or frame.shape[1],
            get_nested_key("config.webcam.height", data) or frame.shape[0],
        )
        shape = (int(W), int(H))

        # Retrieve the target data type
        dtype = get_nested_key("config.webcam.dtype", data) or "float32"

        # Rescale to target size
        image = cv2.resize(frame, shape)

        # Make it float32 if requested
        if dtype == "float32" or dtype == "f32":
            image = np.float32(image / 255.0)
        elif dtype == "uint8" or dtype == "u8":
            pass # Nothing to do here
        else:
            logger.critical(f"Webcam: Unknown Target Datatype {dtype}")
            exit()

        galy = GALY()
        galy.canvas("Main", shape, (0.0, 0.0, 0.0))
        galy.blit("webcam", (0, 0))

        galy.canvas("Extra", shape, (0.0, 0.0, 0.0))
        galy.blit("webcam", (0, 0))

        return {self.outputSignal: image, "galy": galy}

    def stop(self, data):
        pass
