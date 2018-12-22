from PyQt4.QtCore import *
from PyQt4.QtGui import *
import time
import numpy as np
import os, sys

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

        self.labelBoneFile = QLabel()
        self.labelBoneFile.setText("default")
        vboxviewer.addWidget(self.labelBoneFile)

        self.button_readBoneFile = QPushButton("Read Joint File", self)
        self.button_readBoneFile.clicked.connect(self.clickReadBoneFile)
        vboxviewer.addWidget(self.button_readBoneFile)

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

        # edit mode
        self.groupEditMode = QGroupBox("Edit")
        vboxeditmode = QVBoxLayout()

        self.prevLabel = QLabel()
        self.prevLabel.setText("No selected")
        vboxeditmode.addWidget(self.prevLabel)

        self.comboBoxNewLabel = QComboBox()
        #self.comboBoxNewLabel.addItems(self.parent.Points)
        vboxeditmode.addWidget(self.comboBoxNewLabel)

        self.checkOverwritefile = QCheckBox("Overwrite File", self)
        self.checkOverwritefile.setChecked(True)
        vboxeditmode.addWidget(self.checkOverwritefile)

        self.buttonExchange = QPushButton("Exchange")
        self.buttonExchange.clicked.connect(self.exchange)
        self.buttonExchange.setEnabled(False)
        vboxeditmode.addWidget(self.buttonExchange)

        self.groupEditMode.setLayout(vboxeditmode)
        self.groupEditMode.setEnabled(False)
        VBOX.addWidget(self.groupEditMode)

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
        self.prevLabel.setText("No selected")
        self.comboBoxNewLabel.clear()
        self.buttonExchange.setEnabled(False)
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

    def clickReadBoneFile(self):
        filters = "JOINT files(*.joint)"
        if os.name == 'nt':
            # windows
            bonepath = QFileDialog.getOpenFileName(self, 'load file', '', filters)
        else:
            # ubuntu
            bonepath = QFileDialog.getOpenFileName(self, 'load file', '', filters)

        try:
            if bonepath:
                self.parent.read_bonefile(bonepath)
                self.labelBoneFile.setText(bonepath.split(os.path.sep)[-1])

        except Exception as e:
            err = e.args

            QMessageBox.critical(self, "Caution", '{0} is invalid file.\nError code is {1}'.format(bonepath, err))
            self.labelBoneFile.setText('default')

    def check_showboneChanged(self):
        self.parent.draw(fix=True)

    def spinFpsChanged(self):
        self.parent.fps = int(self.spinFps.text())

    def setEditMode(self, label):
        self.prevLabel.setText(label)
        self.comboBoxNewLabel.clear()
        point = [p for p in self.parent.Points if p != label]
        self.comboBoxNewLabel.addItems(point)

    def exchange(self):
        prevind = self.parent.Points.index(str(self.prevLabel.text()))
        newind = self.parent.Points.index(str(self.comboBoxNewLabel.currentText()))

        indlist = np.arange(self.parent.x.shape[1])
        indlist[prevind] = newind
        indlist[newind] = prevind

        self.parent.x = self.parent.x[:, indlist]
        self.parent.y = self.parent.y[:, indlist]
        self.parent.z = self.parent.z[:, indlist]

        self.parent.calcBone()
        self.parent.draw(fix=True)

        if self.checkOverwritefile.isChecked():
            self.parent.rewriteTrc()
        else:
            filters = "TRC files(*.trc)"
            # selected_filter = "CSV files(*.csv)"
            savepath, extension = QFileDialog.getSaveFileNameAndFilter(self, 'Save file', './data/trc', filters)

            savepath = str(savepath)
            extension = str(extension)
            if savepath != "":
                if savepath[-4:] != '.trc':
                    savepath += '.trc'

                self.parent.rewriteTrc(path=savepath)