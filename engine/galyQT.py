import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QAction, QFileDialog
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtCore import Qt, QTimer
import cv2
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


ICON_NONCHECKED = None
ICON_CHECKED = "icons/healthy.png"

class MainWindow(QMainWindow):
    def __init__(self, engineStepCallback):
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

        # Set up a timer to periodically update the window
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step)  # Method to update image
        self.timer.start(33) 

        self.create_menu_bar()
        self.engineStepCallback = engineStepCallback

    def step(self):
        self.engineStepCallback()
        
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

        self.canvas_visibility = {}

    def display_canvas(self, name, image):
        if name not in self.canvas_visibility:
            logger.critical(f"GALY: Unknown canvas to display: {name}")
            exit()

        if not self.canvas_visibility[name]:
            return
        
        cv2.imshow(name, image)

    def on_canvas_toggle(self):
        action = self.sender()  # Get the QAction that triggered the handler
        context = action.data()  # Retrieve the context data

        canvasName = context["canvasName"]

        if action.isChecked():  # If the action is checked (active)
            cv2.namedWindow(canvasName)
            action.setIcon(QIcon(ICON_CHECKED))
            self.canvas_visibility[canvasName] = True
        else:
            cv2.destroyWindow(canvasName)
            action.setIcon(QIcon(ICON_NONCHECKED))
            self.canvas_visibility[canvasName] = False

    def add_canvas_entry(self, name):
        canvas_action = QAction(name, self)
        canvas_action.setData({"canvasName": name})
        canvas_action.setCheckable(True)
        self.canvas_visibility[name] = True
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

def run_qt_eventloop(engineStepCallback):
    global app, window

    app = QApplication(sys.argv)
    window = MainWindow(engineStepCallback)

    window.show()  # Show the window
    app.exec_()  # Enter the event loop

def qt_update_image(image):
    global window
    window.update_image(image)

def qt_quit():
    app.quit()

