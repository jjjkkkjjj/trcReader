import sys, os, random
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import csv

import math
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from leftdock import LeftDockWidget

class Data:
    def __init__(self):
        # configure
        self.fps = 500
        self.units = "mm"
        self.searchRange = 500

        self.now_select = -1
        self.frame = 0

        self.Points = ["head", "R_ear", "L_ear", "sternum", "C7", "R_rib", "L_rib", "R_ASIS", "L_ASIS", "R_PSIS",
                       "L_PSIS",
                       "R_frontshoulder", "R_backshoulder", "R_in_elbow", "R_out_elbow", "R_in_wrist", "R_out_wrist",
                       "R_hand",
                       "L_frontshoulder", "L_backshoulder", "L_in_elbow", "L_out_elbow", "D_UA?", "L_in_wrist",
                       "L_out_wrist",
                       "L_hand"]
        self.Line = [[0, 1], [0, 2], [1, 2], [7, 8], [8, 10], [9, 10], [7, 9], [7, 11], [8, 18], [9, 12], [10, 19],
                     [11, 12], [12, 19], [18, 19], [18, 11], [11, 13],
                     [12, 14], [13, 14], [13, 15], [14, 16], [15, 16], [15, 17], [16, 17], [18, 20], [19, 21], [20, 21],
                     [20, 23], [21, 24], [23, 24], [23, 25], [24, 25],
                     [3, 5], [3, 6], [5, 6]]
        pass

    def read_trcfile(self, path):
        with open(path, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader)
            next(reader)

            thirdLine = next(reader)
            self.fps = int(thirdLine[0])
            self.units = thirdLine[4]
            #self.frame_max = int(thirdLine[7])

            forthline = next(reader)
            self.joints = forthline[2::3]
            if self.joints[-1] == '':
                self.joints = self.joints[:-1]

            data = np.genfromtxt(f, delimiter='\t', skip_header=6, missing_values=' ')
            self.x = data[:, 2::3]
            self.y = data[:, 3::3]
            self.z = data[:, 4::3]
            self.frame_max = self.x.shape[0]

            self.bone1 = [[] for i in range(self.frame_max)]
            self.bone2 = [[] for i in range(self.frame_max)]
            for t in range(self.frame_max):
                for line in self.Line:
                    if np.isnan(self.x[t, line[0]]) or np.isnan(self.x[t, line[1]]):
                        continue
                    else:
                        self.bone1[t].append([self.x[t, line[0]], self.y[t, line[0]], self.z[t, line[0]]])
                        self.bone2[t].append([self.x[t, line[1]], self.y[t, line[1]], self.z[t, line[1]]])

