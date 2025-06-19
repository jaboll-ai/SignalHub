from enum import Enum
import logging
import cv2
import numpy as np
from .misc import get_nested_key
from .galyQT import (
    qt_add_canvas_entry,
    qt_display_canvas,
    qt_add_layer_entry,
    qt_get_layer_visibility,
)
from uuid import uuid4

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GALYCommand(Enum):
    LAYER = (1,)
    LINE = (2,)
    CANVAS = (3,)
    PUTTEXT = (4,)
    BLIT = (5,)
    SET_LAYER_AFFINE_MAPPING = (6,)
    MAHALANOBIS = (7,)
    CIRLCE = (8,)


class GALYBuffer:
    def __init__(self, command: GALYCommand, **kwargs):
        self.command = command
        self.kwargs = kwargs


class GALY:
    def __init__(self):
        self.commands = []
        pass

    def layer(self, name, alwaysVisible = False):
        assert type(name) == str, "Layer name must be a string"
        self.commands.append(GALYBuffer(GALYCommand.LAYER, name=name, alwaysVisible=alwaysVisible))

    def set_layer_affine_mapping(self, mapping):
        assert type(mapping) == np.ndarray, "Mapping must be a numpy matrix"
        assert mapping.shape[0] == 2, "Mapping must be a 2x3 matrix"
        assert mapping.shape[1] == 3, "Mapping must be a 2x3 matrix"
        self.commands.append(
            GALYBuffer(GALYCommand.SET_LAYER_AFFINE_MAPPING, mapping=mapping)
        )

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

    def circle(self, org, radius, color, thickness=1, **kwargs):
        if type(org) == tuple or type(org) == list:
            org = np.array([[org[0], org[1]]])

          

        assert type(org) == np.ndarray, "Origin must be a numpy array"
        org = org.reshape(1, -1)

        assert org.shape[0] == 1, "Origin must be 1x2 matrix"
        assert org.shape[1] == 2, "Origin must be 1x2 matrix"

        assert type(radius) == int, "Radius must be integer"

        assert type(color) == tuple, "Color must be a tuple (R, G, B)"
        assert len(color) == 3, "Color must be a tuple (R, G, B)"

        kwargs["center"] = org
        kwargs["radius"] = radius
        kwargs["thickness"] = thickness
        kwargs["color"] = color

        self.commands.append(GALYBuffer(GALYCommand.CIRLCE, **kwargs))

    def mahalanobis(self, org, covariance, color, scale=1.0, thickness=1, **kwargs):
        if type(org) == tuple:
            org = np.array([[org[0], org[1]]])

        assert type(org) == np.ndarray, "Origin must be a numpy array"
        org = org.reshape(1, -1)

        assert org.shape[0] == 1, "Origin must be 1x2 matrix"
        assert org.shape[1] == 2, "Origin must be 1x2 matrix"

        assert type(scale) == float, "Scale must be float"

        assert type(covariance) == np.ndarray, "Covariance must be a numpy array"
        assert covariance.shape[0] == 2, "Covariance must be 2x2 matrix"
        assert covariance.shape[1] == 2, "Covariance must be 2x2 matrix"

        if type(color) == np.ndarray and color.shape[0] == 3:
            color = color.reshape(-1)
            color = (color[0], color[1], color[2])

        assert type(color) == tuple, "Color must be a tuple (R, G, B)"
        assert len(color) == 3, "Color must be a tuple (R, G, B)"

        kwargs["org"] = org
        kwargs["scale"] = scale
        kwargs["covariance"] = covariance
        kwargs["color"] = color
        kwargs["thickness"] = thickness

        self.commands.append(GALYBuffer(GALYCommand.MAHALANOBIS, **kwargs))

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

        if type(pt1) == np.ndarray:
            pt1 = pt1.reshape(-1)
            pt1 = (pt1[0], pt1[1])

        if type(pt2) == list and len(pt2) == 2:
            pt2 = (pt2[0], pt2[1])

        if type(pt2) == np.ndarray:
            pt2 = pt2.reshape(-1)
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
            qt_add_canvas_entry(name, shape)

        galyCanvases[name] = canvas


currentLayer, mainLayer = None, None
galyLayers = {}
layerMappings = {}
currentVisibility = True


def apply_layer_mapping(pt):
    if currentLayer in layerMappings.keys():
        if type(pt) is np.ndarray:
            pt = pt.reshape(-1)
            
        mapping = layerMappings[currentLayer]
        pt = np.float64(np.array([[pt[0], pt[1], 1.0]]).T)
        #print(mapping.dtype, pt.dtype)

        pt = mapping @ pt

    return (int(np.round(pt[0])), int(np.round(pt[1])))


