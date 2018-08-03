from PyQt4.QtCore import *
from PyQt4.QtGui import *
import time

class LeftDockWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.parent = parent

        self.initUI()

    def initUI(self):
        VBOX = QVBoxLayout(self)

        # viewer
        self.groupViewer = QGroupBox("Viewer")
        vboxviewer = QVBoxLayout()

        self.check_trajectory = QCheckBox("trajectory", self)
        self.check_trajectory.toggled.connect(self.show_trajectory_child)
        vboxviewer.addWidget(self.check_trajectory)

        self.button_noselect = QPushButton("Release", self)
        self.button_noselect.clicked.connect(self.release_select)
        self.button_noselect.setEnabled(False)
        vboxviewer.addWidget(self.button_noselect)

        self.check_showbone = QCheckBox("Show Bone", self)
        self.check_showbone.toggled.connect(self.check_showboneChanged)
        vboxviewer.addWidget(self.check_showbone)

        self.groupViewer.setLayout(vboxviewer)
        VBOX.addWidget(self.groupViewer)

        # video mode
        self.groupVideoMode = QGroupBox("Video")
        vboxvideomode = QVBoxLayout()

        hbox = QHBoxLayout()
        self.labelfps = QLabel()
        self.labelfps.setText("FPS")
        hbox.addWidget(self.labelfps)

        self.spinFps = QSpinBox()
        self.spinFps.setMinimum(0)
        self.spinFps.setMaximum(10000)
        self.spinFps.setValue(self.parent.fps)
        self.spinFps.valueChanged.connect(self.spinFpsChanged)
        hbox.addWidget(self.spinFps)
        vboxvideomode.addLayout(hbox)

        # play, stop button
        hbox2 = QHBoxLayout()
        self.buttonPlay = QPushButton("Play")
        self.buttonPlay.clicked.connect(self.play)
        hbox2.addWidget(self.buttonPlay)

        self.buttonStop = QPushButton("Stop")
        self.buttonStop.clicked.connect(self.stop)
        hbox2.addWidget(self.buttonStop)
        vboxvideomode.addLayout(hbox2)

        self.groupVideoMode.setLayout(vboxvideomode)
        VBOX.addWidget(self.groupVideoMode)

        self.setLayout(VBOX)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateVideo)

    # clicked trajectory checkbox
    def show_trajectory_child(self):
        if self.check_trajectory.isChecked():
            self.parent.show_trajectory()
        else:
            self.parent.trajectory_line = None
            self.parent.draw(fix=True)

    # clicked release button
    def release_select(self):
        self.parent.now_select = -1
        self.button_noselect.setEnabled(False)
        self.parent.trajectory_line = None
        self.parent.draw(fix=True)

    def play(self):
        self.timer.start(1000.0/self.parent.fps) # mm

    def stop(self):
        self.timer.stop()

    def updateVideo(self):
        if self.parent.frame < self.parent.frame_max:
            self.parent.frame += 1
            self.parent.sliderSetValue(self.parent.frame)
            self.parent.draw(fix=True)
        else:
            self.stop()

    # clicked show bone
    #def showbone(self):
    #    self.parent.setbone()
    #    self.parent.draw(fix=True)

    def check_showboneChanged(self):
        self.parent.draw(fix=True)

    def spinFpsChanged(self):
        self.parent.fps = int(self.spinFps.text())