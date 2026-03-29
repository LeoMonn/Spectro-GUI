#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 14 17:19:49 2018

@author: leonard
"""

from PyQt5.QtWidgets import QLineEdit,QLabel,QAction,QPushButton
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QMainWindow,QWidget,QApplication,QDesktopWidget,QGridLayout,QVBoxLayout
from PyQt5.QtCore import pyqtSignal,QThread,pyqtSlot, Qt
from PyQt5.QtGui import QIcon, QFont
import os, sys
import time
from datetime import date



today=date.today()
jour="%02d" %(today.day)
mois="%02d" %(today.month)
annee=str(today.year)


class Fenetre (QMainWindow):
    
    def __init__(self):
        super(Fenetre,self).__init__()
        self.resize(300, 200)
        self.center()
        self.initUI() 
    
    def initUI(self):    
        '''initiates application UI'''
        self.Create_Layout() 
            
        self.statusBar().showMessage('Ready')        
        self.menu()
        self.setWindowTitle('Rotation')    
        ###################################################################"
        
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
            self.CentralWidget.close()
            event.accept()
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
        self.Layout()
        self.connect()
        
        
    def Layout(self):
        self.MainLayout=QVBoxLayout()
        self.Rotation=Rotation(self)
        self.MainLayout.addWidget(self.Rotation)
        
        self.setLayout(self.MainLayout)
        
    def connect(self):
        return
    
    def close(self):
        self.Rotation.close()

      
class Rotation(QWidget):
    """Worker widget exposing high-level left/right arm motions to the rest of the GUI."""
    initover=pyqtSignal()
    
    def __init__(self,parent):
        super().__init__(parent)
        
        #### Import des platines ###
        try:
            from thorpy.comm.discovery import discover_stages
            self.stages = list(discover_stages())
            print(self.stages)
        except:
            print('module non chargé thorpy.comm.discovery')
            self.stages=0
            pass
            
        print('Rotation')
                        ####  Fichier de configuration
        self.repertoire = os.getcwd()+'/'
        self.fichierconfig = "manip_angle_config.txt"
        try:
            if not os.path.exists(self.repertoire + self.fichierconfig):
                file=open(self.repertoire + self.fichierconfig,"w")
                file.write("Offset_Moteur == 0.2")
                file.close()
        except:
            pass
        
        with open(self.repertoire+self.fichierconfig) as f:
            self.config=f.readlines()

        for string in self.config:
            print(self.config)
            if string.find("Offset_Moteur == ")!=-1 :
                self.offset = string[17:] 
                
        self.font_title = QFont()
        self.font_title.setPointSize(10)
        self.font_title.setBold(True)
        self.font_title.setWeight(75)
        
        self.font_text = QFont()
        self.font_text.setPointSize(8)
        self.font_text.setBold(False)
        self.font_text.setWeight(50)
        
        self.Layout()
        self.offset=float(self.Offset_consigne.text())
        self.Rotation_Thread=Rotation_thread(self,self.stages,self.offset)          
        
        self.connect()
        print('emit')
        self.initover.emit()
      
    def Layout(self):    
        self.grid=QGridLayout()
        
        self.Illum_Label=QLabel("Controle de la rotation \n bras de l'illumination")
        self.Illum_Label.setAlignment(Qt.AlignCenter)
        self.Illum_Label.setFont(self.font_title)
        self.Illum_abs_Label=QLabel("déplacement \n absolu")
        self.Illum_abs_Label.setFont(self.font_text)
        self.Illum_Consigne_abs=QLineEdit("0")
        self.Illum_rel_Label=QLabel("déplacement \n relatif")
        self.Illum_rel_Label.setFont(self.font_text)
        self.Illum_Consigne_rel=QLineEdit("0")
        self.Illum_Position_reelle=QLabel("0")
        self.Illum_Position_Theo=QLabel("0")
        self.Illum_Go_abs=QPushButton("Go")
        self.Illum_Go_abs.setFont(self.font_text)
        self.Illum_Go_rel=QPushButton("Go")
        self.Illum_Go_rel.setFont(self.font_text)
        self.Illum_Home=QPushButton("Home")
        self.Illum_Home.setFont(self.font_text)
        
        self.Collec_Label=QLabel("Controle de la rotation \n bras de collection")
        self.Collec_Label.setAlignment(Qt.AlignCenter)
        self.Collec_Label.setFont(self.font_title)
        self.Collec_abs_Label=QLabel("déplacement \n absolu")
        self.Collec_abs_Label.setFont(self.font_text)
        self.Collec_Consigne_abs=QLineEdit("0")
        self.Collec_rel_Label=QLabel("déplacement \n relatif")
        self.Collec_rel_Label.setFont(self.font_text)
        self.Collec_Consigne_rel=QLineEdit("0")
        self.Collec_Position_reelle=QLabel("0")
        self.Collec_Position_Theo=QLabel("0")
        self.Collec_Go_abs=QPushButton("Go")
        self.Collec_Go_abs.setFont(self.font_text)
        self.Collec_Go_rel=QPushButton("Go")
        self.Collec_Go_rel.setFont(self.font_text)
        self.Collec_Home=QPushButton("Home")
        self.Collec_Home.setFont(self.font_text)
        
        self.grid.addWidget(self.Illum_Label,0,0,1,5)
        self.grid.addWidget(self.Illum_abs_Label,1,0)
        self.grid.addWidget(self.Illum_Consigne_abs,1,1)
        self.grid.addWidget(self.Illum_Go_abs,1,2)
        self.grid.addWidget(self.Illum_rel_Label,2,0)
        self.grid.addWidget(self.Illum_Consigne_rel,2,1)
        self.grid.addWidget(self.Illum_Go_rel,2,2)
        self.grid.addWidget(self.Illum_Position_reelle,1,3)
        self.grid.addWidget(self.Illum_Position_Theo,2,3)

        self.Offset_Label=QLabel("Offset \n moteur")
        self.Offset_Label.setFont(self.font_text)
        self.Offset_consigne=QLineEdit(self.offset)
        self.Offset_reglage=QPushButton("Reglage \n l'offset")
        self.Offset_reglage.setFont(self.font_text)
        self.Save_Offset=QPushButton("Save \n Offset")
        self.Save_Offset.setFont(self.font_text)
        
        self.grid.addWidget(self.Illum_Home,1,4)
        
        self.grid.addWidget(self.Collec_Label,3,0,1,5)
        self.grid.addWidget(self.Collec_abs_Label,4,0)
        self.grid.addWidget(self.Collec_Consigne_abs,4,1)
        self.grid.addWidget(self.Collec_Go_abs,4,2)
        self.grid.addWidget(self.Collec_rel_Label,5,0)
        self.grid.addWidget(self.Collec_Consigne_rel,5,1)
        self.grid.addWidget(self.Collec_Go_rel,5,2)
        self.grid.addWidget(self.Collec_Position_reelle,4,3)
        self.grid.addWidget(self.Collec_Position_Theo,5,3)
        self.grid.addWidget(self.Offset_Label,6,0)
        self.grid.addWidget(self.Offset_consigne,6,1)
        self.grid.addWidget(self.Offset_reglage,6,2,1,2)
        self.grid.addWidget(self.Save_Offset,6,4)
        
        self.grid.addWidget(self.Collec_Home,4,4)
        self.setLayout(self.grid)
    
    def connect(self):
        ### Connect ne prend que des fonctions sans arguments. 
        ###     lambda permet de transformer une fonction avec argument en fonction sans argument
        ###     partial pourrait aussi marcher ici
        ### 1 est utilisé pour définir un mouvement absolu
        ### 2 est utilisé pour définir un mouvement relatif
        self.Illum_Consigne_abs.returnPressed.connect(lambda: self.rotationR(float(self.Illum_Consigne_abs.text()),1))
        self.Illum_Go_abs.clicked.connect(lambda: self.rotationR(float(self.Illum_Consigne_abs.text()),1))
        self.Collec_Consigne_abs.returnPressed.connect(lambda: self.rotationL(float(self.Collec_Consigne_abs.text()),1))
        self.Collec_Go_abs.clicked.connect(lambda: self.rotationL(float(self.Collec_Consigne_abs.text()),1))
        self.Illum_Consigne_rel.returnPressed.connect(lambda: self.rotationR(float(self.Illum_Consigne_rel.text()),2))
        self.Illum_Go_rel.clicked.connect(lambda: self.rotationR(float(self.Illum_Consigne_rel.text()),2))
        self.Collec_Consigne_rel.returnPressed.connect(lambda: self.rotationL(float(self.Collec_Consigne_rel.text()),2))
        self.Collec_Go_rel.clicked.connect(lambda: self.rotationL(float(self.Collec_Consigne_rel.text()),2))
        self.Collec_Home.clicked.connect(self.HomeL)
        self.Illum_Home.clicked.connect(self.HomeR)
        self.Save_Offset.clicked.connect(self.saveoffset)
        self.Rotation_Thread.rotation_over.connect(self.waiting)
        self.Rotation_Thread.rotation_started.connect(self.running)
        
    def saveoffset(self):
        """Persist the user offset and mirror it on both arms.

        The collection and illumination arms use opposite motor conventions, so the same optical
        correction is stored with opposite signs in the thread worker.
        """
        for i,string in enumerate(self.config):
            if string.find("Offset_Moteur")!=-1:
                self.config[i]=self.config[i][:17]+self.Offset_consigne.text()
                
        with open(self.repertoire+self.fichierconfig,"w") as f:
            f.writelines(self.config)
        print('close')
        
        self.Rotation_Thread.offset_l=float(self.Offset_consigne.text())
        self.Rotation_Thread.offset_r=-float(self.Offset_consigne.text())
    
    def close(self):
        self.HomeL()
        self.HomeR()
    
    def running(self):
        self.Illum_Go_abs.setEnabled(False)
        self.Illum_Go_rel.setEnabled(False)
        self.Illum_Home.setEnabled(False)
        self.Collec_Go_abs.setEnabled(False)
        self.Collec_Go_rel.setEnabled(False)
        self.Collec_Home.setEnabled(False)
        self.Offset_reglage.setEnabled(False)
        self.Save_Offset.setEnabled(False)
        
    def waiting(self):
        self.Illum_Go_abs.setEnabled(True)
        self.Illum_Go_rel.setEnabled(True)
        self.Illum_Home.setEnabled(True)
        self.Collec_Go_abs.setEnabled(True)
        self.Collec_Go_rel.setEnabled(True)
        self.Collec_Home.setEnabled(True)
        self.Offset_reglage.setEnabled(True)
        self.Save_Offset.setEnabled(True)
     
    def rotationL(self,theta,a):
        """theta = angle de rotation
        a=1 : deplacement vers une position absolue
        a=2 : déplacement relatif par rapport à la position courante
        """
#        print(theta, a)
        self.Rotation_Thread.rotation='rotationL'
        self.Rotation_Thread.theta=theta
        self.Rotation_Thread.a=a
        self.Rotation_Thread.start()
        
    def rotationR(self,theta,a):
        """theta = angle de rotation
        a=1 : deplacement vers une position absolue
        a=2 : déplacement relatif par rapport à la position courante
        """
        #print(theta, a)
        self.Rotation_Thread.rotation='rotationR'
        self.Rotation_Thread.theta=theta
        self.Rotation_Thread.a=a
        self.Rotation_Thread.start()
    
    def HomeL(self):      
        self.Rotation_Thread.rotation='HomeL'
        self.Rotation_Thread.start()
    
    def HomeR(self):
        self.Rotation_Thread.rotation='HomeR'
        self.Rotation_Thread.start()
       
    


class Rotation_thread(QThread):
    """Hardware thread converting optical angles into the motor reference frame."""
    
    rotation_over=pyqtSignal()
    rotation_started=pyqtSignal()
    
    def __init__(self,parent,stages,offset):
        super(self.__class__,self).__init__(parent)
        try:
            ####################################################################
            # initialisation des platines thorlabs
            ####################################################################
            
            #si aucune platine n'ezst branchée, on lance une simulation de moteur
            if stages[0]._port.serial_number ==  55000218:
                self.mr = stages[1] # moteur du bras droit
                self.ml = stages[0] # moteur du bras gauche
            else:
                self.mr = stages[0] # moteur du bras droit
                self.ml = stages[1] # moteur du bras gauche
            #on suppose que tous les paramètres par défaut sont bons.
            print ("position du moteur gauche {0} et droit {1}".format(
            self.ml.position,self.mr.position))
            self.rotation = ''
            self.theta=-1000
            self.a=-1
            
        except:
            print("pas de moteur")
        
        # The two arms are mirrored mechanically, so a positive optical correction on one
        # side becomes a negative correction on the other.
        self.offset_l=offset
        self.offset_r=-offset
    
    @pyqtSlot()
    def run(self):
        def rotationL(theta,a):
            """theta = angle de rotation
            a=1 : deplacement vers une position absolue
            a=2 : déplacement relatif par rapport à la position courante
            """
            self.rotation_started.emit()
            print('rotationL',theta,a)
            try:
                while (self.mr.status_in_motion_forward or self.mr.status_in_motion_reverse \
                       or self.ml.status_in_motion_homing or self.mr.status_in_motion_homing):
                    time.sleep(.2)
                if a==1: #deplacement absolu
                    # The left arm angle is expressed relative to the optical normal, while the
                    # motor home is defined in the stage frame. The -90 deg shift converts between both.
                    self.ml.position = 2048 * float(-90 + self.offset_l+ theta)
                elif a==2: #deplacement relatif
                    self.ml.position = self.ml.position + 2048 * float(theta)
                time.sleep(0.1)
                while (self.ml.status_in_motion_forward or self.ml.status_in_motion_reverse):
                    time.sleep(.2)
                time.sleep(0.2)
                position=self.ml.position/2048
                print('rotationL over',position)
            except:
                print("Dummy L")
                position=float(self.parent().Collec_Position_Theo.text())
                time.sleep(2)
                if a==1: #deplacement absolu
                    position = float(-90+theta+ self.offset_l)
                if a==2: #deplacement relatif
                    position = position + float(theta) 
            self.parent().Collec_Position_reelle.setText(str(round(90+position-self.offset_l,2)))
            self.parent().Collec_Position_Theo.setText(str(round(position,2)))
    #            print(position, self.Collec_Position.text())
            self.rotation_over.emit()
            return position
        
        def rotationR(theta,a):
            """theta = angle de rotation
            a=1 : deplacement vers une position absolue
            a=2 : déplacement relatif par rapport à la position courante
            """
            print('rotationR',theta,a)
            self.rotation_started.emit()
            try:
                while (self.mr.status_in_motion_forward or self.mr.status_in_motion_reverse \
                       or self.ml.status_in_motion_homing or self.mr.status_in_motion_homing):
                    time.sleep(.2)
                if a==1: #deplacement absolu
                    # The right arm uses the mirrored convention of the left arm, hence the sign
                    # flip on theta and the different home offset in the motor frame.
                    self.mr.position = 2048 * float(45 - self.offset_r - theta)
                elif a==2: #deplacement relatif
                    self.mr.position = self.mr.position - 2048 * float(theta)
                time.sleep(.2)
                while (self.mr.status_in_motion_forward or self.mr.status_in_motion_reverse):
                    time.sleep(.2)
                position=self.mr.position/2048
                print('rotationR over',position)
            except:
                print('Dummy R')
                position=float(self.parent().Illum_Position_Theo.text())
                time.sleep(2)
                if a==1: #deplacement absolu
                    position = float(45 - self.offset_r - theta)
                if a==2: #deplacement relatif
                    position = position - float(theta)
            self.parent().Illum_Position_reelle.setText(str(round(-position+45-self.offset_r,2)))
            self.parent().Illum_Position_Theo.setText(str(round(position,2)))
    #       print(position)
            self.rotation_over.emit()
            return position
        
        def HomeL():
            """Pour éviter tous problèmes, on envoie la platine à 0 avant de faire un home pour éviter qu'elle ne
            fasse un tour complet. Pöur le premier Home, il faut que la platine soit proche de sa position home
            """
            # Un bug existe sur le home force On utilise donc le home_non blocking dont le
            # force marche et on fait une boucle pour le faire en blocking
            print('HomeL')
            self.rotation_started.emit()
            try:
                self.ml.position=0
                time.sleep(0.2)
                while (self.ml.status_in_motion_forward or self.ml.status_in_motion_reverse):
                    time.sleep(.2)
                time.sleep(0.1)
                self.ml.home_non_blocking()
                time.sleep(0.2)
                while (self.ml.status_in_motion_homing):
                    time.sleep(.2)
                position=self.ml.position/2048
                self.parent().Collec_Position_reelle.setText(str(round(90+self.ml.position/2048-self.offset_l,2)))
                self.parent().Collec_Position_Theo.setText(str(round(self.ml.position/2048,2)))
                print('homeCollec')
            except:
                print('moteur collection (gauche) non connecté')
                time.sleep(2)
                self.parent().Collec_Position_reelle.setText("90")
                self.parent().Collec_Position_Theo.setText("0")
                position=0
            print('HomeL over')
            self.rotation_over.emit()
            return position
        
        def HomeR():
            """Pour éviter tous problèmes, on envoie la platine à 0 avant de faire un home pour éviter qu'elle ne
            fasse un tour complet. Pöur le premier Home, il faut que la platine soit proche de sa position home
            """
            # Un bug existe sur le home force On utilise donc le home_non blocking dont le
            # force marche et on fait une boucle pour le faire en blocking
            print('HomeR')
            self.rotation_started.emit()
            try:
                self.mr.position=0
                time.sleep(0.2)
                while (self.mr.status_in_motion_forward or self.mr.status_in_motion_reverse):
                    time.sleep(.2)
                time.sleep(0.1)
                self.mr.home_non_blocking()
                time.sleep(0.2)
                while (self.mr.status_in_motion_homing):
                    time.sleep(.5)
                self.parent().Illum_Position_reelle.setText(str(round(-self.mr.position/2048+45-self.offset_r,2)))
                self.parent().Illum_Position_Theo.setText(str(round(self.mr.position/2048,2)))
                print('homeIllum')
                
                position=self.mr.position/2048
            except:
                print('moteur illumination (droite) non connecté')
                time.sleep(2)
                self.parent().Illum_Position_reelle.setText("45")
                self.parent().Illum_Position_Theo.setText("0")
                position=0
            print('HomeR over')
            self.rotation_over.emit()
            return position
        
        if self.rotation == 'rotationL':
            if self.theta != -1000 and self.a!= -1:
                rotationL(self.theta,self.a)
                self.theta = -1000 
                self.a = -1
        elif self.rotation == 'rotationR':
            if self.theta != -1000 and self.a!= -1:
                rotationR(self.theta,self.a)
                self.theta = -1000 
                self.a = -1
        elif self.rotation == 'HomeL':
            HomeL()
        elif self.rotation == 'HomeR':
            HomeR()



def main():
    app = QApplication.instance() 
    if not app:
        app = QApplication(sys.argv)
    prog = Fenetre() 
    prog.show()
    app.exec_()
    app.quit()
    
if __name__ == '__main__':
    main()