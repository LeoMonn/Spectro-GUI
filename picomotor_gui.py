#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Picomotor worker and standalone window.

This module is adapted from the archived Picomotor GUI so it can be plugged into the
current master/worker repository without changing the underlying motion logic.
"""

from PyQt5.QtWidgets import QLineEdit, QLabel, QAction, QPushButton, QMainWindow, QMessageBox
from PyQt5.QtWidgets import QWidget, QApplication, QDesktopWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt5.QtGui import QFont, QIcon
import sys
from datetime import date

try:
    import picomotor5
except:
    print('module non charge picomotor5')
    picomotor5 = None


today = date.today()
jour = "%02d" % (today.day)
mois = "%02d" % (today.month)
annee = str(today.year)


class Fenetre(QMainWindow):

    def __init__(self):
        super(Fenetre, self).__init__()
        self.resize(300, 200)
        self.center()
        self.initUI()

    def initUI(self):
        self.Create_Layout()
        self.statusBar().showMessage('Ready')
        self.menu()
        self.setWindowTitle('Platines Picomotor')

    def Create_Layout(self):
        self.CentralWidget = Main(self)
        self.setCentralWidget(self.CentralWidget)

    def menu(self):
        menubar = self.menuBar()
        menubar.clear()
        fileMenu = menubar.addMenu('&File')

        exitAct = QAction(QIcon('exit.png'), '&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(self.close)
        fileMenu.addAction(exitAct)
        self.CentralWidget.Picomotor.MenuBar(menubar)

    def updateStatusBar(self, string):
        self.statusBar().showMessage(string)

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            'Message',
            'Are you sure to quit?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.CentralWidget.close()
            event.accept()
        else:
            event.ignore()

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)


class Main(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.Layout()
        self.connect()

    def Layout(self):
        self.MainLayout = QVBoxLayout()
        self.Picomotor = Picomotor(self)
        self.MainLayout.addWidget(self.Picomotor)
        self.setLayout(self.MainLayout)

    def connect(self):
        return

    def close(self):
        self.Picomotor.close()


class Picomotor(QWidget):
    """Worker widget exposing manual x/y/z sample moves through the Picomotor."""

    def __init__(self, parent):
        super().__init__(parent)

        self.font_title = QFont()
        self.font_title.setPointSize(10)
        self.font_title.setBold(True)
        self.font_title.setWeight(75)

        self.font_text = QFont()
        self.font_text.setPointSize(8)
        self.font_text.setBold(False)
        self.font_text.setWeight(50)

        self.force_dummy = False
        self.m = 'Dummy'
        self.connect_hardware()

        self.Layout()
        self.connect()

    def Layout(self):
        self.samplemovementlayout = QHBoxLayout()
        self.sample_left_layout = QGridLayout()
        self.sample_right_layout = QGridLayout()

        self.labels = ['Up', 'Down', 'Left', 'Right', 'Focus']
        self.positions = [(0, 1), (2, 1), (1, 0), (1, 2), (1, 1)]
        for i, lab in enumerate(self.labels):
            bouton = QPushButton(lab)
            self.sample_left_layout.addWidget(bouton, self.positions[i][0], self.positions[i][1])
            bouton.clicked.connect(self.picomotor)

        self.x_step_label = QLabel('pas en x')
        self.x_step_edit = QLineEdit('0.1')
        self.y_step_label = QLabel('pas en y')
        self.y_step_edit = QLineEdit('0.1')
        self.focus_step_label = QLabel('pas en focus')
        self.focus_step_edit = QLineEdit('0.1')

        self.sample_right_layout.addWidget(self.x_step_edit, 0, 0)
        self.sample_right_layout.addWidget(self.x_step_label, 0, 1)
        self.sample_right_layout.addWidget(self.y_step_edit, 1, 0)
        self.sample_right_layout.addWidget(self.y_step_label, 1, 1)
        self.sample_right_layout.addWidget(self.focus_step_edit, 2, 0)
        self.sample_right_layout.addWidget(self.focus_step_label, 2, 1)

        self.samplemovementlayout.addLayout(self.sample_left_layout)
        self.samplemovementlayout.addLayout(self.sample_right_layout)
        self.samplemovementlayout.insertStretch(-1)
        self.setLayout(self.samplemovementlayout)

    def connect(self):
        return

    def MenuBar(self, Menu):
        picomotor_menu = Menu.addMenu('&Picomotor')

        force_dummy_act = QAction('Force Dummy Mode', self)
        force_dummy_act.setCheckable(True)
        force_dummy_act.setChecked(self.force_dummy)
        force_dummy_act.setStatusTip('Block hardware motion and keep Picomotor actions in dummy mode')
        force_dummy_act.triggered.connect(self.set_force_dummy)
        picomotor_menu.addAction(force_dummy_act)

        reconnect_act = QAction('Reconnect Hardware', self)
        reconnect_act.setStatusTip('Try to reconnect the Picomotor controller')
        reconnect_act.triggered.connect(self.reconnect_hardware)
        picomotor_menu.addAction(reconnect_act)

    def connect_hardware(self):
        self.close_hardware()
        try:
            if picomotor5 is None:
                raise RuntimeError('picomotor5 unavailable')
            self.m = picomotor5.PMOTOR()
            self.m.open_PMotor()
        except Exception:
            self.m = 'Dummy'

    def close_hardware(self):
        if self.m == 'Dummy':
            return
        for method_name in ('stop_Pmotor', 'close_PMotor'):
            method = getattr(self.m, method_name, None)
            if callable(method):
                try:
                    method()
                except Exception:
                    pass
                break
        self.m = 'Dummy'

    def close(self):
        self.close_hardware()

    def set_force_dummy(self, checked):
        self.force_dummy = checked

    def reconnect_hardware(self):
        if self.force_dummy:
            return
        self.connect_hardware()

    def camera_worker(self):
        return getattr(self.parent(), 'Camera', None)

    def camera_is_dummy(self):
        camera = self.camera_worker()
        return bool(camera and hasattr(camera, 'is_dummy_mode') and camera.is_dummy_mode())

    def camera_has_live_feed(self):
        camera = self.camera_worker()
        return bool(camera and hasattr(camera, 'has_live_camera') and camera.has_live_camera())

    def apply_dummy_move(self, index, delta):
        camera = self.camera_worker()
        if camera is None:
            return False
        camera_thread = getattr(camera, 'camera_thread', None)
        if camera_thread is None:
            return False
        # Keep the historical manip0.6 convention so the synthetic camera image reacts the same
        # way as before when the user presses the Picomotor arrows in dummy mode.
        if index in (0, 1):
            camera_thread.posx += delta
        elif index in (2, 3):
            camera_thread.posy += delta
        elif index == 4:
            camera_thread.posz += delta
        return True

    def send_hardware_move(self, index, delta):
        if index in (0, 1):
            self.m.ech(y=delta)
        elif index in (2, 3):
            self.m.ech(x=delta)
        elif index == 4:
            self.m.ech(z=delta)

    def picomotor(self):
        sign = [1, -1, -1, 1, 1]
        move = [
            self.y_step_edit.text(),
            self.y_step_edit.text(),
            self.x_step_edit.text(),
            self.x_step_edit.text(),
            self.focus_step_edit.text(),
        ]
        btn = self.sender()
        if not isinstance(btn, QPushButton):
            return
        i = self.labels.index(btn.text())
        delta = sign[i] * float(move[i])

        if self.camera_is_dummy():
            if self.apply_dummy_move(i, delta):
                return

        # Without a real camera feed we deliberately avoid moving the real stages, because the
        # user would otherwise lose visual feedback and could damage the setup.
        if not self.camera_has_live_feed() and self.camera_worker() is not None:
            print('camera not ready: Picomotor move blocked')
            return

        if not self.force_dummy and self.m != 'Dummy':
            self.send_hardware_move(i, delta)
        else:
            print("picomotor dummy mode active")

    def autofocus(self):
        return


def main():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    prog = Fenetre()
    prog.show()
    app.exec_()


if __name__ == '__main__':
    main()
