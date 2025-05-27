import sys
import logging
from PyQt5.QtWidgets import (
    QApplication,
    QAction,
    QStatusBar,
)
from PyQt5.QtCore import Qt, QTimer
from .OpenCVWindow import OpenCVWindow
from .engineSpeed import (
    EngineSpeed,
    handle_speed_initialization,
    get_speed_status_text,
    engineSpeedToMilliseconds,
)
from .misc import get_nested_key
from .OSMemory import get_memory_text


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ICON_NONCHECKED = None
# ICON_CHECKED = "icons/healthy.png"


class CanvasWindowData:
    def __init__(self, window, action):
        self.window = window
        self.action = action
        self.image = None


class MainWindow(OpenCVWindow):
    def __init__(self, engine, config):
        applicationName = get_nested_key("applicationame", config) or "SignalHub"
        print("Application Name: ", applicationName)

        super().__init__(None, "Main", applicationName=applicationName)

        self.singleStep = False

        self.create_menu_bar()
        self.engine = engine

        # Set up the status bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        # Set up a timer to periodically update the window
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step)  # Method to update image

        handle_speed_initialization(self, config)

    def update_status_bar_message(self):
        speedText = get_speed_status_text(self.engineSpeed)
        memoryText = get_memory_text()
        bufferText = self.engine.get_buffer_status_text()
        self.status_bar.showMessage(
            speedText + "           " + memoryText + "           " + bufferText
        )

    def change_simulation_speed(self, newSpeed):
        self.engineSpeed = newSpeed

        self.timer.stop()
        self.timer.start(engineSpeedToMilliseconds[self.engineSpeed])

        self.update_status_bar_message()

    def set_singleStep(self, newState):
        self.singleStep = newState
        if self.singleStep == False:
            self.timer.start(engineSpeedToMilliseconds[self.engineSpeed])
        else:
            self.timer.stop()

    def handleEscape(self):
        self.close()

    def handleEnter(self):
        self.set_singleStep(not self.singleStep)

    def handleSpace(self):
        if not self.singleStep:
            self.set_singleStep(True)
        else:
            self.step()

    def keyPressEvent(self, event):
        key = event.key()  # Get the key that was pressed

        if key == Qt.Key_Escape:
            self.handleEscape()
        elif key == Qt.Key_Enter or key == Qt.Key_Return:
            self.handleEnter()
        elif key == Qt.Key_Space or key == Qt.Key_Plus:
            self.handleSpace()
        elif key == Qt.Key_1:
            self.singleStep = False
            self.change_simulation_speed(EngineSpeed.SLOWEST)
        elif key == Qt.Key_2:
            self.singleStep = False
            self.change_simulation_speed(EngineSpeed.SLOW)
        elif key == Qt.Key_3:
            self.singleStep = False
            self.change_simulation_speed(EngineSpeed.NORMAL)
        elif key == Qt.Key_4:
            self.singleStep = False
            self.change_simulation_speed(EngineSpeed.FAST)
        elif key == Qt.Key_5:
            self.singleStep = False
            self.change_simulation_speed(EngineSpeed.FASTEST)
        elif key == Qt.Key_Minus:
            self.set_singleStep(True)
            self.engine.step_backward()
            self.update_status_bar_message()

    def closeEvent(self, event):
        self.save_window_settings()

        for data in self.canvasData.values():
            if data is not None:
                if data.window is not None:
                    data.window.save_window_settings()
                    data.window.close()

    def step(self):
        self.engine.step_forward()
        self.update_status_bar_message()

    def redraw_galy(self):
        self.engine.redraw_galy()
        self.update_status_bar_message()

    def create_menu_bar(self):
        menubar = self.menuBar()

        # File menu
        self.file_menu = menubar.addMenu("File")

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        self.file_menu.addAction(exit_action)

        # Canvas menu
        self.canvas_menu = menubar.addMenu("Canvas")
        self.canvasData = {}

        # Layer Menu
        self.layer_menu = menubar.addMenu("Layer")
        self.layerData = {}

    def display_canvas(self, name, image):
        if name not in self.canvasData:
            logger.critical(f"GALY: Unknown canvas to display: {name}")
            exit()

        data = self.canvasData[name]
        if data is None:
            return

        if data.window is not None:
            data.window.update_image(image)

        data.image = image

    def on_close_canvas(self, canvasName):
        self.canvasData[canvasName].action.setChecked(False)
        # self.canvasData[canvasName].action.setIcon(QIcon(ICON_NONCHECKED))

    def on_canvas_toggle(self):
        action = self.sender()  # Get the QAction that triggered the handler
        context = action.data()  # Retrieve the context data

        canvasName = context["canvasName"]

        if action.isChecked():  # If the action is checked (active)
            # action.setIcon(QIcon(ICON_CHECKED))

            if canvasName not in self.canvasData:
                self.canvasData[canvasName] = CanvasWindowData(
                    OpenCVWindow(self, canvasName, settings=self.settings), action
                )
            else:
                self.canvasData[canvasName].window = OpenCVWindow(
                    self, canvasName, settings=self.settings
                )
                self.canvasData[canvasName].window.update_image(
                    self.canvasData[canvasName].image
                )

            self.canvasData[canvasName].window.show()
        else:
            # action.setIcon(QIcon(ICON_NONCHECKED))
            self.canvasData[canvasName].window.close()
            self.canvasData[canvasName].window = None

    def add_canvas_entry(self, name):
        key = f"canvas/{name}"
        visibility = (
            self.settings.value(key, type=bool) if self.settings.contains(key) else True
        )

        canvas_action = QAction(name, self)
        canvas_action.setData({"canvasName": name})
        canvas_action.setCheckable(True)

        if visibility:
            self.canvasData[name] = CanvasWindowData(
                OpenCVWindow(self, name, settings=self.settings), canvas_action
            )
            self.canvasData[name].window.show()
        else:
            self.canvasData[name] = CanvasWindowData(None, canvas_action)

        canvas_action.setChecked(visibility)
        # canvas_action.setIcon(QIcon(ICON_CHECKED))

        canvas_action.triggered.connect(self.on_canvas_toggle)
        self.canvas_menu.addAction(canvas_action)

    def on_layer_toggle(self):
        action = self.sender()  # Get the QAction that triggered the handler
        context = action.data()  # Retrieve the context data

        layerName = context["layerName"]

        if action.isChecked():  # If the action is checked (active)
            # action.setIcon(QIcon(ICON_CHECKED))
            self.layerData[layerName] = True
        else:
            # action.setIcon(QIcon(ICON_NONCHECKED))
            self.layerData[layerName] = False

        key = f"layers/{layerName}"
        self.settings.setValue(key, self.layerData[layerName])

        self.redraw_galy()

    def add_layer_entry(self, name, alwaysVisible):
        if alwaysVisible:
            self.layerData[name] = True
            return True
        
        key = f"layers/{name}"
        visibility = (
            self.settings.value(key, type=bool) if self.settings.contains(key) else True
        )

        layer_action = QAction(name, self)
        layer_action.setData({"layerName": name})
        layer_action.setCheckable(True)
        self.layerData[name] = visibility
        layer_action.setChecked(visibility)
        # layer_action.setIcon(QIcon(ICON_CHECKED))

        layer_action.triggered.connect(self.on_layer_toggle)
        self.layer_menu.addAction(layer_action)

        return visibility


app, window = None, None


def qt_display_canvas(image, name=None):
    global window

    if name is not None:
        window.display_canvas(name, image)
    else:
        window.update_image(image)


def qt_add_canvas_entry(name):
    window.add_canvas_entry(name)


def qt_add_layer_entry(name, alwaysVisible):
    return window.add_layer_entry(name, alwaysVisible)


def qt_get_layer_visibility(name):
    return window.layerData.get(name, True)


def run_qt_eventloop(engine, config):
    global app, window

    app = QApplication(sys.argv)
    window = MainWindow(engine, config)

    window.show()  # Show the window
    app.exec_()  # Enter the event loop


def qt_quit():
    app.quit()
