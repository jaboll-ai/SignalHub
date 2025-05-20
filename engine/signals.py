import numpy as np

def orNone(other):
  def check(x):
    if x is None:
      return True
    
    return other(x)
  
  return check


def npTensor(shape):
  def checkTensor(x):
    assert type(x) is np.ndarray, "Signal must be a numpy array but is " + str(type(x))
    for index, dim in enumerate(shape):
      if dim > 0:
        assert x.shape[index] == dim, "Tensor shape " + str(x.shape) + " does not match definition " + str(shape)

  return checkTensor

def rgbImage(width, height):
  return npTensor((height, width, 3))