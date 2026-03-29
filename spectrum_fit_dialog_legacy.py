#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  9 10:42:54 2018

@author: leonard

Legacy fitting dialog kept as a historical reference.
The active implementation is `spectrum_fit_dialog.py`.

Module for fitting data.

contains class functions as Gaussian, Fano, Lorentz, and Polynom.
The purpose of thess classes is to use the function to fit data.
The parameters are stored to serve as seed for the fit function and are to be replaced by the output of the fit after it


"""
from PyQt5.QtWidgets import QLineEdit,QLabel,QAction,QPushButton,QSpinBox, QComboBox, QProgressBar, QRadioButton, QListWidget
from PyQt5.QtWidgets import QTextEdit,QCheckBox,QMessageBox,QFileDialog,QStyle, QMenu, QWidgetAction, QSlider
from PyQt5.QtWidgets import QDialog,QMainWindow,QWidget,QApplication,QDesktopWidget,QGridLayout,QVBoxLayout,QHBoxLayout
from PyQt5.QtCore import pyqtSignal,QThread,pyqtSlot,Qt
from PyQt5.QtGui import QIcon, QFont, QCursor
import os, sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from scipy.optimize import curve_fit
from functools import partial



class Fenetre (QMainWindow):
    
    def __init__(self,x,y,value):
        super(Fenetre,self).__init__()
        self.x=x
        self.y=y
        self.value=value
        self.resize(1000, 800)
        self.center()
        self.initUI() 
    
    def initUI(self):    
        '''initiates application UI'''
        self.Create_Layout() 
        self.statusBar().showMessage('Ready')        
        self.menu()
        self.setWindowTitle('Spectro_fit')    
        ###################################################################"

    def Create_Layout(self):
        self.CentralWidget = Main(self,self.x,self.y,self.value)
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
    
    def __init__(self,parent,x,y,value):
        super().__init__(parent)
        self.x=x
        self.y=y
        self.value=value
        self.repertoire = "/home/xavier/Python/CP_angles/"    
        self.Layout()
        self.connect()
        
    def Layout(self):
        self.MainLayout=QVBoxLayout()
        self.Widgets=[Spectro_fit(self,self.x,self.y,self.value)]
        self.MainLayout.addWidget(self.Widgets[0])
        self.setLayout(self.MainLayout)
    
    def connect(self):
        return
    
    def close(self):
        for Widgets in self.Widgets:
            print(Widgets)
            Widgets.stop()

class Spectro_fit(QWidget):
    
    def __init__(self,parent,x,y,value):
        super().__init__(parent)
        print('spectro_fit')
        self.x_nm=x
        self.x=self.x_nm
        self.fit_x=self.x
        self.stack_spectre = np.asarray(y)
        self.value = value
        self.y=self.stack_spectre[0]
        self.cross = False
        self.cross_coord=[0,0]
        self.curseur = False
        
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
        
    def Layout(self):
        #Spectro parameters Layout (Vbox)
        self.spectro_layout = QVBoxLayout()
        self.central_layout = QHBoxLayout()
        self.bottom_layout = QHBoxLayout()
        self.button_layout = QHBoxLayout()
        self.central_right_widget = QWidget()
        self.central_right_widget.setMaximumWidth(120)
        self.central_right_layout = QVBoxLayout()
        self.central_left_layout = QGridLayout()
        
        self.lambda_min_edit = QLineEdit(str(int(self.x[0])))
        self.lambda_max_edit = QLineEdit(str(int(self.x[-1])))
        self.lambda_min_label = QLabel("lambda min (nm)")
        self.lambda_max_label = QLabel("lambda max (nm)")
        
        #Spectro
        self.fig = plt.Figure()
        self.spectro = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.spectro, None)
        self.axes = self.fig.add_subplot(111)
        self.curseur_axe=self.fig.add_subplot(111)
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
        self.curseur_widget.setFixedWidth(400)
        self.nombre_curseur=0
        self.curseurs=[]
        
        #Fit Widget
        self.sommefitline,=self.axes.plot(self.fit_x,self.fit_x*0)
        self.fitline=[self.sommefitline]
        self.fitLayout = QGridLayout()
        self.nofunctionLab = QLabel('noFunction')
        self.function = []
        self.fitLayoutUpdate()
        
        
        #Active Spectrum and display number
        self.activespecWidget=QWidget()
        self.activespecWidget.setMaximumWidth(80)
        self.activespecLayout=QVBoxLayout()
        self.activSlider=QSlider()
        self.activSlider.setRange(1,2)
        self.activSlider.setTickInterval(1)
        self.activSlider.setSingleStep(1)
        self.activSlider.setValue(self.value)
        self.activSlider.setTickPosition(QSlider.TicksLeft)
        self.activSlider.setOrientation(Qt.Vertical)
        self.numdisplayLabel=QLabel('# of spectra \n shown')
        self.numdisplayLabel.setAlignment(Qt.AlignCenter)
        self.numdisplayLabel.setFont(self.font_text)
        self.numdisplayLabel.setFixedWidth(60)
        self.numdisplayEdit=QLineEdit('1')
        self.numdisplayEdit.setFixedWidth(60)
        self.currentposLabel=QLabel('Current \n position')
        self.currentposLabel.setAlignment(Qt.AlignCenter)
        self.currentposLabel.setFont(self.font_text)
        self.currentposLabel.setFixedWidth(60)
        self.currentposSpin=QSpinBox()
        self.activespecLayout.addWidget(self.numdisplayLabel)
        self.activespecLayout.addWidget(self.numdisplayEdit)
        self.activespecLayout.addWidget(self.currentposLabel)
        self.activespecLayout.addWidget(self.currentposSpin)
        self.activespecLayout.addWidget(self.activSlider)
        self.activespecWidget.setLayout(self.activespecLayout)
        self.activespecWidget.setHidden(True)
        print(len(self.stack_spectre))
        if len(self.stack_spectre) >= 2:
            self.activespecWidget.setHidden(False)
            self.currentposSpin.setMaximum(len(self.stack_spectre))
            self.activSlider.setRange(1,len(self.stack_spectre))
            self.activSlider.setValue(self.value)
            self.update_stackspectre()
        
        self.central_layout.addLayout(self.central_left_layout)
        self.spectroLayout=QHBoxLayout()
        
        self.spectroLayout.addWidget(self.activespecWidget)
        self.spectroLayout.addWidget(self.spectro)
        self.central_left_layout.addLayout(self.spectroLayout,0,0,1,4)
        self.central_left_layout.addWidget(self.progress,1,0,1,2)
        
        self.central_right_layout.addWidget(self.go_button)
        self.central_right_layout.addWidget(self.autozoom_button)
        self.central_right_layout.addWidget(self.zoom_button)
        self.central_right_layout.addWidget(self.add_curseur)
        self.central_right_layout.addLayout(self.abscisse_type_layout)
        self.central_right_layout.addStretch(-1)
        
        self.central_right_widget.setLayout(self.central_right_layout)
        
        self.central_layout.addWidget(self.central_right_widget)
       
        self.bottom_layout.addWidget(self.lambda_min_label)
        self.bottom_layout.addWidget(self.lambda_min_edit)
        self.bottom_layout.addWidget(self.lambda_max_label)
        self.bottom_layout.addWidget(self.lambda_max_edit)
        
        self.underLayout=QHBoxLayout()
        self.underLayout.addWidget(self.curseur_widget)
        self.underLayout.addLayout(self.fitLayout)
        
        self.spectro_layout.addLayout(self.central_layout)
        self.spectro_layout.addLayout(self.bottom_layout)
        self.spectro_layout.addLayout(self.underLayout)
        self.spectro_layout.addLayout(self.button_layout)
        
        self.setLayout(self.spectro_layout)
    
    def connect(self):
        self.abscisse_type_slider.valueChanged.connect(self.abscisse_type)
        self.periode_text.returnPressed.connect(self.abscisse_type)
        self.lambda_max_edit.returnPressed.connect(self.abscisse)
        self.lambda_min_edit.returnPressed.connect(self.abscisse)
        self.coord = self.spectro.mpl_connect('button_press_event', self.onclick)
        self.go_button.clicked.connect(self.Go_fit)
        self.add_curseur.clicked.connect(self.addcurseur)
        self.curseur_widget.itemClicked.connect( self.remcurseur)
        self.zoom_button.clicked.connect(self.zoom)
        self.autozoom_button.clicked.connect(self.Autozoom)
        self.activSlider.valueChanged.connect(self.update_stackspectre)
        self.numdisplayEdit.returnPressed.connect(self.update_stackspectre)
        self.currentposSpin.valueChanged.connect(self.update_activSlider)
        return
    
    def MenuBar(self,Menu):
        FittingMenu = Menu.addMenu('&Fitting')
        
        FitAct = QAction('Fit',self)
        FitAct.setShortcut('Ctrl+N')
        FitAct.setStatusTip('Fit the data')
        #FitAct.triggered.connect(self.fit)
        FittingMenu.addAction(FitAct)
        
        AddFuncMenu = FittingMenu.addMenu('&Add Function')
        for i in Function.__subclasses__():
            addFuncAct = QAction(i.__name__,self)
            addFuncAct.setStatusTip('Add a {} function to the fit'.format(i.__name__))
            addFuncAct.triggered.connect(partial(self.addFitFunction,func=i))
            AddFuncMenu.addAction(addFuncAct)
        return
    
    def addFitFunction(self,func):
        if func.__name__ != 'Polynom':
            x0=round((self.axes.get_xlim()[1]+self.axes.get_xlim()[0])/2,2)
            Gamma = round(self.axes.get_xlim()[1]-self.axes.get_xlim()[0],2)/4
            A = round(self.axes.get_ylim()[1]-self.axes.get_ylim()[0],2)/2
            Newfunc=func(x0,Gamma,A)
            self.function.append(Newfunc)
            newline,=self.axes.plot(self.x,Newfunc.function(self.x,*Newfunc.param),zorder=5)
            self.fitline.append(newline)
            self.fitLayoutUpdate()
        else:
            n=2
            array=[1,1,1]
            Newfunc=Polynom(n,array)
            self.function.append(Newfunc)
            newline,=self.axes.plot(self.x,Newfunc.function(self.x,*Newfunc.param),zorder=5)
            self.fitline.append(newline)
            self.fitLayoutUpdate()
    
    def stop(self):
        return
    
    def abscisse(self):
        self.axes.set_xlim(float(self.lambda_min_edit.text()),float(self.lambda_max_edit.text()))
        self.spectro.draw()
        
    def abscisse_type(self):
        """ Allow to change the abscisse axis to nm, eV or normalized frequency (NF)"""
        if self.abscisse_type_slider.value()==1:
            self.periode_text.setEnabled(False)
            self.x=self.x_nm
            self.lambda_min_label.setText("lambda min (nm)")
            self.lambda_max_label.setText("lambda max (nm)")
        elif self.abscisse_type_slider.value()==2:
            self.periode_text.setEnabled(False)
            self.x=1240/self.x_nm
            self.lambda_min_label.setText("Energy min (eV)")
            self.lambda_max_label.setText("Energy max (eV)")
        elif self.abscisse_type_slider.value()==3:
            self.periode_text.setEnabled(True)
            self.x=int(self.periode_text.text())/self.x_nm
            self.lambda_min_label.setText("Freq min (a/nm)")
            self.lambda_max_label.setText("Freq max (a/nm)")
        self.lambda_min_edit.setText(str(round(min(self.x),3)))
        self.lambda_max_edit.setText(str(round(max(self.x),3)))
        self.clear_spectrum()
        self.update_stackspectre()
        self.update_curseur_list()
        self.abscisse()
    
    def fitLayoutLign(self,function,lignnumber,parammax,totallign):
        funcLabel=QLabel(function.name)
        self.fitLayout.addWidget(funcLabel,lignnumber+1,0,1,2)
        col=2
        for i,(n,m) in enumerate(zip(function.paramnames,function.param)):
            paramlabel = QLabel(n)
            paramEdit = QLineEdit(str(round(m,2)))
            paramEdit.returnPressed.connect(partial(self.updatefunction,function=function,i=i))
            self.fitLayout.addWidget(paramlabel,lignnumber+1,col)
            col+=1
            self.fitLayout.addWidget(paramEdit,lignnumber+1,col)
            col+=1
        fixCheck=QCheckBox()
        deleteCheck=QCheckBox()
        self.fitLayout.addWidget(fixCheck,lignnumber+1,parammax*2+3)
        self.fitLayout.addWidget(deleteCheck,lignnumber+1,parammax*2+4)
        
    def updatefunction(self,function,i):
        if function.name == "Polynom function" and i==0:
            value=self.sender().text()
            function.n=int(value)
            function.reinit()
            #print(function)
            self.fitLayoutUpdate()
        else:
            value=self.sender().text()
            function.param[i]=float(value)
            #print(function.param)
            #print(function)
        self.drawfitfunctions()
        
    def drawfitfunctions(self):
        for i,func in enumerate(self.function):
            self.fitline[i+1].set_data(self.fit_x,func.function(self.fit_x,*func.param))
            #plt.figure();plt.plot(self.x,func.function(self.x,*func.param))
        arg=[param for func in self.function for param in func.param]
        #print(*arg)
        if self.function != []:
            self.sommefitline.set_data(self.fit_x,functionsomme(self.fit_x,*arg,function=self.function))
            #plt.figure();plt.plot(self.x,functionsomme(self.x,*arg,function=self.function))
        self.spectro.draw()
        #print('test')
                
    def fitLayoutUpdate(self):
        for i in range(self.fitLayout.count()): self.fitLayout.itemAt(i).widget().close()
        if self.function == []:
            func = Function(X0=0,X1=1,X2=2,X3=3)
            self.fitLayoutLign(func,0,4,1)
            parammax=4
        else :
            parammax=max([len(func.param) for func in self.function])
            for i,func in enumerate(self.function):
                self.fitLayoutLign(func,i+1,parammax,len(self.function))
                
        self.fitLabel1 = QLabel('functions')
        self.fitLabel2 = QLabel('Parameters')
        self.fitLabel3 = QLabel('Fix')
        self.fitLabel4 = QLabel('Delete')
        self.fitLayout.addWidget(self.fitLabel1,0,0,1,2)
        self.fitLayout.addWidget(self.fitLabel2,0,2,1,parammax*2)
        self.fitLayout.addWidget(self.fitLabel3,0,parammax*2+3)
        self.fitLayout.addWidget(self.fitLabel4,0,parammax*2+4)
        self.drawfitfunctions()
        
    
    def Go_fit(self):
        print('fittig !')
        bornesmin=(np.abs(self.x - self.axes.get_xlim()[0])).argmin()
        bornesmax=(np.abs(self.x - self.axes.get_xlim()[1])).argmin()
        Emin=min(self.x[bornesmin],self.x[bornesmax])
        Emax=max(self.x[bornesmin],self.x[bornesmax])
        step=(Emax-Emin)/500
        bornes=np.arange(bornesmin,bornesmax)
        y=self.line.get_ydata()
        a,b=fit(self.x,y,bornes,function=self.function)
        start=0
        end=0
        for func in self.function:
            end+=len(func.param)
            func.param=a[0][start:end]
            start=end
        print(self.function)
        self.fit_x=np.arange(Emin,Emax,step)
        print(Emin,Emax)
        self.fitLayoutUpdate()
        
        return
    
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
        
    def Autozoom(self):
        y=self.line.get_ydata()
        self.axes.set_ylim(np.min(y),np.max(y))
        self.spectro.draw()
    
    def zoom(self):
        self.toolbar.zoom()
        
    def update_spectrum(self,spectre):
        self.y=spectre
        self.line.set_ydata(self.y)
        self.curseur_axe.set_ylim(self.axes.get_ylim())
        self.spectro.draw()
    
    def add_spectrum(self):
        if 0 in self.stack_spectre.shape :
            self.stack_spectre = np.append(self.spectro_thread.x.reshape(1,-1),\
                                           self.y.reshape(1,-1),axis=0)
        else:
            self.stack_spectre = np.append(self.stack_spectre,self.y.reshape(1,-1),axis=0)   
        if len(self.stack_spectre) == 3:
           self.activespecWidget.setHidden(False)
        self.activSlider.setRange(1,len(self.stack_spectre))
        self.activSlider.setValue(len(self.stack_spectre))
        self.currentposSpin.setMaximum(self.currentposSpin.maximum+1)
        self.update_stackspectre()
        
    def update_stackspectre(self):
        value=self.activSlider.value()
        self.currentposSpin.setValue(value)
        displayrange = min(value-1,int(self.numdisplayEdit.text()))
        start= value-displayrange
        finish= value
        #print(value,start,finish)
        if not 0 in self.stack_spectre.shape :
            self.clear_spectrum()
            for i in self.stack_spectre[start:finish]:
                self.axes.plot(self.x,i)
            self.line.set_ydata(self.stack_spectre[finish-1])
        self.drawfitfunctions()
        self.spectro.draw()
                
    def clear_spectrum(self):
        limy=self.axes.get_ylim()
        limx=self.axes.get_xlim()
        self.axes.cla()
        #self.line has to be redifined or the spectrum won't show anymore
        self.line,=self.axes.plot(self.x,self.y,zorder=5)
        #same with self.crossline
        self.crossline, = self.axes.plot(self.coord_cross[0],self.coord_cross[1])
        self.sommefitline,=self.axes.plot(self.fit_x,self.fit_x*0)
        for i,_ in enumerate(self.fitline):
            self.fitline[i]=self.axes.plot(self.fit_x,self.fit_x*0)[0]
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
    
    def update_activSlider(self):
        self.activSlider.setValue(int(self.currentposSpin.value()))


# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total: 
        print()
        
        
def filtre_gauss(decalx,decaly,d,f,kx,ky,posx,posy,largefx,largefy):
    r""" Defini la somme de gaussienne qui sera enlevée de l'espace reciproque lors du filtre du diagramme de bande
    
    Parameters
    -------------
    decalx : int
        decalage sur l'axe horizontal
    decaly : int
        decalage sur l'axe vertical
    d : int
        premier point à enlever (0 = sur l'axe)
    f : int
        dernier point à enlever
    kx :
        
    ky :
        
    posx :
        
    posy :
        
    largefx :
        
    largefy :
        
    
    Returns
    ------------
    filtre :
    """
    filtre=1
    for  i in range(d,f):
        gauss = 1-(np.exp(-(((kx[np.newaxis,:]-posx*i-decalx)/largefx)**2+((ky[:,np.newaxis]-posy*i-decaly)/largefy)**2)) + \
                   np.exp(-(((kx[np.newaxis,:]+posx*i+decalx)/largefx)**2+((ky[:,np.newaxis]+posy*i+decaly)/largefy)**2)) )
        filtre=filtre*gauss
    return filtre

def kpara(theta,omega):
    r""" Donne la valeur de k parallele en fonction de l'angle et de l'energie normalisée
    
    .. math:: \omega\sin(\theta\frac{\pi}{180})
    
    Parameters
    ----------
    theta : float
        angle
    omega : float
        frequence normalisée
        
    Returns
    ---------
    kpara
    """
    return np.sin(theta*np.pi/180)/(1/omega)

def inverse(x,x0,A):
    return A/(x-x0)

class Function():
    """Generic class to define the functions
    Other function will inherite from this class"""
    
    def __init__(self,**kwargs):
        self.Initarg = {}
        for k,v in kwargs.items():
            self.Initarg[k] = v
        self.reinit()
        #self.param = [*args]
        self.reprname = "Generic function Class "
        self.name = "No Function : "
    
    def function(self, *args):
        print("this is a generic function")
        print("you need to define a nex function")
        return
    
    def get_values(self):
        return self.param
    
    def reinit(self):
        '''Reinitialize the values of the parameter to the original called ones
        returns self'''
        self.param=[i for i in self.Initarg.values()]
        self.paramnames = [i for i in self.Initarg.keys()]
        return self
    
    def __repr__(self):
        string=self.reprname + " Params={}".format(str(self.param))
        return string
    
    def __str__(self):
        string = self.name + " Parameters are  " + ", ".join(["=".join([i,str(j)]) for i,j in zip(self.paramnames,self.param)])
        return string


class Sin(Function):
    r""" Sin class to generate a sin function.
    
    """
    def __init__(self,x0,Omega,A):
        super().__init__(x0=x0,Omega=Omega,A=A)
        self.name = 'Sin function'
        self.reprname = self.name
        
    def function(self,x,x0,Omega,A):
        r""" Fonction sinus
        .. math:: A*\sin{\omega*(x-x_0)}
        """
        return A*np.sin(Omega*(x-x0))


class Fano(Function):
    r""" Fano class to generate a fano profil function.
    
    """
    def __init__(self,x0,Gamma,A,q=10):
        super().__init__(x0=x0,Gamma=Gamma,A=A,q=q)
        self.name = 'Fano function'
        self.reprname = self.name
        
    def function(self,x,x0,Gamma,A,q):
        r""" Fonction Fano
        .. math:: \frac{A(q.\Gamma+2*(x-x0))}{(\Gamma^2+4*(x-x0)^2)}
        """
        num=q*Gamma + 2*(x-x0)
        denom=Gamma**2 + 4*(x-x0)**2
        return A/q**2*(num**2/denom)
    
    
class Gaussian(Function):
    r""" non-normalized Gaussian class to generate a gaussian function.
    
    """
    def __init__(self,x0,Gamma,A):
        super().__init__(x0=x0,Gamma=Gamma,A=A)
        self.name = 'Gaussian function'
        self.reprname = self.name
        
    def function(self,x,x0,Gamma,A):
        r""" Fonction Gaussian
        
        .. math:: A*e^{\frac{-(x-x_0)^2}{2*\Gamma^2}}
        
        """
        expo=-(x-x0)**2/(2*Gamma**2)
        norm=A
        return norm*np.exp(expo)
    

class GaussianNorm():
    r""" non-normalized Gaussian class to generate a gaussian function.
    
    """
    def __init__(self,x0,Gamma,A):
        super().__init__(x0=x0,Gamma=Gamma,A=A)
        self.name = 'Norm. Gaussian function'
        self.reprname = self.name
        
    def function(self,x,x0,Gamma,A):
        r""" Fonction Gaussian
        
        .. math:: \frac{A}{\Gamma*\sqrt{2}*\pi}*e^{\frac{-(x-x_0)^2}{2*\Gamma^2}}
        
        """
        expo=-(x-x0)**2/(2*Gamma**2)
        norm=A/(Gamma*np.sqrt(2)*np.pi)
        return norm*np.exp(expo)

class Lorentz(Function):
    r""" Lorentz class to generate a lorentzian function.
    
    """
    def __init__(self,x0,Gamma,A):
        super().__init__(x0=x0,Gamma=Gamma,A=A)
        self.name = 'Lorentz function'
        self.reprname = self.name
        
    def function(self,x,x0,Gamma,A):
        r""" Fonction Lorentz
        
        .. math:: a+bx+cx^2+ \frac{A}{1+4*(x-x0)^2/\Gamma^2}
        
        """
        num=A
        denom=1+4*((x-x0)/Gamma)**2
        return num/denom


class Polynom(Function):
    r""" Polynom class to generate a polynomial function.
    
    """
    def __init__(self,n=1,array=[1,1]):
        self.n=n
        self.Initarg = {'n':self.n}
        self.array=array
        for i,x in enumerate(self.array):
            self.Initarg['x'+str(self.n-i)] = x
        self.reinit()
        super().__init__(**self.Initarg)
        self.name="Polynom function"
        self.reprname=self.name
    
    
    
    def function(self,x,*args):
        r""" Fonction polynom of degree n
        """
        return np.poly1d(args[1:])(x)
    
    def reinit(self):
        '''Reinitialize the values of the parameter to the original called ones
        returns self'''
        self.Initarg = {'n':self.n}
        if len(self.array)<self.n+1:
            while len(self.array)!=self.n+1: self.array.append(1) 
        elif len(self.array)>self.n+1:
            self.array=self.array[:self.n+1]
        for i,x in enumerate(self.array):
            self.Initarg['x'+str(self.n-i)] = x
        self.param=[i for i in self.Initarg.values()]
        self.paramnames = [i for i in self.Initarg.keys()]
        return self
    
    def __str__(self):
        pol=[]
        for i in range(self.n+1):
            pol.append('{}*x^{}'.format(self.param[i+1],self.n-i))
        string=self.name + " of degree {}. Polynom ={}".format(self.n,' + '.join(pol))
        return string

def functionsomme(x,*args,**kwargs):
    start=0
    end=0
    fitmul=0
    for func in kwargs['function']:
        end+=len(func.param)
        fitmul = fitmul + func.function(x,*args[start:end])
        start=end
    return fitmul 
        
def fit(FREQ,sig,bornes,function=[Fano(1,1,1,1)]):
    bestv=[]
    fit=[]
    Emin=min(FREQ[bornes[0]],FREQ[bornes[-1]])
    Emax=max(FREQ[bornes[0]],FREQ[bornes[-1]])
    step=(Emax-Emin)/500
    seed=[]
    funcfit=[]
    for func in function:
        for param in func.param:
            seed.append(param)
        funcfit.append(func)
    #print(seed)
    def fitfit(x,*args):
        return functionsomme(x,*args,function=funcfit)
    a,b=curve_fit(fitfit,FREQ[bornes],sig[bornes],seed,maxfev=500000)
    bestv=[a]
    fit.append(fitfit(np.arange(Emin,Emax,step),*a))
    bestv=np.asarray(bestv).reshape(1,len(seed))
    return bestv,fit
    

def plot_fit(FREQ,function,sig,table,bornes,delta=0.003,shift=True,initfunc=True):
    r""" Fit un ensemble de courbe. (optionel trace les courbes fittées dans une figure)
    
    Parameters
    ------------
    FREQ : array_like
        abscisse pour le fit (e.g fit en energie à un angle donnée FREQ = energie; fit en angle a une energie donnée FREQ = angles)
    function : array of object from class functions
        ex : [Fano(800,10,10,10),Lorentz(10,20,30)]
    sig : array
        données à fitter. 
        Typiquement le diagramme de bande complet. La selection des courbes à fitter se fait dans la variable "table"
    table : array
        tableau contenant l'ensemble des numéros des courbes à fitter 
        (ex: np.arange(30,50) va fitter les courbes à partir de la 31eme jusqu'à la 51eme de l'ensemble donné dans sig)
    bornes : array
        tableau contenant les N points sur lequel le fit va être effectué de la forme np.arange(Pixel1,PixelN)
    seed : array
        tableau contenant les seed pour le premier fit. Les suivants sont réalisés de proches en proches en se resservant de la sortie du fit précédant comme seed.
    plot : {False,True}, optional
        False (Défaut) ne trace pas le résultat du fit; True trace les données et le fit de chaque courbe dans une unique figure
    delta : float, optional
        indique l'écart entre la valeur de x0 trouvé pour le fit et les bornes pour el fit suivant ([x0-delta;x0+delta])
    shift : {True,False}, optional
        True : shift les bornes entre chaque fit; False : garde les bornes initiales entre chaque fit
    
    
    
    Returns
    ---------
    table : array
        identique à l'entrée
    bestval : array
        tableau contenant l'ensemble des paramètres de fit obtenus pour la série de courbe
    Q : array
        tableau contenant l'ensemble des facteurs de qualité obtenus pour la série de courbe
    yfit : array
        tableau contenant l'ensemble des courbes de fit
    """
    bestval=[] 
    yfit=[]
    Q=[]
    print(len(sig),'bornes= ',FREQ[bornes[0]],' ',FREQ[bornes[-1]])
    if initfunc:
        for func in function:
            func.reinit()
    for n,i in enumerate(table):
        a,b=fit(FREQ,sig[i],bornes,function=function)
        start=0
        end=0
        for func in function:
            end+=len(func.param)
            func.param=a[0][start:end]
            start=end
        bestval.append(a)
        yfit.append(b)
        Q.append(abs(bestval[n][0][0]/bestval[n][0][1]))
        Emin=min(FREQ[bornes[0]],FREQ[bornes[-1]])
        Emax=max(FREQ[bornes[0]],FREQ[bornes[-1]])
        #print(seed[0])
        if shift == True:
            Em=(np.abs(FREQ-a[0][0]-delta)).argmin()
            #print(Em)
            EM=(np.abs(FREQ-a[0][0]+delta)).argmin()
            #print(EM)
            bornes=np.arange(min(Em,EM),max(Em,EM))
        printProgressBar(n + 1, len(table), prefix = 'Fit in Progress:', suffix = 'Complete', length = 50)
    bestval=np.asarray(bestval).reshape(-1,len(a[0]))
    return table,bestval,Q,yfit

def main():
    global app
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    x=np.arange(300,1000)
    y=[1+np.sin(x/50+i/2) for i in range (0,10)]
    value=5
    prog = Fenetre(x,y,value) 
    prog.show()
    app.exec_()
    app.quit()

if __name__ == '__main__':
    main()