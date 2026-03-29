#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  9 10:42:54 2018

@author: leonard

Spectro Fit version 2.

Spectra are now objects with associated function to draw them.
Spectra objects store abscisses, ordinates, fitting functions and filtered spectra

Defines the class Function from which are subclassed other functions as Gaussian, Fano, Lorentz, and Polynom.
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
    
    def __init__(self,spectra,value):
        super(Fenetre,self).__init__()
        self.spectra=spectra
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
        self.CentralWidget = Main(self,self.spectra,self.value)
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
            if __name__ == '__main__':
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
    
    def __init__(self,parent,spectra,value):
        super().__init__(parent)
        self.spectra = spectra
        self.value=value
        self.repertoire = "/home/xavier/Python/CP_angles/"    
        self.Layout()
        self.connect()
        
    def Layout(self):
        self.MainLayout=QVBoxLayout()
        self.Widgets=[Spectro_fit(self,self.spectra,self.value)]
        self.MainLayout.addWidget(self.Widgets[0])
        self.setLayout(self.MainLayout)
    
    def connect(self):
        return
    
    def close(self):
        for Widgets in self.Widgets:
            print(Widgets)
            Widgets.stop()

class Spectro_fit(QWidget):
    
    def __init__(self,parent,stack_spectre,value):
        super().__init__(parent)
        print('spectro_fit')
        self.stack_spectre = stack_spectre
        self.value = value
        self.spectre=self.stack_spectre[self.value-1]
        self.x_nm=self.spectre.nm
        self.x=self.x_nm
        self.fit_x=self.x
        self.fit_target_value = self.value
        self.fit_target_axis_mode = 1
        self.fit_function_number = 0
        self.cross = False
        self.cross_coord=[0,0]
        self.curseur = False
        self.periode = self.spectre.periode
        
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
        self.curseur_axe = self.axes
        self.line, = self.spectre.plot(self.x,self.axes,zorder=5)
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
        self.abscisse_type_slider.setSingleStep(1)
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
        self.go_button = QPushButton("Fit !")
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
        self.fitaxes = self.axes
        self.sommefitline,=self.fitaxes.plot([], [], zorder=10)
        self.fitline=[self.sommefitline]
        #print(self.fitline[0])
        self.fitLayout = QGridLayout()
        self.nofunctionLab = QLabel('noFunction')
        self.function = []
        self.formula_label = QLabel('Current fitted model')
        self.formula_label.setFont(self.font_title)
        self.formula_fig = plt.Figure(figsize=(4.2, 2.4))
        self.formula_canvas = FigureCanvas(self.formula_fig)
        self.formula_canvas.setMinimumWidth(360)
        self.formula_canvas.setMaximumHeight(220)
        
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
        
        if len(self.stack_spectre) >= 2:
            self.activespecWidget.setHidden(False)
            self.currentposSpin.setMaximum(len(self.stack_spectre))
            self.activSlider.setRange(1,len(self.stack_spectre))
            self.activSlider.setValue(self.value)
            self.clear_spectrum()
            self.update_window()
        #self.fitLayoutUpdate()
        self.underLayout=QHBoxLayout()
        self.fitInfoLayout = QVBoxLayout()
        self.fitInfoLayout.addLayout(self.fitLayout)
        self.fitInfoLayout.addWidget(self.formula_label)
        self.fitInfoLayout.addWidget(self.formula_canvas)
        self.underLayout.addWidget(self.curseur_widget)
        self.underLayout.addLayout(self.fitInfoLayout)
        
        self.spectro_layout.addLayout(self.central_layout)
        self.spectro_layout.addLayout(self.bottom_layout)
        self.spectro_layout.addLayout(self.underLayout)
        self.spectro_layout.addLayout(self.button_layout)
        
        self.setLayout(self.spectro_layout)
        self.update_formula_panel()
    
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
        self.activSlider.valueChanged.connect(self.update_window)
        self.numdisplayEdit.returnPressed.connect(self.update_window)
        self.currentposSpin.valueChanged.connect(self.update_activSlider)
        return
    
    def MenuBar(self,Menu):
        FittingMenu = Menu.addMenu('&Fitting')
        
        FitAct = QAction('Fit',self)
        FitAct.setShortcut('Ctrl+N')
        FitAct.setStatusTip('Fit the data')
        FitAct.triggered.connect(self.Go_fit)
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
            self.spectre.add_fitfunction(Newfunc)
            newline,=Newfunc.draw(self.current_fit_plot_x(),self.fitaxes,zorder=5)
            self.fitline.append(newline)
            self.update_window()
        else:
            n=2
            array=[1,1,1]
            Newfunc=Polynom(n,array)
            self.spectre.add_fitfunction(Newfunc)
            newline,=Newfunc.draw(self.current_fit_plot_x(),self.fitaxes,zorder=5)
            self.fitline.append(newline)
            self.update_window()
            
    def stop(self):
        return
    
    def abscisse(self):
        self.axes.set_xlim(float(self.lambda_min_edit.text()),float(self.lambda_max_edit.text()))
        self.spectro.draw()
        
    def abscisse_type(self):
        """ Allow to change the abscisse axis to nm, eV or normalized frequency (NF)"""
        if self.abscisse_type_slider.value()==1:
            self.periode_text.setEnabled(True)
            self.x=self.x_nm
            self.lambda_min_label.setText("lambda min (nm)")
            self.lambda_max_label.setText("lambda max (nm)")
        elif self.abscisse_type_slider.value()==2:
            self.periode_text.setEnabled(True)
            self.x=self.spectre.en
            self.lambda_min_label.setText("Energy min (eV)")
            self.lambda_max_label.setText("Energy max (eV)")
        elif self.abscisse_type_slider.value()==3:
            self.periode_text.setEnabled(True)
            self.x=self.spectre.nf
            self.lambda_min_label.setText("Freq min (a/nm)")
            self.lambda_max_label.setText("Freq max (a/nm)")
        self.lambda_min_edit.setText(str(round(min(self.x),3)))
        self.lambda_max_edit.setText(str(round(max(self.x),3)))
        self.fit_x = self.x
        self.fit_target_value = self.activSlider.value()
        self.fit_target_axis_mode = self.abscisse_type_slider.value()
        self.update_window()
        self.abscisse()
    
    def current_fit_plot_x(self):
        """Return the x-grid on which the fitted model should currently be drawn."""
        if self.fit_target_value == self.activSlider.value() and self.fit_target_axis_mode == self.abscisse_type_slider.value():
            return self.fit_x
        return self.x

    def fitLayoutLign(self,function,lignnumber,parammax,totallign):
        funcLabel=QLabel(function.name)
        self.fitLayout.addWidget(funcLabel,lignnumber+1,0,1,2)
        col=2
        for i,(n,m) in enumerate(zip(function.paramnames,function.param)):
            paramlabel = QLabel(n)
            paramEdit = QLineEdit(str(round(m,4)))
            paramEdit.returnPressed.connect(partial(self.updatefunction,function=function,i=i))
            self.fitLayout.addWidget(paramlabel,lignnumber+1,col)
            col+=1
            self.fitLayout.addWidget(paramEdit,lignnumber+1,col)
            col+=1
        fixCheck=QCheckBox()
        fixCheck.setChecked(function.fixed)
        fixCheck.clicked.connect(partial(self.fixfit,function=function))
        deleteCheck=QCheckBox()
        deleteCheck.clicked.connect(partial(self.deletefitfunction,lignnumber))
        self.fitLayout.addWidget(fixCheck,lignnumber+1,parammax*2+3)
        self.fitLayout.addWidget(deleteCheck,lignnumber+1,parammax*2+4)
    
    def fixfit(self,function):
        function.fixed=not function.fixed
        print(function,function.fixed)
        self.update_formula_panel()
        
    def deletefitfunction(self,row):
        n=self.fit_function_number
        self.fitLayout.itemAt(row).widget().close()
        del self.spectre.function[n][row-1]
        self.fitline.remove(self.fitline[row])
        self.update_window()
    
    def updatefunction(self,function,i):
        if function.name == "Polynom function" and i==0:
            value=self.sender().text()
            function.n=int(value)
            function.reinit()
            self.update_window()
        else:
            value=self.sender().text()
            function.param[i]=float(value)
        self.fitline=self.spectre.plot_fit(self.current_fit_plot_x(),0,self.fitaxes,self.fitline)
        self.update_formula_panel()
        self.spectro.draw()
                
    def fitLayoutUpdate(self):
        for i in range(self.fitLayout.count()): self.fitLayout.itemAt(i).widget().close()
        if self.spectre.function == [[]]:
            func = Function(X0=0,X1=1,X2=2,X3=3)
            self.fitLayoutLign(func,0,4,1)
            parammax=4
        else :
            functions=self.spectre.function[0]
            parammax=max([len(func.param) for func in functions])
            for i,func in enumerate(functions):
                self.fitLayoutLign(func,i+1,parammax,len(functions))
                
        self.fitLabel1 = QLabel('functions')
        self.fitLabel2 = QLabel('Parameters')
        self.fitLabel3 = QLabel('Fix')
        self.fitLabel4 = QLabel('Delete')
        self.fitLayout.addWidget(self.fitLabel1,0,0,1,2)
        self.fitLayout.addWidget(self.fitLabel2,0,2,1,parammax*2)
        self.fitLayout.addWidget(self.fitLabel3,0,parammax*2+3)
        self.fitLayout.addWidget(self.fitLabel4,0,parammax*2+4)
        self.update_formula_panel()
    
    def update_formula_panel(self):
        functions = self.spectre.function[self.fit_function_number]
        if functions == []:
            lines = [r"y_{\mathrm{fit}}(x) = 0"]
        else:
            lines = [
                r"y_{\mathrm{fit}}(x) = " + " + ".join([fr"f_{{{i}}}(x)" for i in range(1, len(functions) + 1)]),
            ]
            for i, function in enumerate(functions, 1):
                lines.append(fr"f_{{{i}}}(x) = {function.mathtext_formula()}")

        self.formula_fig.clear()
        ax = self.formula_fig.add_axes([0.0, 0.0, 1.0, 1.0])
        ax.set_axis_off()
        if len(lines) == 1:
            y_positions = [0.82]
        else:
            y_positions = np.linspace(0.92, 0.12, len(lines))
        for y, line in zip(y_positions, lines):
            ax.text(0.02, y, f"${line}$", transform=ax.transAxes, ha='left', va='top', fontsize=10)
        self.formula_canvas.draw()

    def Go_fit(self):
        print('fitting !')
        bornesmin=min((np.abs(self.x - self.axes.get_xlim()[0])).argmin(),(np.abs(self.x - self.axes.get_xlim()[1])).argmin())
        bornesmax=max((np.abs(self.x - self.axes.get_xlim()[0])).argmin(),(np.abs(self.x - self.axes.get_xlim()[1])).argmin())
        Emin=min(self.x[bornesmin],self.x[bornesmax])
        Emax=max(self.x[bornesmin],self.x[bornesmax])
        print(Emin,Emax)
        step=(Emax-Emin)/500
        bornes=np.arange(bornesmin,bornesmax)
        yfit=np.asarray(self.line.get_ydata()) #get_ydata() modifies the values of ydata. Be careful to not change the value of yfit
        fixed=self.x*0.
        functions=self.spectre.function[0]
        for func in functions:
            if func.fixed==True:
                fixed+=func.function(self.x,*func.param)
        a,b=fit(self.x,yfit-fixed,bornes,function=functions)
        start=0
        end=0
        for func in functions:
            if func.fixed!=True:
                end+=len(func.param)
                func.param=a[0][start:end]
                start=end
        self.fit_x=np.arange(Emin,Emax,step)
        self.fit_target_value = self.activSlider.value()
        self.fit_target_axis_mode = self.abscisse_type_slider.value()
        self.update_window()
        print(self.spectre.function[0])
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
     
    def update_window(self):
        self.clear_spectrum()
        self.update_stackspectre()
        self.update_curseur_list()
        self.fitLayoutUpdate()        
        
    def update_curseur_list(self):
        self.curseur_widget.clear()
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
        self.update_window()
        
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
        self.update_window()
        
    def Autozoom(self):
        y=self.spectre.y
        self.axes.set_ylim(np.min(y),np.max(y))
        self.spectro.draw()
    
    def zoom(self):
        self.toolbar.zoom()
        
    def update_spectrum(self,spectre):
        self.spectre.y=spectre
        self.spectre.plot(self.x,self.axes,self.line)
        self.curseur_axe.set_ylim(self.axes.get_ylim())
        self.spectro.draw()
    
    def add_spectrum(self):
        if len(self.stack_spectre)==0 :
            self.stack_spectre.append(self.spectre)
        else:
            self.stack_spectre.append(self.spectre)
        self.spectre = Spectre(self.x_nm,self.stack_spectre[-1].y,int(self.periode_text.text()))
        if len(self.stack_spectre) == 2:
           self.activespecWidget.setHidden(False)
           self.activSlider.setValue(2)
           self.currentposSpin.setValue(2)
        self.activSlider.setRange(1,len(self.stack_spectre))
        self.activSlider.setValue(len(self.stack_spectre))
        self.currentposSpin.setMaximum(self.currentposSpin.maximum()+1)
        
    def update_stackspectre(self):
        value=self.activSlider.value()
        self.currentposSpin.setValue(value)
        displayrange = min(value,int(self.numdisplayEdit.text()))
        start= value-displayrange
        finish= value
        if len(self.stack_spectre) != 0 :
            for spectre in self.stack_spectre[start:finish]:
                if self.abscisse_type_slider.value()==1:
                    x=spectre.nm
                elif self.abscisse_type_slider.value()==2:
                    x=spectre.en
                elif self.abscisse_type_slider.value()==3:
                    x=spectre.nf
                spectre.plot(x,self.axes)
            self.x=x
            self.spectre=self.stack_spectre[finish-1]
            self.spectre.plot(self.x,self.axes,self.line)
            self.axes.set_xlim(float(self.lambda_min_edit.text()), float(self.lambda_max_edit.text()))
            ymin = float(np.min(self.spectre.y))
            ymax = float(np.max(self.spectre.y))
            if ymin == ymax:
                pad = max(abs(ymin) * 0.05, 1.0)
            else:
                pad = 0.05 * (ymax - ymin)
            self.axes.set_ylim(ymin - pad, ymax + pad)
            self.fitline = self.spectre.plot_fit(self.current_fit_plot_x(),0,self.fitaxes,self.fitline)
        self.spectro.draw()
                
    def clear_spectrum(self):
        limy=self.axes.get_ylim()
        limx=self.axes.get_xlim()
        self.axes.cla()
        #self.line has to be redifined or the spectrum won't show anymore
        self.line,=self.spectre.plot(self.x,self.axes,zorder=5)
        #same with self.crossline
        self.crossline, = self.axes.plot(self.coord_cross[0],self.coord_cross[1])
        self.sommefitline,=self.fitaxes.plot([], [], zorder=10)
        self.fitline=[self.sommefitline]
        self.axes.set_ylim(limy)
        self.axes.set_xlim(limx)
    
    def update_activSlider(self):
        self.activSlider.setValue(int(self.currentposSpin.value()))


