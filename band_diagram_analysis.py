#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Band-diagram filtering and fitting helpers used by the spectroscopy GUIs.

The module mixes three responsibilities that are tightly coupled in the original workflow:
- analytic line-shape models used as fit primitives;
- FFT-based filtering of angle-resolved band diagrams;
- sequential fit helpers that reuse one fit result as the seed for the next curve.
"""

import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import scipy.interpolate as interpo
from scipy.optimize import curve_fit


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
    """Simple hyperbolic helper used for quick dispersion overlays."""
    return A/(x-x0)

class Sin():
    r""" Sin class to generate a sin function.
    
    """
    def __init__(self,x0,Omega,A):
        self.x0=x0
        self.Omega=Omega
        self.A=A
        self.param=[self.x0,self.Omega,self.A]
        
    def function(self,x,x0,Omega,A):
        r""" Fonction sinus
        .. math:: A*\sin{\omega*(x-x_0)}
        """
        return A*np.sin(Omega*(x-x0))
    
    def get_values(self):
        return self.param
    
    def reinit(self):
        '''Reinitialize the values of the parameter to the original called ones
        returns self'''
        self.param=[self.x0,self.Omega,self.A]
        return self
    
    def __repr__(self):
        string="Sin class. Param={}".format(str(self.param))
        return string
    
    def __str__(self):
        string="Sin class. Parameters are x0={}, Omega={}, A={}".format(*self.param)
        return string

class Fano():
    r""" Fano class to generate a fano profil function.
    
    """
    def __init__(self,x0,Gamma,A,q=10):
        self.x0=x0
        self.Gamma=Gamma
        self.A=A
        self.q=q
        self.param=[self.x0,self.Gamma,self.A,self.q]
        
    def function(self,x,x0,Gamma,A,q):
        r""" Fonction Fano
        .. math:: \frac{A(q.\Gamma+2*(x-x0))}{(\Gamma^2+4*(x-x0)^2)}
        """
        num=q*Gamma + 2*(x-x0)
        denom=Gamma**2 + 4*(x-x0)**2
        return A*(num**2/denom)
    
    def get_values(self):
        return self.param
    
    def reinit(self):
        '''Reinitialize the values of the parameter to the original called ones
        returns self'''
        self.param=[self.x0,self.Gamma,self.A,self.q]
        return self
    
    def __repr__(self):
        string="Fano class. Param={}".format(str(self.param))
        return string
    
    def __str__(self):
        string="Fano class. Parameters are x0={}, Gamma={}, A={}, q={}".format(*self.param)
        return string

class Gaussian():
    r""" Gaussian class to generate a gaussian function.
    
    """
    def __init__(self,x0,Gamma,A):
        self.x0=x0
        self.Gamma=Gamma
        self.A=A
        self.param=[self.x0,self.Gamma,self.A]
        
    def function(self,x,x0,Gamma,A):
        r""" Fonction Gaussian
        
        .. math:: \frac{A}{\Gamma*\sqrt{2}*\pi}*e^{\frac{-(x-x_0)^2}{2*\Gamma^2}}
        
        """
        expo=-(x-x0)**2/(2*Gamma**2)
        norm=A/(Gamma*np.sqrt(2)*np.pi)
        return norm*np.exp(expo)
    
    def get_values(self):
        return self.param
    
    def reinit(self):
        '''Reinitialize the values of the parameter to the original called ones
        returns self'''
        self.param=[self.x0,self.Gamma,self.A]
        return self
    
    def __repr__(self):
        string="Gaussian class. Param={}".format(str(self.param))
        return string
    
    def __str__(self):
        string="Gaussian class. Parameters are x0={}, Gamma={}, A={}".format(*self.param)
        return string

class Lorentz():
    r""" Lorentz class to generate a lorentzian function.
    
    """
    def __init__(self,x0,Gamma,A):
        self.x0=x0
        self.Gamma=Gamma
        self.A=A
        self.param=[self.x0,self.Gamma,self.A]
        
    def function(self,x,x0,Gamma,A):
        r""" Fonction Lorentz
        
        .. math:: a+bx+cx^2+ \frac{A}{1+4*(x-x0)^2/\Gamma^2}
        
        """
        num=A
        denom=1+4*((x-x0)/Gamma)**2
        return num/denom
    
    def get_values(self):
        return self.param
    
    def reinit(self):
        '''Reinitialize the values of the parameter to the original called ones
        returns self'''
        self.param=[self.x0,self.Gamma,self.A]
        return self
    
    def __repr__(self):
        string="Lorentz class. Param={}".format(str(self.param))
        return string
    
    def __str__(self):
        string="Lorentz class. Parameters are x0={}, Gamma={}, A={}".format(*self.param)
        return string

class Polynom():
    r""" Polynom class to generate a polynomial function.
    
    """
    def __init__(self,n=1,array=[1,1]):
        self.n=n
        self.array=array
        if len(array)<n+1:
            while len(array)<n: self.array.append(1) 
        elif len(array)>n+1:
            self.array=self.array[:n+1]
        self.param=self.array
        
    def function(self,x,*args):
        r""" Fonction polynom of degree n
        """
        return np.poly1d(args)(x)
    
    def get_values(self):
        return self.param
    
    def reinit(self):
        '''Reinitialize the values of the parameter to the original called ones
        returns self'''
        self.param=self.array
        return self
    
    def __repr__(self):
        string="Polynom class. Degree {}, Param={}".format(self.n,str(self.param))
        return string
    
    def __str__(self):
        string="Polynom class of degree {}. Parameters are x0={}, Gamma={}, A={}".format(self.n,*self.param)
        return string

def fitmultiple(x,*args,**kwargs):
    """Evaluate a sum of fit primitives from the flattened optimizer parameter vector."""
    start=0
    end=0
    fitmul=0
    for func in kwargs['function']:
        end+=len(func.param)
        # curve_fit hands back one flat parameter list; each primitive consumes only its own slice.
        fitmul = fitmul + func.function(x,*args[start:end])
        start=end
    return fitmul 
        
def fit(FREQ,sig,bornes,function=[Fano(1,1,1,1)]):
    """Fit one spectrum on the selected bounds with the current set of analytical functions."""
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
    # The fit starts from the parameters currently stored on each function object. In the scan
    # workflow those values are deliberately recycled from the previous curve to stabilize tracking.
    #print(seed)
    def fitfit(x,*args):
        return fitmultiple(x,*args,function=funcfit)
    a,b=curve_fit(fitfit,FREQ[bornes],sig[bornes],seed,maxfev=500000)
    bestv=[a]
    fit.append(fitfit(np.arange(Emin,Emax,step),*a))
    bestv=np.asarray(bestv).reshape(1,len(seed))
    return bestv,fit
    

def plot_fit(FREQ,function,sig,table,bornes,plot=False,delta=0.003,shift=True,initfunc=True):
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
    if plot==True:
        fig = plt.figure()
    for n,i in enumerate(table):
        a,b=fit(FREQ,sig[i],bornes,function=function)
        start=0
        end=0
        for func in function:
            end+=len(func.param)
            # Propagate the fitted parameters back to each function object so the next spectrum can
            # start from a nearby solution instead of restarting from the original seed.
            func.param=a[0][start:end]
            start=end
        bestval.append(a)
        yfit.append(b)
        Q.append(abs(bestval[n][0][0]/bestval[n][0][1]))
        Emin=min(FREQ[bornes[0]],FREQ[bornes[-1]])
        Emax=max(FREQ[bornes[0]],FREQ[bornes[-1]])
        step=(Emax-Emin)/500
        if plot==True:
            plt.plot(FREQ[bornes],sig[i][bornes],'-')
            plt.plot(np.arange(Emin,Emax,step),yfit[n][0],'-')
        #print(seed[0])
        if shift == True:
            # Recenter the fitting window around the fitted resonance. This follows a dispersive
            # branch across angle while keeping the optimizer focused on the same physical mode.
            Em=(np.abs(FREQ-a[0][0]-delta)).argmin()
            #print(Em)
            EM=(np.abs(FREQ-a[0][0]+delta)).argmin()
            #print(EM)
            bornes=np.arange(min(Em,EM),max(Em,EM))
        printProgressBar(n + 1, len(table), prefix = 'Fit in Progress:', suffix = 'Complete', length = 50)
    bestval=np.asarray(bestval).reshape(-1,len(a[0]))
    return table,bestval,Q,yfit


def filtre(nom,nom_ref='ones',periode=384):
    r""" fonction de filtre par FFT des diagrammes de bande
    
    Parameters
    -----------
    nom : string
        nom + chemin du fichier à filtrer
    nom_ref : str, optionel
        nom + chemin du fichier contenant le spectre de référence
        par défaut, génére une liste contenant des 1
    periode : int, optionel
        période du cristal mesuré
        par défaut 384
    
    Returns
    ----------
    FREQ : array
        tableau contenant les énergies des spectres.
        (dépend du spectro utilisé)
    sig_filtre : array
        signal filtré
    Angles : array
        liste des angles mesurés
    sig : array
        données brutes

    """
    try:
        mat = sp.io.loadmat(nom)
        sig = mat['signal']
        Lambdas = mat['lambdas'][0]
        Angles = mat['Angles'] [0]
    except:
        mat=np.load(nom)
        sig = mat['signal']
        Lambdas = mat['lambdas']
        Angles = mat['Angles']
 
    
   
    if nom_ref != 'ones':
        mat=np.load(nom_ref)
        sig_ref = mat['signal'][0]
    else :
        sig_ref = np.ones(len(Lambdas))
    sig=sig/sig_ref
    
    if len(sig)!=len(Angles):
        sig=sig[-len(Angles):]
    Ninterp_angle = 1024
    Nfreq = len(Lambdas)
    FREQ = (periode/Lambdas.flatten())
    freq = np.linspace(FREQ[0], FREQ[-1], Nfreq)
    COStheta = (np.cos(np.arcsin(1/1.45*np.sin(np.pi/180*Angles.flatten()))))
    # The FFT filtering behaves better on a grid that is closer to reciprocal space than on the raw
    # acquisition angle. The Snell-Descartes conversion approximates that projected wavevector axis.
    costheta = np.linspace(COStheta[0],COStheta[-1],Ninterp_angle)
    sig_contrast = 1/(np.max(sig)-np.min(sig))*sig+1-np.max(sig)/(np.max(sig)-np.min(sig))
    
    f_interp = interpo.interp2d(FREQ[::-1], COStheta[::-1], sig_contrast[::-1,::-1], kind='cubic')
    sig_interp = f_interp(freq[::-1], costheta[::-1])[::-1,::-1]
    mean=np.mean(sig_interp)

    kx = np.r_[np.arange(0,Nfreq/2), np.arange(-Nfreq/2,0)].astype(float)
    ky =  np.r_[np.arange(0, Ninterp_angle / 2,1/3), np.arange(-Ninterp_angle / 2, 0,1/3)].astype(float)
    largefx=8;largefy=4;posx=9;posy=3.3;
    filtre=1
    decalx=253;decaly=166
    filtre=filtre_gauss(0,0,1,7,kx,ky,posx,posy,largefx,largefy)*\
            filtre_gauss(decalx,0,0,3,kx,ky,posx,posy,largefx,largefy)*filtre_gauss(-decalx,0,0,3,kx,ky,posx,posy,largefx,largefy)*\
            filtre_gauss(0,decaly,0,3,kx,ky,posx,posy,largefx,largefy)*filtre_gauss(0,-decaly,0,3,kx,ky,posx,posy,largefx,largefy)*\
            filtre_gauss(0,18,0,3,kx,ky,posx,posy,largefx,largefy)*filtre_gauss(0,-18,0,3,kx,ky,posx,posy,largefx,largefy)
    
    
    taille=np.size(sig_interp,0)
    # Mirror-padding the interpolated diagram limits edge discontinuities before the FFT, which
    # reduces ringing when the reciprocal-space mask is applied.
    sig_interp=np.vstack((sig_interp[::-1,:],sig_interp,sig_interp[::-1,:]))

    filtre = filtre* np.fft.fft2(sig_interp)
    filtre = np.fft.ifft2(filtre)
    filtre= filtre[taille:2*taille,:]
    
    lambdas = periode/freq
    # Convert the filtered data back to the experimental axes so downstream GUI code can keep using
    # the original wavelength/angle conventions.
    angles = 180/np.pi*np.arcsin(np.sin(np.arccos(costheta))*1.45)
    f_interp = interpo.interp2d(lambdas, angles,np.real(filtre), kind='cubic')
    sig_filtre = f_interp(Lambdas, Angles)+mean
    return FREQ,sig_filtre,Angles,sig

def fit_filtre(nom,function,points,bornes,nomref='ones',plot=False,delta=0.0035,shift=True,periode=384,initfunc=True):
    r"""Filter a band diagram, then fit the requested cuts with the provided model list.
    
    Parameters
    ------------
    
    nom : string
        nom + chemin du fichier à filtrer
    function : array
        
    points : array
        
    bornes : array
        
    plot : {False,True}, optional
        False (Defaut) ne trace pas le résultat du fit; True trace les données et le fit de chaque courbe dans une unique figure
    delta : float, optional
        if shift=True, indique l'écart entre la valeur de x0 trouvé pour le fit et les bornes pour el fit suivant ([x0-delta;x0+delta])
    
    shift : {False,True}, optional
        True (default): modifies the abscisse interval used for the fit
    
    periode : int, optional
        set the value of the periode used for normalizing the energy : periode of the photonic crystal
        default 384
        
    initfunc : {False,True}, optional
        True : (default) Reinitialize the fitting function to initial parameters stored in class variables
        
    
    Returns
    ---------
    Fano : array
        
    FREQ : array
        
    sig_filtre : array
        
    """
    FREQ,sig_filtre,Angles,sig = filtre(nom,nomref,periode=periode)
    Fit=plot_fit(FREQ,function,\
                  sig_filtre*1000,points,bornes,plot=plot,delta=delta, shift=shift,initfunc=initfunc)
    Fano=Angles[Fit[0]],*Fit[1:]
    return  Fano, FREQ, sig_filtre
