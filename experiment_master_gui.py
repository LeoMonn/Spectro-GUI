#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Master GUI orchestrating the rotation, spectrometer, and camera workers.

Legacy note:
- `spectrometer_gui.py` is the current spectrometer worker.
- older `Spectro*` variants are kept only as legacy references.
"""


from PyQt5.QtWidgets import QLineEdit,QLabel,QAction,QPushButton,QSpinBox,QTextEdit,QCheckBox,QMessageBox,QFileDialog
from PyQt5.QtWidgets import QMainWindow,QWidget,QApplication,QDesktopWidget,QGridLayout,QStyle
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
import numpy as np
import os,sys
from datetime import date
import time




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
        self.setWindowTitle('Manip Angle CP')    
        ###################################################################"

        
        
    def Create_Layout(self):
        
        self.CentralWidget = Main(self)
        self.setCentralWidget(self.CentralWidget)       

    def menu(self):
        menubar=self.menuBar()
        menubar.clear()
        fileMenu = menubar.addMenu('&File')
                
        #########################################
        ##           Menu File                 ##
        #########################################
        exitAct = QAction(QIcon('exit.png'),'&Exit',self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(self.close)
        fileMenu.addAction(exitAct)

        # Worker widgets can contribute their own menu entries when they are active in the
        # master window, so the combined GUI behaves like the standalone tools.
        for worker in self.CentralWidget.active_menu_workers():
            worker.MenuBar(menubar)
        
        
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
    """Top-level container that wires the active worker widgets together."""
    
    def __init__(self,parent):
        
        super().__init__(parent)
        
        self.Layout()
        self.connect()
        
        
    def Layout(self):
        self.MainLayout=QGridLayout()
        #On import d'abord les platines avant le spectro
        #Si OSA_thorlabs est importé, les platines ne sont pas reconnues
        #Bug si les platines ont déjà été chargée dans la console, les platines ne chargent pas.
        import rotation_gui as Rot
        self.Rotation=Rot.Rotation(self)
        import spectrometer_gui as Spe
        self.spectro_module = Spe
        self.Spectro=Spe.Spectro(self)
        import camera_gui as Cam
        self.Camera=Cam.Camera(self)
        import picomotor_gui as Pico
        self.Picomotor=Pico.Picomotor(self)
        self.Save=Save(self)
        self.Manip=Manip(self)
        self.Rotation_check=QCheckBox('Rotation')
        self.Rotation_check.setChecked(True)
        self.Spectro_check=QCheckBox('Spectro')
        self.Spectro_check.setChecked(True)
        self.Camera_check=QCheckBox('Camera')
        self.Camera_check.setChecked(True)
        self.Picomotor_check=QCheckBox('Picomotor')
        self.Picomotor_check.setChecked(False)
        self.MainLayout.addWidget(self.Rotation_check,0,0)
        self.MainLayout.addWidget(self.Spectro_check,0,1)
        self.MainLayout.addWidget(self.Camera_check,0,2)
        self.MainLayout.addWidget(self.Picomotor_check,0,3)
        self.MainLayout.addWidget(self.Spectro,1,1,3,1)
        self.MainLayout.addWidget(self.Camera,1,2,3,1)
        self.MainLayout.addWidget(self.Rotation,1,0)
        self.MainLayout.addWidget(self.Manip,2,0)
        self.MainLayout.addWidget(self.Picomotor,3,0)
        self.MainLayout.addWidget(self.Save,4,0,1,4)
        self.Picomotor.setHidden(True)
        
        self.setLayout(self.MainLayout)

    
    def connect(self):
        self.Rotation_check.stateChanged.connect(self.update_rotation)
        self.Spectro_check.stateChanged.connect(self.update_spectro)
        self.Camera_check.stateChanged.connect(self.update_camera)
        self.Picomotor_check.stateChanged.connect(self.update_picomotor)
      
            
    def active_menu_workers(self):
        """Return visible worker widgets that know how to extend the main menu bar."""
        workers = [self.Rotation, self.Spectro, self.Camera, self.Picomotor]
        return [worker for worker in workers if hasattr(worker, 'MenuBar') and not worker.isHidden()]

    def close(self):
        print('fermeture de la manip')
        self.Spectro.stop()
        self.Rotation.close()
        time.sleep(10)
        self.Camera.close()
        self.Picomotor.close()
        print('manip off')
        
    def update_rotation(self):
        self.Rotation.setHidden(not self.Rotation.isHidden())
        self.Manip.setHidden(not self.Manip.isHidden())
        self.parent().menu()
    
    def update_spectro(self):
        self.Spectro.setHidden(not self.Spectro.isHidden())
        self.parent().menu()
    
    def update_camera(self):
        self.Camera.setHidden(not self.Camera.isHidden())
        self.parent().menu()

    def update_picomotor(self):
        self.Picomotor.setHidden(not self.Picomotor.isHidden())
        self.parent().menu()
    
    

class Manip(QWidget):
    """Coordinates the angle sweep by driving the rotation and spectrometer workers."""

    consignerotation=pyqtSignal(float,int)
    
    def __init__(self,parent):
        super().__init__(parent)
        self.debut = 20 #angle par rapport à la normale du début des mesures
        # on part de 20° par rapport à la normale. Pas possible de
        #faire moins pour le moment.
        self.fin = 30 #angle de fin de mesure. 90° pas très utile. 70° est plus raisonnable 
        self.step = 1 # pas d'angle de 
        self.offset_l = 0 # un éventuel offset sur les angles de la platine par rapport à la normale
        self.offset_r = 0 # un éventuel offset sur les angles de la platine par rapport à la normale
        self.experiment=False
        self.pause=False
        self.rotation=False
        
        self.Layout()
        self.connect()
        
    def Layout(self):
        self.grid=QGridLayout()
        # Début de la mesure en angle
        self.Debut_Label=QLabel("Début")
        self.Debut_consigne=QLineEdit(str(self.debut))
        #Fin de la mesure en angle
        self.Fin_Label=QLabel("Fin")
        self.Fin_consigne=QLineEdit(str(self.fin))
        #Pas en angle
        self.Step_Label=QLabel("Step")
        self.Step_consigne=QLineEdit(str(self.step))
        
        self.Go=QPushButton("Start Acquisition")
        self.Go.setCheckable(True)
        self.Go.setStyleSheet('QPushButton {color: green;}')
        self.Pause=QPushButton("Pause")
        self.Pause.setCheckable(True)

        self.Manip_reglage=QPushButton("Reglage Manip")
        
        self.grid.addWidget(self.Debut_Label,0,0)
        self.grid.addWidget(self.Debut_consigne,0,1)
        self.grid.addWidget(self.Fin_Label,1,0)
        self.grid.addWidget(self.Fin_consigne,1,1)
        self.grid.addWidget(self.Step_Label,2,0)
        self.grid.addWidget(self.Step_consigne,2,1)
        self.grid.addWidget(self.Manip_reglage,2,2,1,2)
        self.grid.addWidget(self.Go,3,0,1,2)
        self.grid.addWidget(self.Pause,3,2,1,2)
        
        self.setLayout(self.grid)
        
    def connect(self):
        self.Go.clicked.connect(self.exp_button)
        self.Pause.clicked.connect(self.pause_button)
        self.parent().Rotation.Rotation_Thread.rotation_over.connect(self.rotation_over)
        self.parent().Rotation.Rotation_Thread.rotation_started.connect(self.rotation_started)
        
    def exp_button(self):
        if self.Go.isChecked() :
            self.Go.setText("Stop Acquisition")
            self.Go.setStyleSheet('QPushButton {color: red;}')
            self.experiment=True
            self.parent().Spectro.manip=True
            if self.parent().Spectro.spectro_choice.currentText()!='No Spectro - Refresh' and self.parent().Spectro.spectro_choice.currentText()!='non connecté'  :
                self.exp(float(self.Debut_consigne.text()),float(self.Fin_consigne.text()),\
                                                 float(self.Step_consigne.text()))
            else:
                print("il faut connecter un spectro")
                self.stop()
        else : 
            self.stop()
    
    def wait(self):
        """Let the Qt event loop breathe while the worker threads finish their move/acquisition."""
        print('wait')
        time.sleep(0.1)  #le temps peut être "long", il faut de toute façon attendre que les moteurs aient bougé et que le spectro ait fini
        app.processEvents()
        time.sleep(0.1)
        while self.rotation==True or self.parent().Spectro.spectro_fini==False or self.pause==True:
            time.sleep(.05)
            app.processEvents()
#        print(self.rotation,self.parent().Spectro.spectro_fini)
        print('wait over')
            
    def stop(self):
        self.experiment=False
        self.parent().Spectro.manip=False
        self.Go.setChecked(False)
        self.Go.setText("Start Acquisition")
        self.Go.setStyleSheet('QPushButton {color: green;}')
    
    def pause_button(self):
        if self.Pause.isChecked():
            self.parent().Spectro.form_selec1.setChecked(True)
            self.pause=True
        else :
            self.parent().Spectro.form_selec2.setChecked(True)
            self.pause=False
  
    def rotation_over(self):
        print('rotation over')
        self.rotation=False
    
    def rotation_started(self):
        print('rotation started')
        self.rotation=True
        
        
    def exp(self,Debut,Fin,Step):
        """Run the full angle-resolved acquisition sequence from background capture to final save."""
        Angles = np.arange(Debut,Fin,Step)
        acq_time=self.parent().Spectro.spectro_thread.int_time
        nmoy=self.parent().Spectro.spectro_thread.avg
        self.parent().Spectro.form_selec1.setChecked(True)
        if Debut<30:
            reply = QMessageBox.question(self, 'Message',\
                                            "Angle inférieur à 30°. Remontez la binoculaire.",\
                                            QMessageBox.Yes | 
               QMessageBox.No, QMessageBox.Yes)             
            if reply == QMessageBox.Yes:
                pass
            else:
                self.stop()
                return
        # We reset both the live trace and the kept stack so the acquisition starts from a
        # clean optical state and the saved file only contains the current sweep.
        self.parent().Spectro.clear_spectrum()
        self.parent().Spectro.clear_stackspectre()
        if self.parent().Spectro.background_select.isChecked():
            self.parent().Spectro.background_select.setChecked(False)
            self.parent().Spectro.paramchanged()
            app.processEvents()
        self.parent().Rotation.HomeL()
        self.wait()
        self.parent().Rotation.HomeR()
        self.wait()
        self.parent().Spectro.Go_spectrum()
        app.processEvents()
        self.wait()
        print('test acqtime',acq_time*(nmoy+1), 'nmoy', nmoy)
        self.parent().Spectro.savebackground()
        app.processEvents()
        # The illumination and collection arms must be positioned symmetrically before the
        # sweep starts, otherwise the optical geometry of the experiment is inconsistent.
        self.parent().Rotation.rotationL(Debut,1)
        self.wait()
        self.parent().Rotation.rotationR(Debut,1)
        self.wait()
        self.parent().Spectro.clear_spectrum()
        self.parent().Spectro.form_selec2.setChecked(True)
        print(Debut,Fin,Step)
        app.processEvents()

        # Each loop iteration acquires one spectrum, then advances both arms by the same
        # angular step to preserve the scattering geometry across the scan.
        for i in Angles:
            self.parent().Spectro.Go_spectrum()
            self.wait()
            self.parent().Rotation.rotationL(Step,2)
            self.wait()
            time.sleep(0.1)
            self.parent().Rotation.rotationR(Step,2)
            self.wait()
            time.sleep(0.1)
            app.processEvents()
            if self.experiment==False:
                    break
            time.sleep(0.1)
            
        if self.experiment==True:     
            self.parent().Rotation.HomeL()
            self.wait()
            self.parent().Rotation.HomeR()
            self.wait()
        
        self.stop()
            
        reply = QMessageBox.question(self, 'Message',\
                                            "Voulez-vous enregistrer le fichier ?",\
                                            QMessageBox.Yes | 
               QMessageBox.No, QMessageBox.Yes)             
        if reply == QMessageBox.Yes:
            print('yes')
            
            fichier=self.parent().Save.filename()[:-4]
            boo=self.parent().Save.existing_file(fichier+'.npz')
            print(boo)
            if boo==True:
                fichier=fichier
                self.parent().Save.numfile+=1
                self.parent().Save.File_number.setValue(self.parent().Save.File_number.value()+1)
                pass
            else:
                compteur=0
                fichier+='_'+str(compteur)
                while os.path.exists(fichier + ".npz" ):
                    compteur+=1
                    fichier = fichier[0:-2] + "_" + str(compteur)
                print(os.path.split(fichier))
                self.parent().Save.prefix_file_name.setText(os.path.split(fichier)[1][:-1])
                self.parent().Save.File_number.setValue(compteur)
            print(fichier)
            notes = self.parent().Save.save_note.toPlainText()+ "\n"+ "\n"
            print(notes)
            payload = self.parent().spectro_module.spectrum_save_payload(
                self.parent().Spectro,
                acq=acq_time,
                nmoy=nmoy,
            )
            payload['Angles'] = Angles
            np.savez(fichier, notes=notes, **payload)
        else:
            return
        

class Save(QWidget):
    """Shared save panel used by the master to persist spectra and camera frames."""
    
    def __init__(self,parent):
        super().__init__(parent)
        self.savepath = os.getcwd()
        self.Layout()
        self.connect()
        
    def Layout(self):
        self.save_layout = QGridLayout()
        
        self.save_spectrum_button = QPushButton ('Save Spectrum')
        self.save_image_button = QPushButton('Save Image')

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
        self.save_layout.addWidget(self.save_spectrum_button,0,3)
        self.save_layout.addWidget(self.save_image_button,1,3)
        self.save_layout.addWidget(self.save_note,0,4,3,3)
        
        self.setLayout(self.save_layout)
        
    
    def connect(self):
        self.file_loc.textChanged.connect(self.changesavepath)
        self.location_button.clicked.connect(self.opensaveloc)
        self.save_spectrum_button.clicked.connect(self.save_spectrum)
        self.save_image_button.clicked.connect(self.save_image)
 
    def opensaveloc(self): 
        #https://pythonprogramming.net/file-saving-pyqt-tutorial/
        file_name=self.filename() 
        file_name = QFileDialog.getSaveFileName(self, 'Save File',file_name,".npz")[0]
        if not file_name:
            return
        notes = self.save_note.toPlainText()+ "\n"+ "\n"
        np.savez(
            file_name,
            notes=notes,
            **self.parent().spectro_module.spectrum_save_payload(self.parent().Spectro)
        )
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
    
    def save_spectrum(self):
        reply = QMessageBox.question(self, 'Message',\
                                            "Voulez vous enregistrer le spectre en cours ?", QMessageBox.Yes | 
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
        np.savez(
            file_name,
            notes=notes,
            **self.parent().spectro_module.spectrum_save_payload(self.parent().Spectro)
        )
        self.numfile+=1
        self.File_number.setValue(self.File_number.value()+1)
    
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
        np.savez(file_name, notes=notes, Image = self.parent().Camera.frame,\
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