class Spectre():
    """Container for one spectrum together with its derived axes and fit metadata."""
    
    def __init__(self,x,y,periode):
        self.nm=x
        self.y=y
        self.periode=periode
        # 1240 eV.nm is the usual hc conversion constant used to map wavelength to photon energy.
        self.en=1240/self.nm
        # The normalized frequency compares spectra in units of lattice period / wavelength.
        self.nf=self.periode/self.nm
        
        #fitting function
        self.function=[[]]
        
        #filtered spectra
        self.filtered=[]
    
    def add_newfit(self):
        self.function.append([])
    
    def add_fitfunction(self,function,n=-1):
        self.function[n].append(function)
    
    def add_filtered(self,filtername, y):
        self.filtered.append({'filtername':filtername, 'y':y})
        
    def plot(self,x,axe=None,line=None,**kwargs):
        if axe != None:
            if line != None:
                return line.set_data(x,self.y)
            else:
                return axe.plot(x,self.y,**kwargs)
        else:
            return plt.plot(x,self.y,**kwargs)
        
    def plot_fit(self,x,n=-1,axe=None,fitline=None,**kwargs):
        if self.function != [[]]:
            arg=[param for func in self.function[n] for param in func.param]
            if axe != None:
                if fitline != None:
                    fitline[0].set_data(x,functionsomme(x,*arg,fixed=False,function=self.function[n]))
                    if self.function[n] != []:
                        for i,func in enumerate(self.function[n][:len(fitline)-1],1):
                            fitline[i].set_data(x,func.function(x,*func.param))
                        for func in self.function[n][len(fitline)-1:]:
                            fitline.append(axe.plot(x,func.function(x,*func.param), **kwargs)[0])
                    for stale_line in fitline[len(self.function[n])+1:]:
                        stale_line.set_data([], [])
                else:
                    fitline=[axe.plot(x,functionsomme(x,*arg,fixed=False,function=self.function[n]),**kwargs)[0]]
                    if self.function[n] != []:
                        for func in self.function[n]:
                            fitline.append(axe.plot(x,func.function(x,*func.param),**kwargs)[0])
            else:
                return plt.plot(x,functionsomme(x,*arg,function=self.function[n]),**kwargs)
            return fitline
        else:
            if axe != None:
                if fitline is None:
                    return [axe.plot([], [], **kwargs)[0]]
                fitline[0].set_data([], [])
                for stale_line in fitline[1:]:
                    stale_line.set_data([], [])
                return fitline[:1]
            else:
                return plt.plot([], [], **kwargs)
        

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
        self.fixed = False #Allows to fix the function while fitting
    
    def function(self, *args):
        print("this is a generic function")
        print("you need to define a nex function")
        return
    
    def draw(self,x,axe=None,**kwargs):
        if axe != None:
            return axe.plot(x,self.function(x,*self.param),**kwargs)
        else:
            return plt.plot(x,self.function(x,*self.param),**kwargs)
    
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

    def literal_formula(self):
        return "f(x)"

    def mathtext_formula(self):
        return r"f(x)"

    def parameter_help(self):
        return {name: "fit parameter" for name in self.paramnames}

    def format_parameter_help(self):
        return ", ".join([f"{name}={desc}" for name, desc in self.parameter_help().items()])


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

    def literal_formula(self):
        return "A * sin(Omega * (x - x0))"

    def mathtext_formula(self):
        return r"A \sin\!\left(\Omega \left(x - x_0\right)\right)"

    def parameter_help(self):
        return {'x0': 'center / phase origin', 'Omega': 'angular frequency', 'A': 'amplitude'}


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

    def literal_formula(self):
        return "A / q^2 * (q * Gamma + 2 * (x - x0))^2 / (Gamma^2 + 4 * (x - x0)^2)"

    def mathtext_formula(self):
        return r"\frac{A}{q^2}\frac{\left(q\Gamma + 2\left(x-x_0\right)\right)^2}{\Gamma^2 + 4\left(x-x_0\right)^2}"

    def parameter_help(self):
        return {'x0': 'resonance position', 'Gamma': 'linewidth', 'A': 'amplitude', 'q': 'Fano asymmetry'}
    
    
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

    def literal_formula(self):
        return "A * exp(-(x - x0)^2 / (2 * Gamma^2))"

    def mathtext_formula(self):
        return r"A \exp\!\left(-\frac{\left(x-x_0\right)^2}{2\Gamma^2}\right)"

    def parameter_help(self):
        return {'x0': 'center', 'Gamma': 'width (sigma-like)', 'A': 'amplitude'}
    

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

    def literal_formula(self):
        return "A / (1 + 4 * ((x - x0) / Gamma)^2)"

    def mathtext_formula(self):
        return r"\frac{A}{1 + 4\left(\frac{x-x_0}{\Gamma}\right)^2}"

    def parameter_help(self):
        return {'x0': 'center', 'Gamma': 'linewidth', 'A': 'amplitude'}


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

    def literal_formula(self):
        terms = [f"{name} * x^{self.n - i}" for i, name in enumerate(self.paramnames[1:])]
        return " + ".join(terms)

    def mathtext_formula(self):
        terms = []
        for i, name in enumerate(self.paramnames[1:]):
            power = self.n - i
            coeff = name[0] + r"_{" + name[1:] + r"}" if len(name) > 1 else name
            if power == 0:
                terms.append(coeff)
            elif power == 1:
                terms.append(fr"{coeff} x")
            else:
                terms.append(fr"{coeff} x^{power}")
        return " + ".join(terms)

    def parameter_help(self):
        mapping = {'n': 'polynomial degree'}
        for i, name in enumerate(self.paramnames[1:]):
            mapping[name] = f'coefficient of x^{self.n - i}'
        return mapping

