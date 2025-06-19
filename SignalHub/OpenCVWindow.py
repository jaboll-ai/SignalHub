from PyQt5.QtWidgets import (
    QMainWindow,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QSettings, QTimer
import cv2
import numpy as np


class OpenCVWindow(QMainWindow):
    def __init__(self, mainWindow, title, applicationName="SignalHub", settings=None, shape=None):
        super().__init__()

        self.mainWindow = mainWindow
        self.setWindowTitle(title)

        # Create a central widget for the window
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Create a layout for placing widgets
        self.layout = QVBoxLayout()

        # Create a label to display the image
        self.image_label = QLabel(self)
        self.layout.addWidget(self.image_label)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.central_widget.setLayout(self.layout)

        # Centralized settings
        if settings is None:
            self.settings = QSettings("DMUSoftware", applicationName)
        else:
            self.settings = settings

        if shape is None:
            shape = (640, 480)
        self.targetWidth, self.targetHeight = shape[0], shape[1]
        #self.setMinimumSize(400, 300)  # Set a custom minimum size smaller than layout

        # Load the window position and size from settings
        self.load_window_settings()

    def closeEvent(self, event):
        self.save_window_settings()
        if self.mainWindow is not None:
            self.mainWindow.on_close_canvas(self.windowTitle())

        event.accept()

    def save_window_settings(self):
        """
        Save the window's position and size using QSettings.
        """
        key = self.windowTitle() + "/pos"
        self.settings.setValue(key, self.pos())  # Save the window position

    def load_window_settings(self):
        """
        Load the window's position and size from QSettings.
        """
        key = self.windowTitle() + "/pos"
        if self.settings.contains(key):
            self.move(self.settings.value(key))  # Restore the window position

    def update_image(self, image):
        # Convert the image from BGR to RGB
        # /image = np.uint8(cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX))
        image = np.uint8(image * 255.0)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Convert the RGB image to a QImage
        h, w, ch = image.shape
        if self.targetWidth != w or self.targetHeight != h:
            w, h = self.targetWidth, self.targetHeight
            image = cv2.resize(image, (w, h))

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
        pass

    def keyPressEvent(self, event):
        if self.mainWindow is not None:
            self.mainWindow.keyPressEvent(event)
