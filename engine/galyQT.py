import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QAction, QFileDialog
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from PyQt5.QtCore import Qt, QTimer
import cv2
import numpy as np


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
        file_menu = menubar.addMenu('File')

        open_action = QAction('Open Image', self)
        open_action.triggered.connect(self.open_image)
        file_menu.addAction(open_action)

        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

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