def functionsomme(x,*args,**kwargs):
    """Evaluate the sum of all non-fixed fit functions using a flattened parameter vector.

    `curve_fit` only knows about a 1D array of fit parameters. This helper rebuilds the
    correspondence between that flat array and the sequence of analytical functions selected by
    the user.
    """
    start=0
    end=0
    fitmul=0
    if 'fixed' in kwargs:
        fixed=kwargs['fixed']
    else:
        fixed=True
    for func in kwargs['function']:
        # Fixed functions keep their own parameters and therefore do not consume entries from
        # the flattened optimization vector.
        if func.fixed != True or fixed!=True: #Maybe this needs to be an and
            end+=len(func.param)
            fitmul = fitmul + func.function(x,*args[start:end])
            start=end
    return fitmul 
        
def fit(FREQ,sig,bornes=None,function=[Fano(1,1,1,1),Polynom(0)]):
    """
    Parameters
    ----------
    FREQ : array of abscisses
    
    sig :  array of ordinates
    
    bornes : (optional) array of the coordinates for the used abscisses. For example bornes=np.arange(50,100) to fit from abscisse 50 to abscisse 99

    function : (optional) array of the functions used for the fit. Example : function =  [Fano(1,1,1), Gaussian(1,2,3)]
        
    Returns
    ---------
    bestv : table of the best values from the fit. They are also stored in function[i].param
    
    fit : array containing the fitting function's ordinate
    """
    if bornes is None:
        bornes=np.arange(len(FREQ))
    bestv=[]
    fit=[]
    Emin=min(FREQ[bornes[0]],FREQ[bornes[-1]])
    Emax=max(FREQ[bornes[0]],FREQ[bornes[-1]])
    step=(Emax-Emin)/500
    seed=[]
    funcfit=[]
    # Only the non-fixed functions contribute free parameters to the optimizer.
    for func in function:
        if func.fixed!=True:
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
    

def main():
    global app
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    x=np.arange(300,1000)
    spectra=[Spectre(x,1+np.sin(x/50+i/2),384) for i in range (0,10)]
    value=5
    prog = Fenetre(spectra,value) 
    prog.show()
    app.exec_()
    app.quit()

if __name__ == '__main__':
    main()