def process_layer(kwargs, otherData):
    global currentLayer, mainLayer, galyLayers, currentVisibility

    name = kwargs["name"]
    alwaysVisible = kwargs["alwaysVisible"]

    currentLayer = name

    if name not in galyLayers:
        if mainLayer is None:
            mainLayer = name

        currentVisibility = qt_add_layer_entry(name, alwaysVisible)
        galyLayers[currentLayer] = currentVisibility
    else:
        currentVisibility = qt_get_layer_visibility(currentLayer)


def process_line(kwargs, otherData):
    if currentCanvas is None:
        logger.error("GALY: No canvas set on line command")
        return

    if not currentVisibility:
        return

    kwargs = kwargs.copy()
    kwargs["pt1"] = apply_layer_mapping(kwargs["pt1"])
    kwargs["pt2"] = apply_layer_mapping(kwargs["pt2"])

    cv2.line(currentCanvas.image, **kwargs)


def process_putText(kwargs, otherData):
    if currentCanvas is None:
        logger.error("GALY: No canvas set on putText command")
        return

    if not currentVisibility:
        return

    kwargs = kwargs.copy()
    kwargs["org"] = apply_layer_mapping(kwargs["org"])
    cv2.putText(currentCanvas.image, **kwargs)


def process_blit(kwargs, otherData):
    if currentCanvas is None:
        logger.error("GALY: No canvas set on blit command")
        return

    if not currentVisibility:
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


def process_set_layer_affine_mapping(kwargs, otherData):
    if currentLayer is None:
        logger.error("GALY: No layer set on set_layer_affine_mapping command")
        return

    mapping = kwargs["mapping"]
    layerMappings[currentLayer] = mapping


def process_mahalanobis(kwargs, otherData):
    if currentCanvas is None:
        logger.error("GALY: No canvas set on mahalanobis command")
        return

    if not currentVisibility:
        return

    chol = np.linalg.cholesky(kwargs["covariance"])
    mu = kwargs["org"].reshape(-1, 1)
    old_point = None
    for rad in np.linspace(0.0, 2.0 * np.pi, 120):
        pt = mu + kwargs["scale"] * chol @ np.array([[np.cos(rad), np.sin(rad)]]).T
        pt = apply_layer_mapping(pt)

        if old_point is not None:
            cv2.line(
                currentCanvas.image, pt, old_point, kwargs["color"], kwargs["thickness"]
            )

        old_point = pt


def process_circle(kwargs, otherData):
    if currentCanvas is None:
        logger.error("GALY: No canvas set on mahalanobis command")
        return

    if not currentVisibility:
        return

    kwargs = kwargs.copy()
    kwargs["center"] = apply_layer_mapping(kwargs["center"])

    cv2.circle(currentCanvas.image, **kwargs)


galyCommandTable = {
    GALYCommand.CANVAS: process_canvas,
    GALYCommand.LAYER: process_layer,
    GALYCommand.LINE: process_line,
    GALYCommand.PUTTEXT: process_putText,
    GALYCommand.BLIT: process_blit,
    GALYCommand.SET_LAYER_AFFINE_MAPPING: process_set_layer_affine_mapping,
    GALYCommand.MAHALANOBIS: process_mahalanobis,
    GALYCommand.CIRLCE: process_circle,
}


def process_galy_stream(stream: GALY, otherData: dict):
    global currentCanvas, mainCanvas, currentLayer, mainLayer

    # Reset canvas and layer (do not silently fall over if a previous module has changed it)
    currentCanvas = mainCanvas
    currentLayer = mainLayer

    # Iterate over all commands
    for buffer in stream.commands:
        if buffer.command in galyCommandTable:
            galyCommandTable[buffer.command](buffer.kwargs, otherData)
        else:
            logger.critical(
                f"GALY Command {buffer.command} requested but not implemented"
            )
            exit()


def remove_galy_streams(data):
    remaining_signals = {}
    for key, stream in data.items():
        if not isinstance(stream, GALY):
            remaining_signals[key] = stream

    return remaining_signals


def make_galy_streams_unique(data):
    signals = {}
    for key, stream in data.items():
        if not isinstance(stream, GALY):
            signals[key] = stream
        else:
            unique_key = uuid4().hex
            signals[unique_key] = stream

    return signals


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
        qt_display_canvas(canvas.image, canvasName if canvas != mainCanvas else None, canvas.image.shape)

    return remaining_signals
