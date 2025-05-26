from enum import Enum
from PyQt5.QtCore import QTimer
from .misc import get_nested_key


class EngineSpeed(Enum):
    SLOWEST = (1,)
    SLOW = (2,)
    NORMAL = (3,)
    FAST = (4,)
    FASTEST = 5


engineSpeedToMilliseconds = {
    EngineSpeed.SLOWEST: 600,
    EngineSpeed.SLOW: 300,
    EngineSpeed.NORMAL: 80,
    EngineSpeed.FAST: 33,
    EngineSpeed.FASTEST: 1,
}

engineSpeedToText = {
    EngineSpeed.SLOWEST: "Slowest",
    EngineSpeed.SLOW: "Slow",
    EngineSpeed.NORMAL: "Normal",
    EngineSpeed.FAST: "Fast",
    EngineSpeed.FASTEST: "Realtime",
}


def handle_speed_initialization(window, config):
    singleStep = False
    speed = get_nested_key("engine.speed", config) or 3
    if speed == 0:
        speed = EngineSpeed.NORMAL
        singleStep = True
        window.set_singleStep(True)
    elif speed == 1:
        speed = EngineSpeed.SLOWEST
    elif speed == 2:
        speed = EngineSpeed.SLOW
    elif speed == 3:
        speed = EngineSpeed.NORMAL
    elif speed == 4:
        speed = EngineSpeed.FAST
    elif speed == 5:
        speed = EngineSpeed.FASTEST
    window.change_simulation_speed(speed)

    if (get_nested_key("engine.singlestep", config) == True) or (singleStep == True):
        window.set_singleStep(True)

        # If we start in single step mode right away, we still need to do the first step
        singleShotTimer = QTimer(window)
        singleShotTimer.singleShot(1, window.step)


def get_speed_status_text(engineSpeed):
    return f"Speed: {engineSpeedToText[engineSpeed]} ({engineSpeedToMilliseconds[engineSpeed]}ms)"
