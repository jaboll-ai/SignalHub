from enum import Enum
import logging
import cv2
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GALYCommand(Enum):
  LAYER = 1,
  LINE = 2,
  CANVAS = 3

class GALYBuffer:
  def __init__(self, command: GALYCommand, **kwargs):
    self.command = command
    self.kwargs = kwargs

class GALY:
  def __init__(self):
    self.commands = []
    pass

  
  def canvas(self, name, shape, color):
    assert type(name) == str, "Name must be a string"
    
    assert type(shape) == tuple, "Shape must be a tuple (W, H)"
    assert len(shape) == 2, "Shape must be a tuple (W, H)"

    assert type(color) == tuple, "Color must be a tuple (R, G, B)"
    assert len(color) == 3, "Color must be a tuple (R, G, B)"

    self.commands.append(GALYBuffer(GALYCommand.CANVAS, name=name, shape=shape, color=color))

  def line(self, pt1, pt2, color, thickness=1):
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

    self.commands.append(GALYBuffer(GALYCommand.LINE, pt1=pt1, pt2=pt2, color=color, thickness=thickness))

class GALYCanvas:
  def __init__(self, shape, color):
    self.image = np.zeros((shape[0], shape[1], 3)) 
    self.color = color

  def reset(self):
    self.image[:, :, 0] = self.color[0]
    self.image[:, :, 1] = self.color[1]
    self.image[:, :, 2] = self.color[2]

currentCanvas = None

galyCanvases = {

}

def process_canvas(kwargs):
  global currentCanvas, galyCanvases
  
  name, shape, color = kwargs["name"], kwargs["shape"], kwargs["color"]

  if name in galyCanvases:
    currentCanvas = galyCanvases[name]
  else:
    canvas = GALYCanvas(shape, color)
    canvas.reset()
    currentCanvas = canvas

def process_layer(kwargs):
  pass

def process_line(kwargs):
  if currentCanvas is None:
    logger.error("GALY: No canvas set to draw line")
    return
  
  #pt1, pt2, color, thickness = kwargs["startPoint"], kwargs["endPoint"], kwargs["color"], kwargs["thickness"]
  cv2.line(currentCanvas.image, **kwargs)

  pass

galyCommandTable = {
  GALYCommand.CANVAS: process_canvas,
  GALYCommand.LAYER: process_layer,
  GALYCommand.LINE: process_line
}



def process_galy_stream(stream: GALY):
  # Do not silently overwrite layers previously set, to 
  # currentLayer = None
  # Iterate over all commands
  
  for buffer in stream.commands:
    if buffer.command in galyCommandTable:
      galyCommandTable[buffer.command](buffer.kwargs)
    else:
      logger.critical(f"GALY Command {buffer.command} requested but not implemented")
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
  for canvas in galyCanvases:
    canvas.reset()

  # Iterate all signals, find GALY streams
  remaining_signals = {}
  for key, stream in data.items():
    if not isinstance(stream, GALY):
      remaining_signals[key] = stream
      continue

    process_galy_stream(stream)

  # Now show all canvases
  for canvasName, canvas in galyCanvases.items():
    print("Showing ", canvasName)
    cv2.imshow(canvasName, canvas.image)

  # WaitKey (TODO: Needs to be done different such that the engine remains control on what happens)
  cv2.waitKey(0)


  return remaining_signals
