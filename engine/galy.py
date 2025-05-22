from enum import Enum
import logging
import cv2
import numpy as np
from .misc import get_nested_key
from .galyQT import qt_update_image, qt_add_canvas_entry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GALYCommand(Enum):
    LAYER = (1,)
    LINE = (2,)
    CANVAS = (3,)
    PUTTEXT = (4,)
    BLIT = (5,)


class GALYBuffer:
    def __init__(self, command: GALYCommand, **kwargs):
        self.command = command
        self.kwargs = kwargs


class GALY:
    def __init__(self):
        self.commands = []
        pass

    def blit(self, source, offset):
        if type(offset) == list and len(offset) == 2:
            offset = (offset[0], offset[1])

        assert type(source) == str, "Source must be string"
        assert type(offset) == tuple, "Shape must be a tuple (W, H)"
        assert len(offset) == 2, "Shape must be a tuple (W, H)"

        self.commands.append(GALYBuffer(GALYCommand.BLIT, source=source, offset=offset))

    def canvas(self, name, shape, color):
        assert type(name) == str, "Name must be a string"

        assert type(shape) == tuple, "Shape must be a tuple (W, H)"
        assert len(shape) == 2, "Shape must be a tuple (W, H)"

        assert type(color) == tuple, "Color must be a tuple (R, G, B)"
        assert len(color) == 3, "Color must be a tuple (R, G, B)"

        self.commands.append(
            GALYBuffer(GALYCommand.CANVAS, name=name, shape=shape, color=color)
        )

    def putText(
        self,
        text,
        org,
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=1.0,
        color=(1.0, 1.0, 1.0),
        thickness=1,
        **kwargs,
    ):
        kwargs["text"] = text
        kwargs["org"] = org
        kwargs["fontFace"] = fontFace
        kwargs["fontScale"] = fontScale
        kwargs["color"] = color
        kwargs["thickness"] = thickness

        self.commands.append(GALYBuffer(GALYCommand.PUTTEXT, **kwargs))

    def line(self, pt1, pt2, color, thickness=2, **kwargs):
        if type(pt1) == list and len(pt1) == 2:
            pt1 = (pt1[0], pt1[1])

        if type(pt2) == list and len(pt2) == 2:
            pt2 = (pt2[0], pt2[1])

        assert type(pt1) == tuple, "startPoint must be a tuple (W, H)"
        assert len(pt1) == 2, "startPoint must be a tuple (W, H)"

        assert type(pt2) == tuple, "endPoint must be a tuple (W, H)"
        assert len(pt2) == 2, "endPoint must be a tuple (W, H)"

        assert type(color) == tuple, "color must be a tuple (R, G, B)"
        assert len(color) == 3, "color must be a tuple (R, G, B)"

        kwargs["pt1"] = pt1
        kwargs["pt2"] = pt2
        kwargs["color"] = color
        kwargs["thickness"] = thickness

        self.commands.append(GALYBuffer(GALYCommand.LINE, **kwargs))


class GALYCanvas:
    def __init__(self, shape, color):
        self.image = np.zeros((shape[0], shape[1], 3))
        self.color = color

    def reset(self):
        self.image[:, :, 0] = self.color[0]
        self.image[:, :, 1] = self.color[1]
        self.image[:, :, 2] = self.color[2]


currentCanvas, mainCanvas = None, None

galyCanvases = {}


def process_canvas(kwargs, otherData):
    global currentCanvas, galyCanvases, mainCanvas

    name, shape, color = kwargs["name"], kwargs["shape"], kwargs["color"]

    if name in galyCanvases:
        currentCanvas = galyCanvases[name]
    else:
        shape = (shape[1], shape[0], 3)
        canvas = GALYCanvas(shape, color)
        canvas.reset()
        currentCanvas = canvas

        if mainCanvas is None:
            mainCanvas = canvas
        else:
            qt_add_canvas_entry(name)       

        galyCanvases[name] = canvas


def process_layer(kwargs, otherData):
    pass


def process_line(kwargs, otherData):
    if currentCanvas is None:
        logger.error("GALY: No canvas set on line command")
        return

    cv2.line(currentCanvas.image, **kwargs)


def process_putText(kwargs, otherData):
    if currentCanvas is None:
        logger.error("GALY: No canvas set on putText command")
        return

    cv2.putText(currentCanvas.image, **kwargs)


def process_blit(kwargs, otherData):
    if currentCanvas is None:
        logger.error("GALY: No canvas set on blit command")
        return

    source, offset = kwargs["source"], kwargs["offset"]

    image = get_nested_key(source, otherData)
    if image is None:
        logger.error(f"GALY: Cannot find blit source {source} in available signals")
        return

    if not isinstance(image, np.ndarray):
        logger.error(f"GALY: Blit source must be a numpy array")
        return

    x0, y0, w, h = int(offset[0]), int(offset[1]), image.shape[1], image.shape[0]
    x1, y1 = x0 + w, y0 + h

    # Do the actual blit
    currentCanvas.image[y0:y1, x0:x1] = image


galyCommandTable = {
    GALYCommand.CANVAS: process_canvas,
    GALYCommand.LAYER: process_layer,
    GALYCommand.LINE: process_line,
    GALYCommand.PUTTEXT: process_putText,
    GALYCommand.BLIT: process_blit,
}


def process_galy_stream(stream: GALY, otherData: dict):
    global currentCanvas, mainCanvas

    # Reset canvas and layer (do not silently fall over if a previous module has changed it)
    currentCanvas = mainCanvas

    # Iterate over all commands
    for buffer in stream.commands:
        if buffer.command in galyCommandTable:
            galyCommandTable[buffer.command](buffer.kwargs, otherData)
        else:
            logger.critical(
                f"GALY Command {buffer.command} requested but not implemented"
            )
            exit()

    pass


def remove_galy_streams(data):
    remaining_signals = {}
    for key, stream in data.items():
        if not isinstance(stream, GALY):
            remaining_signals[key] = stream

    return remaining_signals


def process_galy(data):
    # Reset all canvases
    for canvas in galyCanvases.values():
        canvas.reset()

    # Iterate all signals, find GALY streams
    remaining_signals = {}
    for key, stream in data.items():
        if not isinstance(stream, GALY):
            remaining_signals[key] = stream
            continue

        process_galy_stream(stream, data)

    # Now show all canvases
    for canvasName, canvas in galyCanvases.items():
        if canvas == mainCanvas:
          qt_update_image(canvas.image)
        else:
          cv2.imshow(canvasName, canvas.image)

    # WaitKey (TODO: Needs to be done different such that the engine remains control on what happens)
    key = cv2.waitKey(1)
    if key == 27:
        exit()

    return remaining_signals
