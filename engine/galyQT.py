import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QAction, QDialog
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtCore import Qt, QSettings, QTimer
import cv2
import numpy as np
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ICON_NONCHECKED = None
ICON_CHECKED = "icons/healthy.png"

class CanvasWindowData:
    def __init__(self, window, action):
        self.window = window
        self.action = action
        self.image = None


class OpenCVWindow(QDialog):
    def __init__(self, mainWindow, title):
        super().__init__()

        self.mainWindow = mainWindow
        self.setWindowTitle(title)

        # Create a layout for placing widgets
        self.layout = QVBoxLayout()

        # Create a label to display the image
        self.image_label = QLabel(self)
        self.layout.addWidget(self.image_label)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        # Load the window position and size from settings
        self.load_window_settings()

    def closeEvent(self, event):
        self.save_window_settings()

        self.mainWindow.onCloseCanvas(self.windowTitle())
        event.accept()
    
    def save_window_settings(self):
        """
        Save the window's position and size using QSettings.
        """
        settings = QSettings("DMUSoftware", "SignalHub")  # You can replace with your application name
        key = self.windowTitle() + "/pos"
        settings.setValue(key, self.pos())  # Save the window position

    def load_window_settings(self):
        """
        Load the window's position and size from QSettings.
        """
        settings = QSettings("DMUSoftware", "SignalHub")  # You can replace with your application name
        key = self.windowTitle() + "/pos"
        if settings.contains(key):
            self.move(settings.value(key))  # Restore the window position


    def update_image(self, image):
        # Convert the image from BGR to RGB
        image = np.uint8(cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Convert the RGB image to a QImage
        h, w, ch = image.shape
        bytes_per_line = ch * w
        q_image = QImage(image.data, w, h, bytes_per_line, QImage.Format_RGB888)

        self.resize(h, w)  # Resize the main window to fit the image

        # Display the image in the label
        pixmap = QPixmap.fromImage(q_image)
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignCenter)  # Center the image in the label
        self.image_label.resize(w, h)

        self.adjustSize()  # This will resize the window to fit the content exactly
        QTimer.singleShot(0, self.set_fixed_size)
    
    def set_fixed_size(self):
        # Lock the window size after the layout has been updated
        self.setFixedSize(self.size())  # Lock the window size to the current size

    def keyPressEvent(self, event):
        self.mainWindow.keyPressEvent(event)
        
class MainWindow(QMainWindow):
    def __init__(self, engine):
        super().__init__()

        self.setWindowTitle("Main Image")
        self.setGeometry(100, 100, 800, 600)

        # Create a central widget for the window
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Create a layout for placing widgets
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Create a label to display the image
        self.image_label = QLabel(self)
        self.layout.addWidget(self.image_label)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.singleStep = False

        # Set up a timer to periodically update the window
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step)  # Method to update image
        self.timer.start(33) 

        self.create_menu_bar()
        self.engine = engine

        # Load the window position and size from settings
        self.load_window_settings()


    def set_singleStep(self, newState):
        self.singleStep = newState
        if self.singleStep == False:
            print("Starting timer")
            self.timer.start(33)
        else:
            print("Stopping timer")
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
        elif key == Qt.Key_Space:
            self.handleSpace()

        
    def closeEvent(self, event):
        self.save_window_settings()

        for window in self.canvasWindows.values():
            if window is not None:
                window.save_window_settings()
                window.close()

    def save_window_settings(self):
        """
        Save the window's position and size using QSettings.
        """
        settings = QSettings("DMUSoftware", "SignalHub")  # You can replace with your application name
        key = self.windowTitle() + "/pos"
        settings.setValue(key, self.pos())  # Save the window position

    def load_window_settings(self):
        """
        Load the window's position and size from QSettings.
        """
        settings = QSettings("DMUSoftware", "SignalHub")  # You can replace with your application name
        key = self.windowTitle() + "/pos"
        if settings.contains(key):
            self.move(settings.value(key))  # Restore the window position

    def step(self):
        self.engine.step_callback_from_qt()
        
    def open_image(self):
        pass
    
    def create_menu_bar(self):
        menubar = self.menuBar()

        # File menu
        self.file_menu = menubar.addMenu('File')

        open_action = QAction('Open Image', self)
        open_action.triggered.connect(self.open_image)
        self.file_menu.addAction(open_action)

        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        self.file_menu.addAction(exit_action)

        # Canvas menu
        self.canvas_menu = menubar.addMenu("Canvas")

        self.canvasData = {}

    def display_canvas(self, name, image):
        if name not in self.canvasData:
            logger.critical(f"GALY: Unknown canvas to display: {name}")
            exit()

        data = self.canvasData[name]
        if data is None:
            return
        
        data.window.update_image(image)
        data.image = image
           
    def onCloseCanvas(self, canvasName):
        self.canvasData[canvasName].action.setChecked(False)
        self.canvasData[canvasName].action.setIcon(QIcon(ICON_NONCHECKED))

    def on_canvas_toggle(self):
        action = self.sender()  # Get the QAction that triggered the handler
        context = action.data()  # Retrieve the context data

        canvasName = context["canvasName"]

        if action.isChecked():  # If the action is checked (active)
            action.setIcon(QIcon(ICON_CHECKED))

            if canvasName not in self.canvasData:
                self.canvasData[canvasName] = CanvasWindowData(OpenCVWindow(self, canvasName), action)
            else:
                self.canvasData[canvasName].window = OpenCVWindow(self, canvasName)
                self.canvasData[canvasName].window.update_image(self.canvasData[canvasName].image)

            self.canvasData[canvasName].window.show()
        else:
            #cv2.destroyWindow(canvasName)
            action.setIcon(QIcon(ICON_NONCHECKED))
            self.canvasData[canvasName].window.close()
            self.canvasData[canvasName].window = None

    

    def add_canvas_entry(self, name):
        canvas_action = QAction(name, self)
        canvas_action.setData({"canvasName": name})
        canvas_action.setCheckable(True)
        self.canvasData[name] = CanvasWindowData(OpenCVWindow(self, name), canvas_action)
        self.canvasData[name].window.show()
        canvas_action.setChecked(True)
        canvas_action.setIcon(QIcon(ICON_CHECKED))

        canvas_action.triggered.connect(self.on_canvas_toggle)
        self.canvas_menu.addAction(canvas_action)

    def update_image(self, image):
        # Convert the image from BGR to RGB
        image = np.uint8(cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Convert the RGB image to a QImage
        h, w, ch = image.shape
        bytes_per_line = ch * w
        q_image = QImage(image.data, w, h, bytes_per_line, QImage.Format_RGB888)

        self.resize(h, w)  # Resize the main window to fit the image

        # Display the image in the label
        pixmap = QPixmap.fromImage(q_image)
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignCenter)  # Center the image in the label
        self.image_label.resize(w, h)

        self.adjustSize()  # This will resize the window to fit the content exactly
        QTimer.singleShot(0, self.set_fixed_size)
    
    def set_fixed_size(self):
        # Lock the window size after the layout has been updated
        self.setFixedSize(self.size())  # Lock the window size to the current size

app, window = None, None

def qt_display_canvas(name, image):
    window.display_canvas(name, image)

def qt_add_canvas_entry(name):
    window.add_canvas_entry(name)

def run_qt_eventloop(engine):
    global app, window

    app = QApplication(sys.argv)
    window = MainWindow(engine)

    window.show()  # Show the window
    app.exec_()  # Enter the event loop

def qt_update_image(image):
    global window
    window.update_image(image)

def qt_quit():
    app.quit()

