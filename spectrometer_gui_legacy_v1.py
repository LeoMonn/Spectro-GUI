#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 14 12:17:44 2018

@author: leonard

Legacy worker kept as a historical reference.
The active spectrometer implementation is `spectrometer_gui.py`.
"""
##################################################################
###       import pour l'interface et autres fonctions       ######
##################################################################
from PyQt5.QtWidgets import QLineEdit,QLabel,QAction,QPushButton,QSpinBox, QComboBox, QProgressBar, QRadioButton, QListWidget
from PyQt5.QtWidgets import QTextEdit,QCheckBox,QMessageBox,QFileDialog,QStyle, QMenu, QWidgetAction, QSlider
from PyQt5.QtWidgets import QMainWindow,QWidget,QApplication,QDesktopWidget,QGridLayout,QVBoxLayout,QHBoxLayout
from PyQt5.QtCore import pyqtSignal,QThread,pyqtSlot,Qt
from PyQt5.QtGui import QIcon, QFont, QCursor
import os, sys
import time
from datetime import date
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np
import re

##################################################################
###       import pour le fonctionnement de la manip         ######
##################################################################

list_bib=[];devices=[''];liste=['not connected']
try:
    import seabreeze
    seabreeze.use('pyseabreeze')
    import seabreeze.spectrometers as sb
    print('sea')
    list_bib.append("sea")
    for n,spe_sea in enumerate(sb.list_devices(),1):
        devices.append(spe_sea)
        liste.append("Ocean Optics "+str(n))
except:
    pass

try:
    import OSA_Thorlabs as osat        
    list_bib.append("thor")
    print('thor')
    regex= re.compile(rb"USB::\w+::\w+::\w+::RAW")
    m=re.findall(regex,osat.findressource())
    for n,spe_th in enumerate(m):
        devices.append(spe_th)
        liste.append("Thorlabs_" + str(n))
except:
    pass
    
devices.append('Dummy')

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
        '''initiates application UI'''
        self.Create_Layout() 
        self.statusBar().showMessage('Ready')        
        self.menu()
        self.setWindowTitle('Spectro')    
        ###################################################################"

    def Create_Layout(self):
        self.CentralWidget = Main(self)
        self.setCentralWidget(self.CentralWidget)       

    def menu(self):
        menubar=self.menuBar()
        fileMenu = menubar.addMenu('&File')
        exitAct = QAction(QIcon('exit.png'),'&Exit',self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(self.close)
        fileMenu.addAction(exitAct)
        for Widgets in self.CentralWidget.Widgets:
            Widgets.MenuBar(menubar)
        
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
            QApplication.quit()
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
        self.repertoire = "/home/xavier/Python/CP_angles/"    
        self.Layout()
        self.connect()
        
    def Layout(self):
        self.MainLayout=QVBoxLayout()
        self.Widgets=[Spectro(self)]
        self.Save=Save(self)
        self.MainLayout.addWidget(self.Widgets[0])
        self.MainLayout.addWidget(self.Save)
        self.setLayout(self.MainLayout)
    
    def connect(self):
        return
    
    def close(self):
        for Widgets in self.Widgets:
            Widgets.stop()

    
class Spectro(QWidget):
    """ Class that defines the UI and fonctions for the spectrometer  """
    
    def __init__(self,parent):
        super().__init__(parent)
        print('Spectro')
        
        self.int_time = 1
        self.spectre = 0
        self.background = 0
        self.avg = 1
        self.stack_spectre = np.array([])
        self.cross = False
        self.cross_coord=[0,0]
        self.curseur = False
        self.spectro_fini=True
        self.spectro_thread = Spectro_Thread(self,self.int_time,self.avg)
        self.manip=False    #Allows external control of the spectrometer 
                            #through Go_spectrum() without pressing the Go button
                            #Deactivates the stacked plot
        
        # Defnition of the text font for titles and labels
        self.font_title = QFont()
        self.font_title.setPointSize(10)
        self.font_title.setBold(True)
        self.font_title.setWeight(75)
        
        self.font_text = QFont()
        self.font_text.setPointSize(8)
        self.font_text.setBold(False)
        self.font_text.setWeight(50)
        
        self.Layout()
        self.connect()
    
    def MenuBar(self,Menu):
        SpectroMenu = Menu.addMenu('&Spectro')
        OpenAct = QAction(QIcon('exit.png'),'&Open',self)
        OpenAct.setShortcut('Ctrl+O')
        OpenAct.setStatusTip('Open Files')
        #exitAct.triggered.connect(self.close)
        SpectroMenu.addAction(OpenAct)
        
    
    def Layout(self):   
        #Choix spectro
        self.spectro_choice=QComboBox()
        self.spectro_choice_box(self.spectro_choice)
        
        #Spectro parameters Layout (Vbox)
        self.spectro_layout = QVBoxLayout()
        self.Top_layout = QHBoxLayout()
        self.central_layout = QHBoxLayout()
        self.bottom_layout = QHBoxLayout()
        self.button_layout = QHBoxLayout()
        self.central_right_widget = QWidget()
        self.central_right_widget.setMaximumWidth(120)
        self.central_right_layout = QVBoxLayout()
        self.central_left_layout = QGridLayout()

        #Spectrop parametrers
        self.continuous_check = QCheckBox()
        self.continuous_label = QLabel ("Continuous") 
        self.continuous_label.setFont(self.font_text)
        self.acquisition_time_edit = QLineEdit(str(self.int_time))
        self.averaging_edit = QLineEdit("1")
        
        self.x=self.spectro_thread.x
        self.lambda_min_edit = QLineEdit(str(int(self.x[0])))
        self.lambda_max_edit = QLineEdit(str(int(self.x[-1])))
        
        #Spectro
        self.fig = plt.Figure()
        self.spectro = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.spectro, None)
        self.axes = self.fig.add_subplot(111)
        self.curseur_axe=self.fig.add_subplot(111)
        self.y = self.x*0
        self.background = self.x*self.background
        self.line, = self.axes.plot(self.x,self.y,zorder=5)
        self.coord_cross = [[self.x[0],self.cross_coord[0],self.cross_coord[0],\
                                 self.cross_coord[0],self.cross_coord[0],self.x[-1]],\
                           [self.cross_coord[1],self.cross_coord[1],self.axes.get_ylim()[0],\
                            self.axes.get_ylim()[1],self.cross_coord[1],self.cross_coord[1]]]
        self.crossline, = self.axes.plot(self.cross_coord[0],self.cross_coord[1],zorder=10)
        self.abscisse()

        #Format des abscisses
        self.abscisse_type_slider=QSlider()
        self.abscisse_type_slider.setRange(1,3)
        self.abscisse_type_slider.setTickInterval(1)
        self.abscisse_type_slider.setSingleStep(0.5)
        self.abscisse_type_slider.setValue(1)
        self.abscisse_type_slider.setTickPosition(QSlider.TicksBelow)
        self.abscisse_type_slider.setOrientation(Qt.Horizontal)
        self.Label1=QLabel("nm")
        self.Label2=QLabel("eV")
        self.Label3=QLabel('NF')
        
        self.periode_text=QLineEdit("424")
        self.periode_text.setEnabled(False)
        
        self.abscisse_type_layout=QGridLayout()
        self.abscisse_type_layout.addWidget(self.abscisse_type_slider,0,0,1,10)
        self.abscisse_type_layout.addWidget(self.Label1,1,0,1,2)
        self.abscisse_type_layout.addWidget(self.Label2,1,4,1,2)
        self.abscisse_type_layout.addWidget(self.Label3,1,8,1,2)
        self.abscisse_type_layout.addWidget(self.periode_text,2,7,1,3)
        
        #ProgressBar
        self.progress = QProgressBar(self)
        self.progress_thread=Progressbar(self,self.int_time)
        
        self.temps_spectre = QLabel("Acquisition time : 0.000 s")
        self.temps_spectre.setFont(self.font_text)
        self.avg_progress = QLabel("Average : ")
        self.avg_progress.setFont(self.font_text)
    
        #Spectro parameters labels
        self.acquisition_time_label = QLabel("Acquisition \n Time (s)")
        self.acquisition_time_label.setFont(self.font_text)
        
        self.averaging_label = QLabel ("Averaging")
        self.averaging_label.setFont(self.font_text)
        self.lambda_min_label = QLabel("lambda min (nm)")
        self.lambda_max_label = QLabel("lambda max (nm)")
        
        #Gestion du background
        self.background_select = QCheckBox()
        self.background_select_label = QLabel("Background")
        self.background_select_label.setFont(self.font_text)
        self.background_sauvegarde = QPushButton("Save Background")
        self.background_sauvegarde.setFont(self.font_text)
        
        #Bouton lancement
        self.go_button = QPushButton("Go !")
        self.go_button.setFont(self.font_title)
        self.go_button.setCheckable(True)
        
        #Bouton selection spectre 2D/superposé
        self.form_selec1 = QRadioButton("simple \n plot")
        self.form_selec1.setFont(self.font_text)
        self.form_selec1.setChecked(True)
        self.form_selec2 = QRadioButton("Stacked \n plot")
        self.form_selec2.setFont(self.font_text)
        self.form_selec3 = QRadioButton("2D \n plot")
        self.form_selec3.setFont(self.font_text)
        
        #Boutton zoom
        self.autozoom_button = QPushButton("Auto Zoom")
        self.autozoom_button .setFont(self.font_text)
        self.zoom_button = QPushButton("Zoom")
        self.zoom_button.setFont(self.font_text)
        self.zoom_button.setCheckable(True)

        #Curseurs
        self.add_curseur = QPushButton("Add Cursor")
        self.add_curseur.setFont(self.font_text)
        self.curseur_widget = QListWidget()
        self.curseur_widget.addItem("No cursor")
        self.curseur_widget.setMaximumHeight(100)
        self.nombre_curseur=0
        self.curseurs=[]
        
        #garder à l'écran/clear ecran
        self.keep_on_screen_button = QPushButton("keep spectrum")
        self.keep_on_screen_button.setFont(self.font_text)
        self.clear_screen_button = QPushButton("Reinitialize")
        self.clear_screen_button.setFont(self.font_text)
        
        self.Top_layout.addWidget(self.background_select)
        self.Top_layout.addWidget(self.background_select_label)
        self.Top_layout.addWidget(self.continuous_check)
        self.Top_layout.addWidget(self.continuous_label)
        self.Top_layout.addWidget(self.acquisition_time_label)
        self.Top_layout.addWidget(self.acquisition_time_edit)
        self.Top_layout.addWidget(self.averaging_label)
        self.Top_layout.addWidget(self.averaging_edit)
        self.Top_layout.addWidget(self.spectro_choice)
        
        self.central_layout.addLayout(self.central_left_layout)
        
        self.central_left_layout.addWidget(self.spectro,0,0,1,4)
        self.central_left_layout.addWidget(self.progress,1,0,1,2)
        self.central_left_layout.addWidget(self.temps_spectre,1,2)
        self.central_left_layout.addWidget(self.avg_progress,1,3)
        
        self.central_right_layout.addWidget(self.go_button)
        self.central_right_layout.addWidget(self.keep_on_screen_button)
        self.central_right_layout.addWidget(self.clear_screen_button)
        self.central_right_layout.addWidget(self.autozoom_button)
        self.central_right_layout.addWidget(self.zoom_button)
        self.central_right_layout.addWidget(self.add_curseur)
        self.central_right_layout.addWidget(self.background_sauvegarde)
        self.central_right_layout.addWidget(self.form_selec1)
        self.central_right_layout.addWidget(self.form_selec2)
        self.central_right_layout.addWidget(self.form_selec3)
        self.central_right_layout.addLayout(self.abscisse_type_layout)
        self.central_right_layout.addStretch(-1)
        
        self.central_right_widget.setLayout(self.central_right_layout)
        
        self.central_layout.addWidget(self.central_right_widget)
       
        self.bottom_layout.addWidget(self.lambda_min_label)
        self.bottom_layout.addWidget(self.lambda_min_edit)
        self.bottom_layout.addWidget(self.lambda_max_label)
        self.bottom_layout.addWidget(self.lambda_max_edit)
        
        self.spectro_layout.addLayout(self.Top_layout)
        self.spectro_layout.addLayout(self.central_layout)
        self.spectro_layout.addLayout(self.bottom_layout)
        self.spectro_layout.addWidget(self.curseur_widget)
        self.spectro_layout.addLayout(self.button_layout)
        
        self.setLayout(self.spectro_layout)
        
    def connect(self):
        self.abscisse_type_slider.valueChanged.connect(self.abscisse_type)
        self.periode_text.returnPressed.connect(self.abscisse_type)
        self.continuous_check.stateChanged.connect(self.paramchanged)
        self.acquisition_time_edit.textChanged.connect(self.continuous_mode)
        self.averaging_edit.textChanged.connect(self.continuous_mode)
        self.lambda_max_edit.returnPressed.connect(self.abscisse)
        self.lambda_min_edit.returnPressed.connect(self.abscisse)
        self.coord = self.spectro.mpl_connect('button_press_event', self.onclick)
        self.background_select.stateChanged.connect(self.paramchanged)
        self.background_sauvegarde.clicked.connect(self.savebackground)
        self.go_button.clicked.connect(self.Go_spectrum)
        self.add_curseur.clicked.connect(self.addcurseur)
        self.curseur_widget.itemClicked.connect( self.remcurseur)
        self.zoom_button.clicked.connect(self.zoom)
        self.clear_screen_button.clicked.connect(self.clear_stackspectre)
        self.spectro_choice.activated[str].connect(self.SpectroChoice)
        self.autozoom_button.clicked.connect(self.Autozoom)
        self.keep_on_screen_button.clicked.connect(self.add_spectrum)
        
        self.spectro_thread.spectredone.connect(self.update_spectrum)
        self.spectro_thread.acq_over.connect(self.spectro_over)
        self.spectro_thread.spectrum_starting.connect(self.start_progress)
        self.progress_thread.finish.connect(self.update_progress)
    
    def spectro_choice_box(self,spectro_choice):
        liste=self.spectro_thread.spectro_list()
        spectro_choice.clear()
        for i in liste:
            spectro_choice.addItem(i)
    
    def SpectroChoice(self,text):
        self.spectro_thread.spectro_connect(text)
        self.abscisse_type()        
    
    def stop(self):
        self.spectro_thread.stop()
        
    def onclick(self,event):
        if event.button ==1 and event.dblclick==True:
            #Menu pour changer les coordonnées max et min du graph
            #http://python.6.x6.nabble.com/Add-custom-widget-to-the-QMenu-td1795339.html
            
            self.GraphMenu= QMenu(self)
            #Definition du Widget apparaissant
            GraphWidget = QWidget()
            GraphWidgetLayout = QGridLayout()
            
            Xmin=QLabel("Xmin");Xmax=QLabel("Xmax");self.XMinEdit=QLineEdit(str(self.axes.get_xlim()[0]));self.XMaxEdit=QLineEdit(str(self.axes.get_xlim()[1]))
            Ymin=QLabel("Ymin");Ymax=QLabel("Ymax");self.YMinEdit=QLineEdit(str(self.axes.get_ylim()[0]));self.YMaxEdit=QLineEdit(str(self.axes.get_ylim()[1]))
            Okbutton=QPushButton("Ok");Escbutton=QPushButton("Esc")
            
            self.XMinEdit.returnPressed.connect(self.updatedblclick);self.XMaxEdit.returnPressed.connect(self.updatedblclick)
            self.YMinEdit.returnPressed.connect(self.updatedblclick);self.YMaxEdit.returnPressed.connect(self.updatedblclick)
            Okbutton.clicked.connect(self.updatedblclick);Escbutton.clicked.connect(self.GraphMenu.clear)
            
            GraphWidgetLayout.addWidget(Xmin,0,0);GraphWidgetLayout.addWidget(self.XMinEdit,0,1);
            GraphWidgetLayout.addWidget(Xmax,0,2);GraphWidgetLayout.addWidget(self.XMaxEdit,0,3);
            GraphWidgetLayout.addWidget(Ymin,1,0);GraphWidgetLayout.addWidget(self.YMinEdit,1,1);
            GraphWidgetLayout.addWidget(Ymax,1,2);GraphWidgetLayout.addWidget(self.YMaxEdit,1,3);
            GraphWidgetLayout.addWidget(Okbutton,2,1);GraphWidgetLayout.addWidget(Escbutton,2,2)
            
            GraphWidget.setLayout(GraphWidgetLayout)
            limites = QWidgetAction(self.GraphMenu)
            limites.setDefaultWidget(GraphWidget)
            self.GraphMenu.addAction(limites)
            self.GraphMenu.exec_(QCursor.pos())
            return
        #AutoZoom sur click droit
        elif event.button==3:
            self.abscisse()
            self.Autozoom()
            return
        #Curseur sur simple click gauche
        elif event.button ==1 and event.dblclick==False:
            x,y = event.xdata,event.ydata
            if event.inaxes != None and self.zoom_button.isChecked() == False: 
                cross_coord=[x, y]
            else: 
                return
            self.coord_cross = [[self.x[0],cross_coord[0],cross_coord[0],\
                                 cross_coord[0],cross_coord[0],self.x[-1]],\
                           [cross_coord[1],cross_coord[1],self.axes.get_ylim()[0],\
                            self.axes.get_ylim()[1],cross_coord[1],cross_coord[1]]]
            self.crossline.set_xdata(self.coord_cross[0])
            self.crossline.set_ydata(self.coord_cross[1])
            self.spectro.draw()
            if self.nombre_curseur == 0:
                self.parent().parent().statusBar().showMessage("x:"+str(round(x,2))+"   y:"+str("%.2e"% y))
            elif self.nombre_curseur >0:
                #print(x,self.curseurs[0][0][1])
                if self.abscisse_type_slider.value()==1:
                    x=x        
                if self.abscisse_type_slider.value()==2:
                    x=1240/x   
                elif self.abscisse_type_slider.value()==3:
                    x=int(self.periode_text.text())/x     
                delta_lambda = x-self.curseurs[0][0][1]
                delta_En = (1/self.curseurs[0][0][1]-1/x)*1e7
                self.parent().parent().statusBar().showMessage("x:"+str(round(x,2))+"   y:"+\
                            str("%.2e"% y) + "  "+chr(916) + chr(955) + ' = '+ \
                            str(round(delta_lambda,2)) + " nm  "+ chr(916)+"En = " +str(round(delta_En)) + " cm-1")
            return self.coord_cross
    
    def updatedblclick(self):
        #Update le graph avec les coordonnées entrées dans le Qmenu popup 
        self.axes.set_xlim(float(self.XMinEdit.text()),float(self.XMaxEdit.text()))
        self.axes.set_ylim(float(self.YMinEdit.text()),float(self.YMaxEdit.text()))
        self.spectro.draw()
        self.GraphMenu.clear()
        
    def coord_spectrum(self,event):
        return
    
    def Go_spectrum(self):
        time.sleep(0.1)
        if self.go_button.isChecked() or self.manip==True:      #On veut que les spectres se lancent en manip même si le bouton n'est pas Checké
            self.spectro_fini=False
            if self.spectro_choice.currentText()=='No Spectro - Refresh' or self.spectro_choice.currentText()=='not connected'  :
                return
            self.spectro_thread.avg=int(self.averaging_edit.text())
            self.spectro_thread.int_time=float(self.acquisition_time_edit.text())
            self.spectro_thread.spectro_param(float(self.acquisition_time_edit.text()))
            self.spectro_thread.start()
        else:
            self.continuous_check.setChecked(False)

    def spectro_over(self):
        self.go_button.setChecked(False)
        self.spectro_fini=True
        
    def update_spectrum(self,spectre,i,tps):
        self.y=spectre
        self.line.set_ydata(self.y)
        self.curseur_axe.set_ylim(self.axes.get_ylim())
        self.spectro.draw()
        if tps > 0.1:
            tps=round(tps,2)
            time = 's'
        elif tps < 0.1 and tps > 0.0001 :
            tps = round(1000*tps,2)
            time = 'ms'
        elif tps < 0.0001:
            tps = round(1000000*tps,2)
            time='µs'  
        self.temps_spectre.setText("Acquisition time :"+ str(tps) + time)
        self.avg_progress.setText("Average : "+ str(i)+"/"+self.averaging_edit.text())
        if self.form_selec2.isChecked() and str(i)==self.averaging_edit.text():
            self.add_spectrum()
        if self.form_selec3.isChecked() and str(i)==self.averaging_edit.text():
            self.add_spectrum()
            x=range(len(self.stack_spectre))
            plt.pcolormesh(x,self.x,self.stack_spectre[1:].T)
            plt.draw()
            
    def start_progress(self,int_time):
        self.progress_thread.int_time=int_time
        self.progress_thread.start()
        # The  progress bar calculation is done in a thread
        
    def update_progress(self,prog) :
        # The  progress bar calculation is done in a thread
        self.progress.setValue(prog)
        
    def paramchanged(self):
        self.spectro_thread.background_check=self.background_select.isChecked()
        self.spectro_thread.continuous=self.continuous_check.isChecked()
        
    def add_spectrum(self):
        if 0 in self.stack_spectre.shape :
            self.stack_spectre = np.append(self.spectro_thread.x.reshape(1,-1),\
                                           self.y.reshape(1,-1),axis=0)
        else:
            self.stack_spectre = np.append(self.stack_spectre,self.y.reshape(1,-1),axis=0)   
        self.update_stackspectre()
        self.spectro.draw()
    
    def update_stackspectre(self):
        if not 0 in self.stack_spectre.shape :
            ### stacked plot is desabled mainly to gain time when lots of spectra are acquired
            if self.manip==False :
                for i in self.stack_spectre[1:]:
                    self.axes.plot(self.x,i)
    
    def clear_spectrum(self):
        limy=self.axes.get_ylim()
        limx=self.axes.get_xlim()
        self.axes.cla()
        self.line,=self.axes.plot(self.x,self.y)
        self.crossline, = self.axes.plot(self.coord_cross[0],self.coord_cross[1])
        self.axes.set_ylim(limy)
        self.axes.set_xlim(limx)
        
    def clear_stackspectre(self):
        self.stack_spectre = np.array([])
        #Reinitializing
        self.y=self.x*0
        self.clear_spectrum()
        self.update_curseur_list()
        #Do not clear curseur_axe, it doesn't work !!
        self.spectro.draw()
    
    def rem_spectrum(self):
        return       
          
    def savebackground(self):
        self.spectro_thread.background = self.y
        self.background_select.setChecked(True)
        
    def Autozoom(self):
        self.axes.set_ylim(np.min(self.y),np.max(self.y))
        self.spectro.draw()
    
    def zoom(self):
        self.toolbar.zoom()
    
    def abscisse(self):
        self.axes.set_xlim(float(self.lambda_min_edit.text()),float(self.lambda_max_edit.text()))
        self.spectro.draw()
    
    def abscisse_type(self):
        """ Allow to change the abscisse axis to nm, eV or normalized frequency (NF)"""
        if self.abscisse_type_slider.value()==1:
            self.periode_text.setEnabled(False)
            self.x=self.spectro_thread.x
            self.lambda_min_label.setText("lambda min (nm)")
            self.lambda_max_label.setText("lambda max (nm)")
        elif self.abscisse_type_slider.value()==2:
            self.periode_text.setEnabled(False)
            self.x=1240/self.spectro_thread.x
            self.lambda_min_label.setText("Energy min (eV)")
            self.lambda_max_label.setText("Energy max (eV)")
        elif self.abscisse_type_slider.value()==3:
            self.periode_text.setEnabled(True)
            self.x=int(self.periode_text.text())/self.spectro_thread.x
            self.lambda_min_label.setText("Freq min (a/nm)")
            self.lambda_max_label.setText("Freq max (a/nm)")
        self.lambda_min_edit.setText(str(round(min(self.x),3)))
        self.lambda_max_edit.setText(str(round(max(self.x),3)))
        self.clear_spectrum()
        self.update_stackspectre()
        self.update_curseur_list()
        self.abscisse()
            
    def continuous_mode(self):
        self.continuous_check.setChecked(False)
        self.background_select.setChecked(False)
        self.paramchanged()
        
    def update_curseur_list(self):
        self.curseur_widget.clear()
        self.clear_spectrum()
        self.update_stackspectre()
        if self.curseurs!=[]:
            for i,Cur in enumerate(self.curseurs):
                if self.abscisse_type_slider.value()==1:
                    x=Cur[0]           
                if self.abscisse_type_slider.value()==2:
                    x=1240/Cur[0]
                elif self.abscisse_type_slider.value()==3:
                    x=int(self.periode_text.text())/Cur[0]
                self.curseur_axe.plot(x,Cur[1])
                label = "cursor" + str(i+1) + \
                        "  Position : x = " +str(round(x[1],2))+"   y :"+str("%.2e"% Cur[1][1])
                if i !=0:
                    delta_lambda = Cur[0][1]-self.curseurs[0][0][1]
                    delta_En = (1/self.curseurs[0][0][1]-1/Cur[0][1])*1e7
                    label+="  "+chr(916) + chr(955) + ' = '+ str(round(delta_lambda,2)) +\
                           " nm  "+ chr(916)+"En = " +str(round(delta_En)) + " cm-1"
                self.curseur_widget.addItem(label)
                self.nombre_curseur=i+1        
        self.spectro.draw()
        
    
    def addcurseur(self):
        x,y=np.asarray(self.crossline.get_data()[0]),np.asarray(self.crossline.get_data()[1])
        #Cursors are stored in nm
        #display is changed later
        if self.abscisse_type_slider.value()==2:
            x=1240/x
        elif self.abscisse_type_slider.value()==3:
            x=int(self.periode_text.text())/x
        self.curseurs.append([x,y])
        self.update_curseur_list()
        
    def remcurseur(self, item):
        self.listMenu= QMenu(self)
        self.remove = QAction("Remove Cursor")
        self.listMenu.addAction(self.remove)
        self.remove.triggered.connect(self.removeClicked)
        self.listMenu.popup(QCursor.pos())

    def removeClicked(self):
        curRow = self.curseur_widget.currentRow()
        self.curseur_widget.takeItem(curRow)
        del self.curseurs[curRow]
        self.nombre_curseur+=-1
        self.update_curseur_list()
    
class Spectro_Thread(QThread):
    
    spectredone=pyqtSignal(np.ndarray,int,float)
    spectrum_starting = pyqtSignal(float)
    acq_over = pyqtSignal()
      
    def __init__(self,parent,acq_time,avg):
        super(self.__class__,self).__init__(parent)
        self.spec=str()
        self.avg = avg
        self.int_time = acq_time
        self.x=np.arange(300,1000)
        self.spectre = self.x*0
        self.devices=devices                #On crée une liste des appareils
        self.liste=liste                    #On fait une liste pour nommer les spectro
        self.text=str()                     #Nom du spectro pour passer les param

        self.spectro_param(self.int_time)    
        self.continuous=False
        self.background=self.x*0
        self.background_check=False
        print('init spectro over')
    
    def spectro_list(self):
        self.liste.append('Dummy')
        liste=self.liste
        return liste
    
    def spectro_connect(self,text):
        
        if self.spec != str():
            self.stop()
        i=self.liste.index(text)
        if text=='not connected':
            print('no spectro is connected')
            self.spec=str()
            return
        elif text.find("Ocean Optics")!=-1:
            self.spec=sb.Spectrometer(self.devices[i][0])
        elif text.find("Thorlabs")!=-1:
            print(self.devices[i])
            self.spec=osat.Spectrometer(self.devices[i])
        else:
            self.spec=self.devices[i]
        self.text=text
        self.spectro_param(self.int_time)
        print('spectro {} connected'.format(text))
        
    def stop(self):
        print(self.spec != str())
        if self.spec != 'Dummy' and self.spec != str():
            self.spec.close()
            self.spec = str()
        print('test')
    
    def spectro_param(self,acq_time):
        self.int_time=acq_time
        if self.text.find("Ocean Optics")!=-1:
            self.spec.integration_time_micros(acq_time*10**6)
            self.x = self.spec.wavelengths()
            self.spectre = self.x*0
        elif self.text.find("Thorlabs")!=-1:
            self.spec.setIntegrationTime(acq_time)
            self.x = self.spec.wavelength
            self.spectre = self.x*0
        elif self.text=="Dummy":
            self.spec="Dummy"
            self.x=np.arange(300,1000)
            self.spectre = self.x*0
        self.parent().y=self.spectre
    
    @pyqtSlot()
    def run(self):
        before = time.time()
        if self.avg == 0: 
            self.avg=1
        for i in range(self.avg):
            if self.text=='Dummy':
                self.spectrum_starting.emit(self.int_time)
                spe=self.Dummy(self.int_time)
            elif self.text.find("Thorlabs")!=-1:
                # Spectrometer are started in continuous mode
                # first spectrum always takes twice the time, so no need to getSpectrum()
                # spectrometer needs to be stopped via stopscan()
                before = time.time()
                self.spectrum_starting.emit(self.int_time*4/5) #la barre de progression s'arrete à 80%
                print('test')
                if self.int_time > 0.3 :
                    spe = self.spec.getSpectrumCont()
                else :
                    #In continuous mode, the spectrometer can't go down to 10 µs
                    #single acquisition mode is used even if it means losing some time
                    #Refresh is limited to 20 spectra/s. Could probably go up to 30 spectra/s
                    spe = self.spec.getSpectrum()
            elif self.text.find("Ocean Optics")!=-1:
                if i==0:
                    self.spec.integration_time_micros(0.1*10**6)
                    self.spec.intensities(
                            correct_dark_counts=False, correct_nonlinearity=False)
                    self.spectro_param(self.int_time)
                    time.sleep(.1)
                self.spectrum_starting.emit(self.int_time)
                before = time.time()
                spe = self.spec.intensities(
                    correct_dark_counts=False, correct_nonlinearity=False)
            if self.background_check :
                spe = spe - self.background
            else :
                spe = spe
            self.spectre = (self.spectre*(i)+spe)/(i+1)
            self.y=self.spectre
            after=time.time()
            self.spectredone.emit(self.y,i+1,round(after-before,3))
        
        if self.continuous:
            self.run()
        elif self.text.find("Thorlabs")!=-1:
            if self.int_time >0.3 :
                #Pour enlever le spectro du mode continu, on donne une commande stopscan qui
                #demande un nouveau scan. On change donc le temps d'integration avant
                #de demander ce scan et on le remet après
                self.spec.setIntegrationTime(0.1)
                self.spec.stopscan()
                time.sleep(min(0.5,self.int_time))
                self.spec.getSpectrum()
                self.spec.setIntegrationTime(self.int_time)
            else:
                #Refresh is limiter to 20 spectra/s
                if after-before < 0.05 :
                        time.sleep(0.05-after-before)
            self.acq_over.emit()
        else :
            #On n'a pas besoin d'arreter le spectro 'sea' parce qu'il n'est pas lancé en continu
            self.acq_over.emit()
     
    def Dummy(self,acq_time):
        import random
        nombreDeBase = random.randint(1,300)
        y = acq_time*np.sin((self.x+nombreDeBase)/100)
        time.sleep(acq_time)
        return y

            
class Save(QWidget):
    
    def __init__(self,parent):
        super().__init__(parent)
        self.savepath = os.getcwd()
        self.Layout()
        self.connect()
        
    def Layout(self):
        self.save_layout = QGridLayout()
        self.save_spectrum_button = QPushButton ('Save Spectrum')

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
        self.save_note.append("User :")
        self.save_note.append("Sample :" )
        self.save_note.append("Comments :")
        self.save_note.setMaximumHeight(100)
        
        #Save Layout
        self.save_layout.addWidget(self.file_loc,0,0,1,2)
        self.save_layout.addWidget(self.location_button,0,2)
        self.save_layout.addWidget(self.prefix_file_name,1,0,1,2)
        self.save_layout.addWidget(self.File_number,1,2)
        self.save_layout.addWidget(self.save_spectrum_button,0,3)
        self.save_layout.addWidget(self.save_note,0,4,3,3)
        
        self.setLayout(self.save_layout)
    
    def connect(self):
        self.file_loc.textChanged.connect(self.changesavepath)
        self.location_button.clicked.connect(self.opensaveloc)
        self.save_spectrum_button.clicked.connect(self.save_spectrum)

    def opensaveloc(self): 
        #https://pythonprogramming.net/file-saving-pyqt-tutorial/
        file_name=self.filename() 
        file_name = QFileDialog.getSaveFileName(self, 'Save File',file_name,".npz")[0]
        if not file_name:
            return
        notes = self.save_note.toPlainText()+ "\n"+ "\n"

        np.savez(file_name, notes=notes, lambdas=self.parent().Spectro.x,\
                     signal=self.parent().Spectro.stack_spectre[1:], acq=self.parent().Spectro.int_time,\
                     nmoy=self.parent().Spectro.avg)
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
                                            "The file is already existing, Do you want to overwrite it ?", QMessageBox.Yes | 
               QMessageBox.No, QMessageBox.No)             
               if reply == QMessageBox.Yes:
                   return True
               else:
                   return False
        except IOError:
            return True
    
    def save_spectrum(self):
        reply = QMessageBox.question(self, 'Message',\
                                            "DO you want to save current spectrum ?", QMessageBox.Yes | 
                                            QMessageBox.No, QMessageBox.No)             
        if reply == QMessageBox.Yes:
            self.parent().Spectro.add_spectrum()
        else:
            pass
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
        np.savez(file_name, notes=notes, lambdas=self.parent().Spectro.x,\
                     signal=self.parent().Spectro.stack_spectre[1:], acq=self.parent().Spectro.int_time,\
                     nmoy=self.parent().Spectro.avg)
        self.numfile+=1
        self.File_number.setValue(self.File_number.value()+1)
   
    def filename(self):
        file_name=self.prefix_file_name.text()+str(self.File_number.value())+ '.npz'
        if self.savepath:
            return os.path.join(self.savepath, file_name)
        return file_name
    
    def changesavepath(self):
        self.savepath = self.file_loc.text()

class Progressbar(QThread):
    finish = pyqtSignal(float)
    
    def __init__(self, parent,int_time):
        super(self.__class__,self).__init__(parent)
        self.int_time=int_time
        
    @pyqtSlot()
    def run(self):
        int_time=self.int_time
        if self.int_time < 0.4:
            return
        ti=0
        total = int_time
        i=min(total/20,0.2)
        while ti<total:
            ti+=i
            prog=round(ti/total*100,2)
            time.sleep(i*4/5) #Acquisition time is fine, but the bar stops at 80%. Unfinished bat stacks and finish their process at the end which is annoying.
            self.finish.emit(prog)


def main():
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance() 
    prog = Fenetre() 
    prog.show()
    app.aboutToQuit.connect(app.deleteLater)
    app.exec_()
    app.quit()

    
if __name__ == '__main__':
    main()
