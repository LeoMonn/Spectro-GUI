#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 14 12:17:44 2018

@author: leonard
"""
##################################################################
###       import pour l'interface et autres fonctions       ######
##################################################################
from PyQt5.QtWidgets import QLineEdit,QLabel,QAction,QPushButton,QSpinBox, QComboBox, QSlider
from PyQt5.QtWidgets import QTextEdit,QCheckBox,QMessageBox,QFileDialog,QStyle
from PyQt5.QtWidgets import QMainWindow,QWidget,QApplication,QDesktopWidget,QGridLayout,QVBoxLayout,QHBoxLayout
from PyQt5.QtCore import pyqtSignal,Qt,QThread,pyqtSlot
from PyQt5.QtGui import QIcon, QFont
import pyqtgraph as pg
from functools import partial
import os, sys
import time
from datetime import date

import numpy as np
import numpy.random as npr

##################################################################
###       import pour le fonctionnement de la manip         ######
##################################################################

try:
    import aravis
except:
    print('camera non chargée')

today=date.today()
jour="%02d" %(today.day)
mois="%02d" %(today.month)
annee=str(today.year)

class Fenetre (QMainWindow):
    
    def __init__(self):
        super(Fenetre,self).__init__()
        self.resize(1000, 800)
        self.center()
        self.initUI() 
    
    def initUI(self):    
        self.Create_Layout()
        self.statusBar().showMessage('Ready')        
        self.menu()
        self.setWindowTitle('Camera')    

    def Create_Layout(self):
        
        self.CentralWidget = Main(self)
        self.setCentralWidget(self.CentralWidget)       

    def menu(self):
        menubar=self.menuBar()
        fileMenu = menubar.addMenu('&File')
                
        #########################################
        ##           Menu File                 ##
        #########################################
        exitAct = QAction(QIcon('exit.png'),'&Exit',self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(self.close)
        fileMenu.addAction(exitAct)
        
        
    def updateStatusBar(self, string): 
        self.statusBar().showMessage(string)    
        
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QMessageBox.Yes | 
            QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            #We close the main widget, and so the subwidgets
            self.CentralWidget.close()
            #event is accepted
            event.accept()
            #closing with self.close() does not work in spyder 
            #However, QApplication.quit() does the job !!
        else:
            event.ignore() 

    def center(self):
        '''centers the window on the screen'''
        
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width()-size.width())//2, 
            (screen.height()-size.height())//2)

class Main(QWidget):
    
    def __init__(self,parent):
        
        super().__init__(parent)
        
                ####  Fichier de configuration
        self.repertoire = "/home/xavier/Python/CP_angles/"    
        self.Layout()
        self.connect()
        
    def Layout(self):
        self.MainLayout=QVBoxLayout()
        self.Camera=Camera(self)
        self.Save=Save(self)
        self.MainLayout.addWidget(self.Camera)
        self.MainLayout.addWidget(self.Save)
        
        self.setLayout(self.MainLayout)

    def connect(self):
        return
    
    def close(self):
        self.Camera.close()

class Camera(QWidget):
    """Camera worker widget responsible for live imaging, ROI handling and 1D projections."""
    
    parambound=pyqtSignal(list,list,list)
    
    def __init__(self,parent):
        super().__init__(parent)
        
        self.font_title = QFont()
        self.font_title.setPointSize(10)
        self.font_title.setBold(True)
        self.font_title.setWeight(75)
        
        self.font_text = QFont()
        self.font_text.setPointSize(8)
        self.font_text.setBold(False)
        self.font_text.setWeight(50)
        
        self.int_time = 1
        self.gain_auto=False
        self.temps_acq_auto=False
        self.set_frame_rate=4
        self.set_gain=20
        self.set_temps_acq = round(1/self.set_frame_rate,3)*1000000/2    #En µs 
                                                                        #On divise par deux pour que la caméra soit fluide
                                                                        # La caméra est ralentie quand le temps d'acquisition est au max                                              
        #Initialisation des camera
        self.FPS=0
        self.Camera_Param=Camera_param(self,self.set_frame_rate,self.set_gain,self.set_temps_acq)
        self.camera_thread = Camera_Thread(self,self.set_frame_rate,self.set_gain,self.set_temps_acq)
        self.frame_shape=[400,400]
        self.frame=[]
        self.draw=False
        self.draw_shape = None
        self.rois=[]
        self.activerois = [[],[],[]]
        self.img1b=pg.ImageItem()

        self.Background=np.zeros((self.frame_shape[1],self.frame_shape[0]))
        
        self.xh=[]
        self.yh=[]
        self.xv=[]
        self.yv=[]
        self.vcurve=[]
        self.hcurve=[]
        
        self.Layout()
        self.connect()
        self.inversion()
        
    def Layout(self):   

        #Layout Général
        self.cameralayout = QVBoxLayout()
        self.toplayout = QHBoxLayout()
        self.camerabuttonlayout = QHBoxLayout()
        
        #Affichage camera
        self.camera_widget = pg.GraphicsLayoutWidget()
        self.camera_widget.ci.layout.setColumnStretchFactor(0, 6)
        self.camera_widget.ci.layout.setColumnStretchFactor(1, 1)
        self.camera_widget.ci.layout.setRowStretchFactor(0, 6)
        self.camera_widget.ci.layout.setRowStretchFactor(1, 1)

        self.view = self.camera_widget.addViewBox(0,0,invertY=True)
        self.view.setAspectLocked(True)
        self.camera = pg.ImageItem(border='w',autoLevels=False)
        self.view.addItem(self.camera)
        self.Hor_Plot=self.camera_widget.addPlot(1,0)
        self.Vert_Plot=self.camera_widget.addPlot(0,1)

        #Draw LAyout
        self.circle_button = QPushButton("circle")
        self.square_button = QPushButton("Rectangle")
        
        #Camera choice
        self.camera_choice = QComboBox()
        self.CameraChoiceBox(self.camera_choice)

        #Inversion button
        self.vert_inv_check = QCheckBox()
        self.vert_inv_label = QLabel('Vertical \n inversion')
        self.vert_inv_label.setFont(self.font_text)
        self.hor_inv_check =QCheckBox()
        self.hor_inv_label = QLabel('Horizontal \n inversion')
        self.hor_inv_label.setFont(self.font_text)
        self.axe_inv_check = QCheckBox()
        self.axe_inv_label = QLabel('Axe transpose \n inversion')
        
        #bouton camera
        self.camera_on_button = QPushButton()
        self.camera_on_button.setText("Start Camera")
        self.camera_on_button.setStyleSheet('QPushButton {color: green;}')
        self.camera_on_button.setCheckable(True)
        self.aff_FPS=QLabel("FPS: " + "{:.0f}".format(self.FPS))
        self.camera_param_button=QPushButton()
        self.camera_param_button.setText("Param")
            
        #top
        self.toplayout.addWidget(self.camera_choice)
        self.toplayout.addWidget(self.vert_inv_check)
        self.toplayout.addWidget(self.vert_inv_label)
        self.toplayout.addWidget(self.hor_inv_check)
        self.toplayout.addWidget(self.hor_inv_label)
        self.toplayout.addWidget(self.axe_inv_check)
        self.toplayout.addWidget(self.axe_inv_label)
        self.toplayout.addStretch(-1)
        #buttons
        self.camerabuttonlayout.addWidget(self.circle_button)
        self.camerabuttonlayout.addWidget(self.square_button)
        self.camerabuttonlayout.addWidget(self.camera_on_button)
        self.camerabuttonlayout.addWidget(self.aff_FPS)
        self.camerabuttonlayout.addWidget(self.camera_param_button)
        
        #camera layout
        self.cameralayout.addLayout(self.toplayout)
        self.cameralayout.addWidget(self.camera_widget)
        self.cameralayout.addLayout(self.camerabuttonlayout)
        self.cameralayout.addWidget(self.Camera_Param)
        self.Camera_Param.setHidden(True)
        
        self.setLayout(self.cameralayout)
    
    def connect(self):
        self.camera_widget.scene().sigMouseClicked.connect(self.add_ROI)
        self.circle_button.clicked.connect(self.Draw)
        self.square_button.clicked.connect(self.Draw)
        self.camera_choice.activated[str].connect(self.CameraChoice)
        self.camera_on_button.clicked.connect(self.StreamingCamera)
        self.vert_inv_check.clicked.connect(self.inversion)
        self.hor_inv_check.clicked.connect(self.inversion)
        self.axe_inv_check.clicked.connect(self.inversion)
        self.camera_param_button.clicked.connect(self.camera_param_show)
        
        self.camera_thread.imagedone.connect(self.update_camera)
        self.Camera_Param.Paramchanged.connect(self.setcameraparam)
    
    def close(self):
        self.camera_thread.stop()
        print('Camera Off')

    def current_camera_id(self):
        """Return the currently selected camera identifier used by the acquisition thread."""
        return getattr(self.camera_thread, 'idcam', 'camera selection')

    def is_dummy_mode(self):
        """Tell whether the worker currently renders the synthetic dummy image."""
        return self.current_camera_id() == 'Dummy'

    def has_live_camera(self):
        """Tell whether a physical camera is selected and therefore can track real moves safely."""
        return self.current_camera_id() not in ('Dummy', 'camera selection', 'No Camera - refresh')
    
    def CameraChoiceBox(self,camera_choice):        
        ids = self.camera_thread.camera_list()
        camera_choice.clear()
        camera_choice.addItem('camera selection')
        for i in ids :
            camera_choice.addItem(i)
            
    def CameraChoice(self,text):        
        self.idcam = text
        self.camera_thread.connect_camera(self.idcam)
        self.setlimits(self.set_frame_rate)
        
        self.frame_shape=self.camera_thread.shape
        self.Background=np.zeros((self.frame_shape[1],self.frame_shape[0])).astype(self.camera_thread.type)
        self.Hor_Plot.setXRange(0,self.frame_shape[1],padding=0)
        self.Vert_Plot.setYRange(0,self.frame_shape[0],padding=0)
        self.xh=[np.arange(self.frame_shape[1])]
        self.xv=[np.arange(self.frame_shape[0])]
        self.yh=[np.zeros(len(self.xh[0]))]
        self.yv=[np.zeros(len(self.xv[0]))]
        self.hcurve = [self.Hor_Plot.plot(self.xh[0],self.yh[0])]
        self.vcurve = [self.Vert_Plot.plot(self.xv[0],self.yv[0])]
        self.vcurve[0].rotate(90)
        
    def camera_param_show(self):
        self.Camera_Param.setHidden(not self.Camera_Param.isHidden())
    
    def setlimits(self,frame_rate):
        """
        Met à jour les limites des différents paramètres de la caméra
        frame_rate en entrée permet de limiter le temps d'acquisition
        """
        def inbounds(bound,value):
            """ vérifie que les valeurs sont dans les bornes de la caméra
            """
            return min(max(bound[0],value),bound[1])
        
        self.frame_rate_bound,self.gain_bound=self.camera_thread.bounds(self.idcam)
        self.set_frame_rate = inbounds(self.frame_rate_bound,frame_rate)
        self.set_gain = inbounds(self.gain_bound,self.set_gain)
        self.temps_acq_bound = [0,int(1/self.set_frame_rate*1000000)] #En µs
        self.parambound.emit(self.frame_rate_bound,self.gain_bound,self.temps_acq_bound)
        
    
    def setcameraparam(self,a,gain_auto,temps_acq_auto,frame_rate,gain,temps_acq):
        """
        a=0 : un check a été clické
        a=1 : un slide a été modifié
        a=2 : un textedit a été changé (returnpress) 
        """
        #On récupère les entrée de lafonction et on les stocks dans les variables de classe
        self.gain_auto=gain_auto
        self.temps_acq_auto=temps_acq_auto
        self.set_frame_rate=frame_rate
        self.set_gain=gain
        self.set_temps_acq=temps_acq

        # On regarde si la caméra est live puis on arrete la caméra
        live=0
        if self.camera_on_button.isChecked():
            live=1
            self.camera_on_button.setChecked(False)
            self.camera_button()
        
        #On envoie dans la caméra
        if a==0:
            self.camera_thread.gain_auto = self.gain_auto
            self.camera_thread.temps_acq_auto = self.temps_acq_auto
        else :
            self.camera_thread.gain=self.set_gain
            self.camera_thread.fps=self.set_frame_rate
            self.camera_thread.tmps_acq = self.set_temps_acq
        if live==1 :
            #On relance la caméra
            self.camera_on_button.setChecked(True)
            self.StreamingCamera()
    
    def inversion(self):
        self.vert_inv = self.vert_inv_check.isChecked()
        self.hor_inv = self.hor_inv_check.isChecked()
        self.axe_inv = self.axe_inv_check.isChecked()
        #print(self.vert_inv,self.hor_inv,self.axe_inv)
        
    def camera_button(self):
        if self.camera_on_button.isChecked() :
            self.camera_on_button.setText("Stop Camera")
            self.camera_on_button.setStyleSheet('QPushButton {color: red;}')
            self.camera_thread.start()
        else : 
            self.camera_on_button.setText("Start Camera")
            self.camera_on_button.setStyleSheet('QPushButton {color: green;}')
            self.camera_thread.stop()
                
    def StreamingCamera(self):
        idcam=self.idcam
        self.camera_thread.Go_camera(idcam)
        if idcam == 'camera selection':
            print("aucune camera n'est sélectionnée")
            self.camera_on_button.setChecked(False)
        elif idcam == 'No Camera - refresh':
            self.CameraChoiceBox(self.camera_choice)
        else :
            self.camera_button()
    
    def update_camera(self,Frame,FPS,gain,tps):
        self.frame=Frame
        if self.Camera_Param.background_check.isChecked(): 
            Frame=Frame-self.Background
            Frame[Frame<=0]=0
        if self.axe_inv : Frame = Frame.T
        if self.hor_inv : Frame=Frame[::-1]
        if self.vert_inv : Frame=Frame.T[::-1].T
        
        self.aff_FPS.setText("FPS: " + "{:.0f}".format(FPS))
        if not 0 in Frame.shape:
            frame_min = float(np.min(Frame))
            frame_max = float(np.max(Frame))
            if frame_min == frame_max:
                frame_max = frame_min + 1.0
            self.camera.setImage(Frame, clear=True, autoLevels=False, levels=(frame_min, frame_max))
        if self.gain_auto:
            self.Camera_Param.gain_slider.setValue(gain)
        if self.temps_acq_auto:
            self.Camera_Param.temps_acq_slider.setValue(int(tps))
        self.frame_shape=Frame.shape
        
        # The horizontal and vertical traces are integrated intensity profiles. They are a
        # compact way to monitor alignment or ROI motion without reading the full image by eye.
        self.yh[0]=np.sum(Frame,axis=1)
        self.yv[0]=np.sum(Frame.T,axis=1)[::-1]
        self.hcurve[0].setData(self.yh[0])
        self.vcurve[0].setData(-self.yv[0])
        if np.size(self.rois) != 0:
            for i,roi in enumerate(self.rois,1):
                # Each ROI gets its own pair of integrated traces so we can compare local regions
                # of the camera image against the full-frame projection.
                pos_x, pos_y = roi.pos()
                #angle = roi.angle()
                size_x, size_y = roi.size()
                xmin=max(0,int(pos_x));xmax=min(self.frame_shape[0],int(pos_x+size_x))
                ymin=max(0,int(pos_y));ymax=min(self.frame_shape[1],int(pos_y+size_y))
                self.xh[i]=np.arange(xmin,xmax)
                self.xv[i]=np.arange(self.frame_shape[1]-ymax,self.frame_shape[1]-ymin)
                self.yh[i]=np.sum(Frame[xmin:xmax,ymin:ymax],axis=1)
                self.yv[i]=np.sum(Frame[xmin:xmax].T[ymin:ymax],axis=1)[::-1]
                self.hcurve[i].setData(self.xh[i],self.yh[i])
                self.vcurve[i].setData(self.xv[i],-self.yv[i])
    
    def Acq_background(self):
        self.Background=self.frame
    
    def Draw(self):
        """Quand un des bouton de dessin de ROI est pressé, met self.draw en true
        et garde en mémoire la valeur du bouton
        """
        self.draw=True
#        self.camera_widget.setConfigOption('leftButtonPan', False)
        btn = self.sender() #Récupère le bouton cliqué
        if isinstance(btn,QPushButton):
            self.draw_shape = btn.text()
            print(self.draw_shape)
        print(self.drawing,self.draw_shape)
#        self.drawing.draw=True
        
    def add_ROI(self,event):
        """Ajoute un ROI en fonction du bouton pressé
        ajoute le ROI à la liste self.rois
        reinitialise les valeurs par défaut de self.draw et self.draw_shape
        """
        pos=self.view.mapSceneToView(event.scenePos())
        if self.draw == True:
            if self.draw_shape=='circle':
                print('test circle')
                self.rois.append(pg.CircleROI([pos.x()-100,pos.y()-100], [200, 200],removable=True))
            elif self.draw_shape=='Rectangle':
                print('test rectangle')
                self.rois.append(pg.RectROI([pos.x(),pos.y()], [200, 20],removable=True))
            self.rois[-1].sigRegionChanged.connect(self.update)
            self.rois[-1].sigRemoveRequested.connect(self.remove_ROI)
            self.view.addItem(self.rois[-1])
            self.draw = False
            self.draw_shape=str()
            pos_x, pos_y = self.rois[-1].pos()
            size_x, size_y = self.rois[-1].size()
            xmin=max(0,int(pos_x));xmax=min(self.frame_shape[0],int(pos_x+size_x))
            ymin=max(0,self.frame_shape[1]-int(pos_y+size_y));ymax=min(self.frame_shape[1],self.frame_shape[1]-int(pos_y))
            self.xh.append(np.arange(xmin,xmax))
            self.xv.append(np.arange(ymin,ymax))
            self.yh.append(np.ones(len(self.xh[-1])))
            self.yv.append(np.ones(len(self.xv[-1])))
            self.hcurve.append(self.Hor_Plot.plot(self.xh[-1],self.yh[-1],pen=len(self.rois)))
            self.vcurve.append(self.Vert_Plot.plot(self.xv[-1],self.yv[-1],pen=len(self.rois)))
            self.vcurve[-1].rotate(90)
        return

    def remove_ROI(self):
        """Retire le ROI sélectionné par click droit du layout et de la liste des rois
        """
        item = self.sender()
        self.view.removeItem(item)
        self.rois.remove(item)
        print('test', self.rois, np.size(self.rois))
        return


class Camera_param(QWidget):
    """Parameter panel mirroring the subset of camera settings exposed in the GUI."""
    
    Paramchanged = pyqtSignal(int,bool,bool,int,int,float)
    
    def __init__(self,parent,set_frame_rate,set_gain,set_temps_acq):
        
        super(self.__class__,self).__init__(parent)
        self.gain_auto = False
        self.temps_acq_auto = False
        
        self.set_frame_rate=set_frame_rate
        self.set_gain=set_gain
        self.set_temps_acq=set_temps_acq
        
        self.frame_rate_bound=[]
        self.gain_bound=[]
        self.temps_acq_bound=[]
        
        self.layout()
        self.connect()

    def layout(self):
        self.camera_param_layout = QGridLayout()
        
        #Camera parameters labels
        self.frame_rate_label = QLabel("frame rate")
        self.gain_label = QLabel("Gain")
        self.temps_acq_label = QLabel("temps d'acq.")      
        
        #Camera parameters edit
        self.check_gain_auto = QCheckBox()
        self.check_temps_acq = QCheckBox()
        self.frame_rate_slider = QSlider()
        self.frame_rate_slider.setTickInterval(1)
        self.frame_rate_slider.setSingleStep(1)
        self.frame_rate_slider.setValue(self.set_frame_rate)
        self.frame_rate_slider.setOrientation(Qt.Horizontal)
        self.gain_slider = QSlider()
        self.gain_slider.setTickInterval(1)
        self.gain_slider.setSingleStep(1)
        self.gain_slider.setOrientation(Qt.Horizontal)
        self.gain_slider.setValue(self.set_gain)
        self.temps_acq_slider = QSlider()
        self.temps_acq_slider.setSingleStep(10)
        self.temps_acq_slider.setOrientation(Qt.Horizontal)
        self.temps_acq_slider.setRange(0,int(self.set_temps_acq))
        self.temps_acq_slider.setValue(int(self.set_temps_acq))
        self.temps_acq_edit = QLineEdit(str(self.set_temps_acq))
        self.temps_acq_edit.setMaximumWidth(50)
        self.frame_rate_edit = QLineEdit(str(self.set_frame_rate))
        self.frame_rate_edit.setMaximumWidth(50)
        self.gain_edit = QLineEdit(str(self.set_gain))
        self.gain_edit.setMaximumWidth(50)
        
        #Camera BAckground
        self.background_lay=QHBoxLayout()
        self.background_button = QPushButton()
        self.background_button.setText('Background Acquisition')
        self.background_check = QCheckBox()
        self.background_label = QLabel('Background correction')
        self.background_lay.addWidget(self.background_button)
        self.background_lay.addWidget(self.background_check)
        self.background_lay.addWidget(self.background_label)
        self.background_lay.addStretch(-1)
        
        #Camera parameters
        self.camera_param_layout.addWidget(QLabel("Auto"))
        self.camera_param_layout.addWidget(self.frame_rate_slider,0,2,1,4)
        self.camera_param_layout.addWidget(self.frame_rate_label,0,1)
        self.camera_param_layout.addWidget(self.frame_rate_edit,0,6)
        self.camera_param_layout.addWidget(self.check_gain_auto,1,0)        
        self.camera_param_layout.addWidget(self.gain_label,1,1)
        self.camera_param_layout.addWidget(self.gain_slider,1,2,1,4)
        self.camera_param_layout.addWidget(self.gain_edit,1,6)
        self.camera_param_layout.addWidget(self.check_temps_acq,2,0)
        self.camera_param_layout.addWidget(self.temps_acq_label,2,1)
        self.camera_param_layout.addWidget(self.temps_acq_slider,2,2,1,4)
        self.camera_param_layout.addWidget(self.temps_acq_edit,2,6)
        self.camera_param_layout.addLayout(self.background_lay,3,0,1,7)
        
        self.setLayout(self.camera_param_layout)
        

    def connect(self):
        
        #modification des parametres
        self.check_gain_auto.stateChanged.connect(partial(self.setcameraparam,a=0)) #https://stackoverflow.com/questions/6784084/how-to-pass-arguments-to-functions-by-the-click-of-button-in-pyqt
        self.check_temps_acq.stateChanged.connect(partial(self.setcameraparam,a=0))
        self.frame_rate_slider.sliderReleased.connect(partial(self.setcameraparam,a=1))
        self.gain_slider.sliderReleased.connect(partial(self.setcameraparam,a=1))
        self.temps_acq_slider.sliderReleased.connect(partial(self.setcameraparam,a=1))
        self.temps_acq_edit.returnPressed.connect(partial(self.setcameraparam,a=2))
        self.frame_rate_edit.returnPressed.connect(partial(self.setcameraparam,a=2))
        self.gain_edit.returnPressed.connect(partial(self.setcameraparam,a=2))
        self.background_button.clicked.connect(self.background)
           
        self.parent().parambound.connect(self.setbounds)
        return
    
    def setbounds(self,Frame_rate,gain,temps_acq):

        self.frame_rate_bound=Frame_rate
        self.gain_bound=gain
        self.temps_acq_bound=temps_acq
        self.temps_acq_slider.setRange(self.temps_acq_bound[0],self.temps_acq_bound[1])
        self.frame_rate_slider.setRange(self.frame_rate_bound[0],self.frame_rate_bound[1])
        self.gain_slider.setRange(self.gain_bound[0],self.gain_bound[1])
    
    def setcameraparam(self,a):

        def inbounds(bound,value):
            """ vérifie que les valeurs sont dans les bornes de la caméra
            """
            return min(max(bound[0],value),bound[1])
        
        if a==0:
            self.gain_auto = self.check_gain_auto.isChecked()
            self.temps_acq_auto = self.check_temps_acq.isChecked()
            self.gain_slider.setEnabled(not self.gain_auto)
            self.gain_edit.setEnabled(not self.gain_auto)

            self.temps_acq_slider.setEnabled(not self.temps_acq_auto)
            self.temps_acq_edit.setEnabled(not self.temps_acq_auto)

        elif a==1:
            #On transfère la valeur aux paramètres
            self.set_gain = inbounds(self.gain_bound,self.gain_slider.value())
            self.set_frame_rate = inbounds(self.frame_rate_bound,self.frame_rate_slider.value())
            self.temps_acq_bound = [0,int(1/self.set_frame_rate*1000000)]
            self.temps_acq_slider.setRange(self.temps_acq_bound[0],self.temps_acq_bound[1])
            self.set_temps_acq = inbounds(self.temps_acq_bound,self.temps_acq_slider.value())
            #On transfère au textEdit
            self.gain_edit.setText(str(self.set_gain))
            self.frame_rate_edit.setText(str(self.set_frame_rate))
            self.temps_acq_edit.setText(str(self.set_temps_acq))
        elif a==2:
            #On transfère aux paramètre
            self.set_gain = inbounds(self.gain_bound,int(self.gain_edit.text()))
            self.set_frame_rate = inbounds(self.frame_rate_bound,int(self.frame_rate_edit.text()))
            self.temps_acq_bound = [0,int(1/self.set_frame_rate*1000000)]
            self.temps_acq_slider.setRange(self.temps_acq_bound[0],self.temps_acq_bound[1])
            self.set_temps_acq = int(inbounds(self.temps_acq_bound,float(self.temps_acq_edit.text())))
            #On transfère aux sliders
            self.gain_slider.setValue(self.set_gain)
            self.frame_rate_slider.setValue(self.set_frame_rate)
            self.temps_acq_slider.setValue(self.set_temps_acq)
            #On transfère au textEdit
            self.gain_edit.setText(str(self.set_gain))
            self.frame_rate_edit.setText(str(self.set_frame_rate))
            self.temps_acq_edit.setText(str(self.set_temps_acq))
            
        self.Paramchanged.emit(a,self.gain_auto,self.temps_acq_auto,self.set_frame_rate,self.set_gain,self.set_temps_acq)
        
    def background(self):
        self.parent().Acq_background()
        self.background_check.setChecked(True)
    

class Camera_Thread(QThread):
    """Acquisition thread that hides the aravis hardware details behind a simple image stream."""
    
    imagedone=pyqtSignal(np.ndarray,int, int,float)
    
    def __init__(self,parent,fps,gain,tps_acq):
        super(self.__class__,self).__init__(parent)
        self.cam =str()
        self.ids = []
        self.fps = fps
        self.gain = gain
        self.gain_auto = False
        self.temps_acq_auto = False
        self.tmps_acq = tps_acq
        self.runs = False
        #En cas de Dummy
        self.shape = (512, 1024)
        self.type=np.float32
        self.sim_image_center = np.array(self.shape)/2.
        self.posx,self.posy=200,100
        self.posz=50
        self.sigma0=20
        self.frame=[]
      
    def camera_list(self):
        try:
            self.ids = aravis.get_device_ids() #List visible cameras
        except:
            self.ids = []
        if self.ids == []:
            self.ids.append('No Camera - refresh')       
        self.ids.append('Dummy')
        self.idcam='camera selection'
        return self.ids        
    
    def disconnect_camera(self):
        self.cam = str()
    
    def bounds(self,idcam):
        if idcam == 'camera selection' or idcam == 'Dummy' or idcam == 'No Camera - refresh': 
            frame_rate_bound=[0,100]
            gain_bound=[0,50]
            return frame_rate_bound,gain_bound
        else:
            frame_rate_bound = [int(self.cam.get_frame_rate_bounds()[0]),int(self.cam.get_frame_rate_bounds()[1])]
            gain_bound = [int(self.cam.get_gain_bounds()[0]),int(self.cam.get_gain_bounds()[1])]
            return frame_rate_bound,gain_bound
        
    def connect_camera(self,idcam):
        self.stop()
        self.disconnect_camera()
        print('Camera thread',idcam)
        if idcam != 'Dummy':
            try:    
                self.cam = aravis.Camera(str(idcam))
                print('camera connectée')
            except:
                print("La caméra est déjà connectée ou la connection n'a pas réussie")
        else:
            print('caméra Dummy')
        self.Go_camera(idcam)
        if idcam == 'Dummy':
            self.shape = (512, 1024)
        self.bounds(idcam)

    def stop(self):
        self.runs = False
        print(self.cam,self.idcam)
        if self.cam != str() and self.idcam!='Dummy' and self.idcam!='camera selection' and self.idcam!='No Camera - refresh':
            self.cam.stop_acquisition()
          
    def Go_camera(self,idcam):
        self.runs=True
        self.idcam=idcam
        if idcam =='Dummy' :
            self.type=np.float32
            return
        if idcam =='No Camera - refresh' or idcam =='camera selection':
            self.parent().CameraChoiceBox(self.parent().camera_choice)
            return
        self.cam.set_pixel_format(17301505) ; self.type=np.uint8   #set the camera in 'Mono 8' format
        #self.cam.set_pixel_format(17301514)    #set the camera in 'Bayer GB 8' format
        #self.cam.set_pixel_format(17825799)    #set the camera in 'Mono 16' format
        if self.gain_auto:
            self.cam.set_gain_auto(aravis.Aravis.Auto.CONTINUOUS)   #On passe en gain auto
        else:
            self.cam.set_gain_auto(aravis.Aravis.Auto.OFF)          #enleve le gain automatique
            self.cam.set_gain(self.gain)
        if self.temps_acq_auto:
            self.cam.set_exposure_time_auto(aravis.Aravis.Auto.CONTINUOUS)
        else:
            self.cam.set_exposure_time_auto(aravis.Aravis.Auto.OFF)
            self.cam.set_exposure_time(float(self.tmps_acq))
        self.cam.set_frame_rate(self.fps)
        self.cam.start_acquisition_continuous(nb_buffers=10)
        self.shape=np.shape(self.cam.pop_frame())
  
    @pyqtSlot()    
    def run(self):
        while self.runs: 
            before=time.time()
            if self.idcam=='Dummy':
                self.frame = self.acquire_image_data()
            else :
                self.frame = np.transpose(self.cam.pop_frame().astype(int))
            after=time.time()
            fps=1/(after-before)
            if self.gain_auto:
                self.gain=self.cam.get_gain()
            if self.temps_acq_auto:
                self.tmps_acq=int(self.cam.get_exposure_time())
            self.imagedone.emit(self.frame.astype(self.type),fps,self.gain,self.tmps_acq)
        if self.idcam != 'Dummy':
            self.cam.stop_acquisition()

    
    def acquire_image_data(self):
        """Generate a synthetic Gaussian spot used when no physical camera is connected."""
        x0, y0 = self.sim_image_center
        
        def g(x, y, x0, y0, sigma):
            return np.exp(-((x - x0)**2 + (y - y0)**2)/(2*sigma**2))
        
        sigma = self.sigma0*np.sqrt(1+((self.posz)/10)**2)
        x = np.arange(0, self.shape[0])
        y = np.arange(0, self.shape[1])
        X, Y = np.meshgrid(x, y)
        img = g(X, Y, x0 + self.posx, y0 + self.posy, sigma)
        img = (200*img/np.max(img))*self.tmps_acq/1000000*(self.gain+10)/60
        img += 2*npr.random(self.shape).T*(self.gain+10)/60 + 2*npr.random(self.shape).T
        wait_time = 1/self.fps
        time.sleep(wait_time)
        return img.astype(self.type)
            
class Save(QWidget):
    
    def __init__(self,parent):
        super().__init__(parent)
        self.savepath = os.getcwd()
        self.Layout()
        self.connect()
        
    def Layout(self):
        self.save_layout = QGridLayout()
        
        self.save_image_button = QPushButton ('Save Image')

        self.file_loc = QLineEdit(self.savepath)
        self.location_button = QPushButton()
        #https://joekuan.wordpress.com/2015/09/23/list-of-qt-icons/
        self.location_button.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_FileDialogStart')))
        self.numfile=1
        self.File_number = QSpinBox()
        self.prefix_file_name = QLineEdit(annee+mois+jour+"a")
        self.File_number.setMinimum(1)
        self.File_number.setValue(1)
        
        #Notes
        self.save_note = QTextEdit("Date : " + annee+'/'+mois+'/'+jour )
        self.save_note.append("Utilisateur :")
        self.save_note.append("Echantillon :" )
        self.save_note.append("Mesure :")
        self.save_note.setMaximumHeight(100)
        
        #Save Layout
        self.save_layout.addWidget(self.file_loc,0,0,1,2)
        self.save_layout.addWidget(self.location_button,0,2)
        self.save_layout.addWidget(self.prefix_file_name,1,0,1,2)
        self.save_layout.addWidget(self.File_number,1,2)
        self.save_layout.addWidget(self.save_image_button,0,3)
        self.save_layout.addWidget(self.save_note,0,4,3,3)
        
        self.setLayout(self.save_layout)
        
    
    def connect(self):
        self.file_loc.textChanged.connect(self.changesavepath)
        self.location_button.clicked.connect(self.opensaveloc)
        self.save_image_button.clicked.connect(self.save_image)

 
    def opensaveloc(self): 
        #https://pythonprogramming.net/file-saving-pyqt-tutorial/
        file_name=self.filename() 
        file_name = QFileDialog.getSaveFileName(self, 'Save File',file_name,".npz")[0]
        if not file_name:
            return
        notes = self.save_note.toPlainText()+ "\n"+ "\n"

        np.savez(file_name, notes=notes, Image = self.parent().Camera.frame, Background=self.parent().Camera.Background ,\
                     signalX=[self.parent().Camera.xh,self.parent().Camera.yh], signalY=[self.parent().Camera.xv,self.parent().Camera.yv])
        self.numfile+=1
        self.File_number.setValue(self.File_number.value()+1)
        self.prefix_file_name.setText(os.path.split(file_name)[1][:-5])
        self.savepath = os.path.split(file_name)[0]
        self.file_loc.setText(self.savepath)
        return
    
    def existing_file(self,file_name):
        try:
            with open(file_name):
               reply = QMessageBox.question(self, 'Message',\
                                            "Le fichier existe déjà, voulez vous l'écraser ?", QMessageBox.Yes | 
               QMessageBox.No, QMessageBox.No)             
               if reply == QMessageBox.Yes:
                   return True
               else:
                   return False
        except IOError:
            return True
    
    def save_image(self):
        file_name=self.filename()[:-4]
        boo=self.existing_file(file_name+'.npz')
        if boo==True:
            self.numfile+=1
            self.File_number.setValue(self.File_number.value()+1)
            pass
        else:
            compteur=0
            file_name+='_'+str(compteur)
            while os.path.exists(file_name + ".npz" ):
                compteur+=1
                file_name = file_name[0:-2] + "_" + str(compteur)
            self.prefix_file_name.setText(os.path.split(file_name)[1][:-1])
            self.File_number.setValue(compteur)
        notes = self.save_note.toPlainText()+ "\n"+ "\n"
        np.savez(file_name, notes=notes, Image = self.parent().Camera.frame, Background=self.parent().Camera.Background ,\
                     signalX=[self.parent().Camera.xh,self.parent().Camera.yh], signalY=[self.parent().Camera.xv,self.parent().Camera.yv])
   
    
    def filename(self):
        file_name=self.prefix_file_name.text()+str(self.File_number.value())+ '.npz'
        if self.savepath:
            return os.path.join(self.savepath, file_name)
        return file_name
    
    def changesavepath(self):
        self.savepath = self.file_loc.text()

def main():
    app = QApplication.instance() 
    if not app:
        app = QApplication(sys.argv)
    prog = Fenetre() 
    prog.show()
    app.exec_()


    
if __name__ == '__main__':
    main()