class trcReader(QMainWindow, Data):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        Data.__init__(self)

        self.setWindowTitle('trcReader with matplotlib')
        self.create_menu()
        self.create_main_frame()
        self.setleftDock()
        self.filed = False
        self.xbutton = False
        self.ybutton = False
        self.zbutton = False

    def draw(self, fix=False):
        if self.filed:
            if fix:
                azim = self.axes.azim
                elev = self.axes.elev
                xlim = self.axes.get_xlim().copy()
                ylim = self.axes.get_ylim().copy()
                zlim = self.axes.get_zlim().copy()
                addlim = np.max([xlim[1] - xlim[0], ylim[1] - ylim[0], zlim[1] - zlim[0]])
                xlim[1] = xlim[0] + addlim
                ylim[1] = ylim[0] + addlim
                zlim[1] = zlim[0] + addlim
            # clear the axes and redraw the plot anew
            #
            self.axes.clear()
            plt.title('frame number=' + str(self.frame))
            self.axes.grid(self.grid_cb.isChecked())

            self.axes.set_xlabel('x')
            self.axes.set_ylabel('y')
            self.axes.set_zlabel('z')

            if fix:
                self.axes.set_xlim(xlim)
                self.axes.set_ylim(ylim)
                self.axes.set_zlim(zlim)
                self.axes.view_init(elev=elev, azim=azim)

            if self.trajectory_line is not None:
                self.axes.lines.extend(self.trajectory_line)

            self.scatter = [
                self.axes.scatter3D(self.x[self.frame, i], self.y[self.frame, i], self.z[self.frame, i], ".",
                                    color='blue', picker=5) for i in range(len(self.joints))]

            if self.now_select != -1:
                self.scatter[self.now_select] = self.axes.scatter3D(self.x[self.frame, self.now_select],
                                                                    self.y[self.frame, self.now_select],
                                                                    self.z[self.frame, self.now_select], ".",
                                                                    color='red', picker=5)

            if self.leftdockwidget.check_showbone.isChecked():
                for bone1, bone2 in zip(self.bone1[self.frame], self.bone2[self.frame]):
                    self.axes.plot([bone1[0], bone2[0]], [bone1[1], bone2[1]], [bone1[2], bone2[2]], "-",
                                   color="black")

            self.canvas.draw()


        else:
            self.axes.clear()
            self.axes.grid(self.grid_cb.isChecked())
            self.canvas.draw()

    def create_menu(self):
        # file
        self.file_menu = self.menuBar().addMenu("&File")

        input_action = self.create_action("&Input", slot=self.input_trcfile, shortcut="Ctrl+I", tip="Input csv file")
        self.add_actions(self.file_menu, (input_action,))

        output_action = self.create_action("&Output", slot=self.output, shortcut="Ctrl+O", tip="Output annotated csv file")
        self.add_actions(self.file_menu, (output_action,))

        quit_action = self.create_action("&Quit", slot=self.close, shortcut="Ctrl+Q", tip="Close the application")
        self.add_actions(self.file_menu, (None, quit_action))

        # help
        self.help_menu = self.menuBar().addMenu("&Help")
        about_action = self.create_action("&About", shortcut='F1', slot=self.show_about, tip='About the demo')
        self.add_actions(self.help_menu, (about_action,))

        # edit
        self.edit_menu = self.menuBar().addMenu("&Edit")

        nextframe_action = self.create_action("&Next", slot=self.nextframe, shortcut="Ctrl+N", tip="show next frame")
        self.add_actions(self.edit_menu, (nextframe_action,))

        previousframe_action = self.create_action("&Previous", slot=self.previousframe, shortcut="Ctrl+P", tip="show previous frame")
        self.add_actions(self.edit_menu, (previousframe_action,))

        #self.configuration_action = self.create_action("&Configuration", slot=self.configure, tip="Set configuration")
        #self.add_actions(self.edit_menu, (self.configuration_action,))

    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(self, text, slot=None, shortcut=None,
                      icon=None, tip=None, checkable=False,
                      signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action

    def input_trcfile(self):
        filters = "TRC files(*.trc)"
        if os.name == 'nt':
            # windows
            self.path = QFileDialog.getOpenFileName(self, 'load file', '', filters)
        else:
            # ubuntu
            self.path = QFileDialog.getOpenFileName(self, 'load file', '', filters)
        try:
            if self.path:
                self.read_trcfile(self.path)

            else:
                msg = """You should select .csv file!"""
                QMessageBox.about(self, "Caution", msg.strip())
                return False

            self.now_select = -1
            self.trajectory_line = None

            self.filed = True
            self.draw()

            self.slider.setEnabled(True)
            self.slider.setMaximum(self.frame_max - 1)
            self.slider.setMinimum(0)
            self.slider.setValue(self.frame)

            self.leftdock.setEnabled(True)

            self.groupxrange.setEnabled(True)
            self.groupyrange.setEnabled(True)
            self.groupzrange.setEnabled(True)

            return True

        except:
            return False

    def output(self):
        if self.filed:
            filters = "TRC files(*.trc)"
             #selected_filter = "CSV files(*.csv)"
            savepath, extension = QFileDialog.getSaveFileNameAndFilter(self, 'Save file', '', filters)

            savepath = str(savepath).encode()
            extension = str(extension).encode()
            #print(extension)
            if savepath != "":
                savepath += '.trc'
                with open(savepath, 'wb') as f:
                    f.write("PathType,4,(X/Y/Z),{0},\n".format(savepath))
                    f.write("DataRate,CameraRate,NumFrames,NumMarkers,Units,OrigDataRate,OrigDataStartFrame,OrigNumFrames,\n")
                    f.write("{0},{0},{1},{2},{3},{0},1,{1},\n".format(self.fps, self.frame_max + 1, len(self.Points), self.units))

                    line1 = "Frame#,Time,"
                    line2 = ",,"
                    for index, point in enumerate(self.Points):
                        line1 += "{0},,,".format(point)
                        line2 += "X{0},Y{0},Z{0},".format(index + 1)
                    line1 += ",\n"
                    line2 += ",\n"

                    f.write(line1)
                    f.write(line2)
                    f.write(",\n")

                with open(savepath, 'a') as f:
                    data = np.zeros((self.xnew.shape[0], self.xnew.shape[1]*3 + 2))
                    # frame
                    data[:, 0] = np.arange(1, self.frame_max + 1)
                    # time
                    data[:, 1] = np.arange(0, self.frame_max/float(self.fps), 1/float(self.fps))

                    # x
                    data[:, 2::3] = self.xnew
                    # y
                    data[:, 3::3] = self.ynew
                    # z
                    data[:, 4::3] = self.znew

                    np.savetxt(f, data, delimiter=',')

                QMessageBox.information(self, "Saved", "Saved to {0}".format(savepath))


    def show_about(self): # show detail of this application
        msg = """ A demo of using PyQt with matplotlib:

         * Use the matplotlib navigation bar
         * Add values to the text box and press Enter (or click "Draw")
         * Show or hide the grid
         * Drag the slider to modify the width of the bars
         * Save the plot to a file using the File menu
         * Click on a bar to receive an informative message
        """
        QMessageBox.about(self, "About the demo", msg.strip())

    def create_main_frame(self):
        self.main_frame = QWidget()

        # Create the mpl Figure and FigCanvas objects.
        # 5x4 inches, 100 dots-per-inch
        #
        self.dpi = 100
        self.fig = plt.figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)

        # Since we have only one plot, we can use add_axes
        # instead of add_subplot, but then the subplot
        # configuration tool in the navigation toolbar wouldn't
        # work.
        #
        self.axes = Axes3D(self.fig)

        # Bind the 'pick' event for clicking on one of the bars
        #
        self.canvas.mpl_connect('pick_event', self.onclick)
        self.canvas.setFocusPolicy(Qt.ClickFocus)
        self.canvas.setFocus()
        self.canvas.mpl_connect('key_press_event', self.onkey)
        self.canvas.mpl_connect('key_release_event', self.onrelease)
        # Create the navigation toolbar, tied to the canvas
        #
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)

        # Other GUI controls
        #
        self.grid_cb = QCheckBox("Show &Grid")
        self.grid_cb.setChecked(True)
        self.connect(self.grid_cb, SIGNAL('stateChanged(int)'), lambda: self.draw(fix=True))

        # x range selector
        self.groupxrange = QGroupBox("x")
        hboxX = QHBoxLayout()
        self.buttonXminus = QPushButton("<")
        self.buttonXminus.clicked.connect(lambda: self.rangeChanger("x", False))
        hboxX.addWidget(self.buttonXminus)

        self.buttonXplus = QPushButton(">")
        self.buttonXplus.clicked.connect(lambda: self.rangeChanger("x", True))
        hboxX.addWidget(self.buttonXplus)
        self.groupxrange.setLayout(hboxX)

        # y range selector
        self.groupyrange = QGroupBox("y")
        hboxY = QHBoxLayout()
        self.buttonYminus = QPushButton("<")
        self.buttonYminus.clicked.connect(lambda: self.rangeChanger("y", False))
        hboxY.addWidget(self.buttonYminus)

        self.buttonYplus = QPushButton(">")
        self.buttonYplus.clicked.connect(lambda: self.rangeChanger("y", True))
        hboxY.addWidget(self.buttonYplus)
        self.groupyrange.setLayout(hboxY)

        # z range changer
        self.groupzrange = QGroupBox("z")
        hboxZ = QHBoxLayout()
        self.buttonZminus = QPushButton("<")
        self.buttonZminus.clicked.connect(lambda: self.rangeChanger("z", False))
        hboxZ.addWidget(self.buttonZminus)

        self.buttonZplus = QPushButton(">")
        self.buttonZplus.clicked.connect(lambda: self.rangeChanger("z", True))
        hboxZ.addWidget(self.buttonZplus)
        self.groupzrange.setLayout(hboxZ)

        self.groupxrange.setEnabled(False)
        self.groupyrange.setEnabled(False)
        self.groupzrange.setEnabled(False)
        #
        # Layout with box sizers
        #
        hbox = QHBoxLayout()

        for w in [self.grid_cb, self.groupxrange, self.groupyrange, self.groupzrange]:
            hbox.addWidget(w)
            hbox.setAlignment(w, Qt.AlignVCenter)

        vbox = QVBoxLayout()
        self.setslider(vbox)
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addLayout(hbox)

        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)

    def onclick(self, event):
        if self.filed:
            ind = event.ind[0]
            x0, y0, z0 = event.artist._offsets3d
            self.now_select = np.where(self.x[self.frame] == x0[ind])[0][0]

            self.leftdockwidget.button_noselect.setEnabled(True)

            if self.leftdockwidget.check_trajectory.isChecked():
                self.show_trajectory()
                return

            self.draw(fix=True)

    def onrelease(self, event):
        if self.filed:
            if self.xbutton and event.key == '.':
                self.rangeChanger("x", True)
            elif self.xbutton and event.key == ',':
                self.rangeChanger("x", False)
            elif self.ybutton and event.key == '.':
                self.rangeChanger("y", True)
            elif self.ybutton and event.key == ',':
                self.rangeChanger("y", False)
            elif self.zbutton and event.key == '.':
                self.rangeChanger("z", True)
            elif self.zbutton and event.key == ',':
                self.rangeChanger("z", False)

            if event.key == 'x':
                self.xbutton = False
            elif event.key == 'y':
                self.ybutton = False
            elif event.key == 'z':
                self.zbutton = False

    def onkey(self, event):
        if self.filed:
            if event.key == ',' and self.frame != 0 and not self.xbutton and not self.ybutton and not self.zbutton:
                self.frame += -1
                self.sliderSetValue(self.frame)
            elif event.key == '.' and self.frame != self.frame_max and not self.xbutton and not self.ybutton and not self.zbutton:
                self.frame += 1
                self.sliderSetValue(self.frame)
            elif event.key == 'q':
                result = QMessageBox.warning(self, "Will you quit?",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if result == QMessageBox.Yes:
                    plt.close(event.canvas.figure)
                else:
                    pass
            elif event.key == 'x':
                self.xbutton = True
            elif event.key == 'y':
                self.ybutton = True
            elif event.key == 'z':
                self.zbutton = True

            self.draw(fix=True)
            """
            self.axes.clear()
            self.axes.grid(self.grid_cb.isChecked())
            plt.title('frame number=' + str(self.frame))
            for i in range(self.joints):
                self.scatter[i] = self.axes.scatter3D(self.x[self.frame][i], self.y[self.frame][i],
                                                      self.z[self.frame][i],
                                                      ".", color='blue', picker=5)
            self.canvas.draw()
            """
            #self.now_select = -1

    def nextframe(self):
        if self.filed:
            if self.frame != self.frame_max:
                self.frame += 1
                self.sliderSetValue(self.frame)

    def previousframe(self):
        if self.filed:
            if self.frame != self.frame_max:
                self.frame += -1
                self.sliderSetValue(self.frame)

    def rangeChanger(self, coordinates, plus):
        ticks = eval("self.axes.get_{0}ticks()".format(coordinates))
        if plus:
            width = ticks[1] - ticks[0]
        else:
            width = ticks[0] - ticks[1]

        lim = eval("self.axes.get_{0}lim()".format(coordinates))
        lim += width

        self.draw(fix=True)

        pass

    ###
    # UI
    ###
    # left dock
    def setleftDock(self):
        self.leftdock = QDockWidget(self)
        self.leftdock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.leftdock.setFloating(False)

        self.leftdockwidget = LeftDockWidget(self)
        self.leftdock.setWidget(self.leftdockwidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.leftdock)
        self.leftdock.setEnabled(False)

    def show_trajectory(self):
        if self.filed:
            if self.now_select != -1:
                x_trajectory = self.x.T
                y_trajectory = self.y.T
                z_trajectory = self.z.T

                self.trajectory_line = self.axes.plot(x_trajectory[self.now_select], y_trajectory[self.now_select],
                                               z_trajectory[self.now_select], color='red')
                self.draw(fix=True)

                return

        self.trajectory_line = None

    # slider
    def setslider(self, vbox):
        #
        # slider
        #
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider.valueChanged.connect(self.sliderValueChanged)

        vbox.addWidget(self.slider)

        #self.topdock = QDockWidget(self)
        #self.topdock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        #self.topdock.setFloating(False)

        #self.topdock.setWidget(self.slider)
        #self.addDockWidget(Qt.TopDockWidgetArea, self.topdock)

    def sliderValueChanged(self):
        self.frame = self.slider.value()
        self.draw(fix=True)

    def sliderSetValue(self, value):
        self.slider.setValue(value)


print("activate qt!")
app = QApplication(sys.argv)
form = trcReader()
form.show()
app.exec_()
