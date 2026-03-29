#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  6 15:00:15 2018

@author: leonard
"""

from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import cbook
from matplotlib import cm
from matplotlib.colors import LightSource
import scipy.interpolate as interpo
from scipy.signal import butter, lfilter, freqz, sosfilt

def butter_lowpass(cutoff, fs, order=5,output='ba'):
    """Return Butterworth low-pass coefficients in transfer-function or SOS form."""
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    if output=='ba':
        b, a = butter(order, normal_cutoff, btype='low', analog=False,output=output)
        return b, a
    elif output=='sos':
        sos = butter(order, normal_cutoff, btype='low', analog=False,output=output)
        return sos

def butter_lowpass_filter(data, cutoff, fs, order=5,output='ba'):
    """Filter a 1D trace while keeping the calling code agnostic to the chosen representation."""
    if output=='ba':
        b, a = butter_lowpass(cutoff, fs, order=order,output=output)
        y = lfilter(b, a, data)
    elif output=='sos':
        sos = butter_lowpass(cutoff, fs, order=order,output=output)
        y = sosfilt(sos, data)
    return y

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

def filtre_image(nom,nom_ref='ones',periode=384):
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


    mat=np.load(nom)
    Image = mat['Image']    
    
    Image=Image.T
    plt.figure();plt.pcolormesh(Image)
    Vertical=np.arange(0,len(Image))
    Ninterp_angle = 4096
    theta0=56
    deltatheta=4.5
    Angles=np.linspace(theta0+deltatheta,theta0-deltatheta,len(Image.T))
    # The angular axis is remapped through the collection geometry and Snell-Descartes
    # law so the interpolation is done in a coordinate closer to in-plane momentum.
    COStheta = (np.cos(np.arcsin(1/1.45*np.sin(np.pi/180*Angles.flatten()))))
    costheta = np.linspace(COStheta[0],COStheta[-1],Ninterp_angle)
    Image_contrast = Image/np.max(Image)
    #Image_contrast = 1/(np.max(Image)-np.min(Image))*Image+1-np.max(Image)/(np.max(Image)-np.min(Image))
    
    f_interp = interpo.interp2d(COStheta[::-1], Vertical, Image_contrast, kind='cubic')
    sig_interp = f_interp(costheta[::-1], Vertical)[::-1]
    #plt.figure();plt.pcolormesh(sig_interp[850:1150,1550:2550])
    
    mean=np.mean(sig_interp/(1-sig_interp))
    
    # The contrast transform and FFT make the periodic fringes appear as localized peaks
    # in reciprocal space, which is where the Gaussian masks are applied.
    spectre = np.fft.fft2(sig_interp/(1-sig_interp)-np.mean(sig_interp/(1-sig_interp)))
    plt.figure();plt.imshow(np.fft.fftshift((np.abs(spectre))),norm=mpl.colors.LogNorm())
    
    #spectre4 = [np.fft.fft(1/(1-i)) for i in sig_interp]  
    
    ky = np.r_[np.arange(0,len(Image)/2), np.arange(-len(Image)/2,0)].astype(float)
    kx =  np.r_[np.arange(0, Ninterp_angle / 2,1/2), np.arange(-Ninterp_angle / 2, 0,1/2)].astype(float) #
    largefx=10;largefy=40;posx=20;posy=12;
    filtre=1;
    decalx=153;
    filtre= filtre* filtre_gauss(0,0,1,2,kx,ky,posx,posy,largefx,largefy)*\
                    filtre_gauss(decalx,0,0,1,kx,ky,posx,posy,largefx,largefy)*filtre_gauss(-decalx,0,0,1,kx,ky,posx,posy,largefx,largefy)*\
                    filtre_gauss(2*decalx,0,0,1,kx,ky,posx,posy,largefx,largefy)*filtre_gauss(-2*decalx,0,0,1,kx,ky,posx,posy,largefx,largefy)
                    
    #plt.figure();plt.imshow(np.fft.fftshift(1-filtre),vmin=0,vmax=1)
    taille=np.size(sig_interp,1)
    sig_interp=np.hstack((sig_interp[::-1,:],sig_interp))

    filtre = filtre* np.fft.fft2(1/(1-sig_interp)-np.mean(1/(1-sig_interp)))
    plt.figure();plt.imshow(np.fft.fftshift(np.abs(np.real(filtre))),norm=mpl.colors.LogNorm())
    filtre = np.fft.ifft2(filtre)
    filtre= filtre[:,taille:]
    
    
    
    angles = 180/np.pi*np.arcsin(np.sin(np.arccos(costheta))*1.45)

    f_interp = interpo.interp2d(angles, Vertical[::-1],np.real(filtre), kind='cubic')
    sig_filtre = f_interp(Angles, Vertical[::-1])+mean
    plt.figure();plt.pcolormesh(sig_filtre,vmin=-0.1,vmax=1.2)
    return Vertical,sig_filtre,Angles,Image

def filtre_ligne_butter(Image,order = 15,cutoff = 120, plot=False,interp=False,output='ba'):
    r""" fonction de filtre passe bas Butterworth ligne par ligne des images
    
    Parameters
    -----------
    Image : array
        données à filtrer
    order : int, optionel
        ordre du filtre
    cutoff : int, optionel
        fréquence du cutoff. Typiquement pour la fréquence du FP observé est de 150
    plot : bool, optionel
        tracer de la figure avec le filtre, le signal brut et filtré sur une coupe, l'image brut et filtré
    
    Returns
    ----------
    
    Image_filtre : array
        signal filtré
    Image : array
        données brutes

    Ref
    -----------
    https://stackoverflow.com/questions/25191620/creating-lowpass-filter-in-scipy-understanding-methods-and-units

    """

    Image=Image.T
    Vertical=np.arange(0,len(Image))
    Ninterp_angle = 4096
    theta0=56
    deltatheta=4.5
    Angles=np.linspace(theta0+deltatheta,theta0-deltatheta,len(Image.T))
    COStheta = (np.cos(np.arcsin(1/1.45*np.sin(np.pi/180*Angles.flatten()))))
    costheta = np.linspace(COStheta[0],COStheta[-1],Ninterp_angle)
    Image_contrast = Image/np.max(Image)
   
    f_interp = interpo.interp2d(COStheta[::-1], Vertical, Image_contrast, kind='cubic')
    sig_interp = f_interp(costheta[::-1], Vertical)[::-1]

    # Filter requirements.
    if interp == True:
        Image_filtre=np.ones((len(sig_interp),len(sig_interp.T)))        
        # In interpolated mode we filter along the momentum-like axis after the optical
        # reparameterization, which gives a cleaner separation of the Fabry-Perot fringe.
        for n,data in enumerate(sig_interp):
            fs = len(data)       # sample rate, Hz
            
            # Get the filter coefficients so we can check its frequency response.
            y = butter_lowpass_filter(data, cutoff, fs, order,output=output)
            Image_filtre[n]=y
        
        angles = 180/np.pi*np.arcsin(np.sin(np.arccos(costheta))*1.45)
        f_interp = interpo.interp2d(angles, Vertical[::-1],np.real(Image_filtre), kind='cubic')
        sig_filtre = f_interp(Angles, Vertical[::-1])
        data=sig_interp[950]
    else:
        Image_filtre=np.ones((len(Image),len(Image.T)))        
        # In raw mode the filter is applied line by line on the detector axis, which is
        # faster and avoids the interpolation cost when a rough cleaning is enough.
        for n,data in enumerate(Image_contrast):
            fs = len(data)       # sample rate, Hz
            
            # Get the filter coefficients so we can check its frequency response.
            y = butter_lowpass_filter(data, cutoff, fs, order,output=output)
            Image_filtre[n]=y
        sig_filtre=Image_filtre  
        data=Image_contrast[950]
    if plot==True:
        
        # Plot the frequency response.
        b,a=butter_lowpass(cutoff, fs, order,output='ba')     
        w, h = freqz(b, a, worN=8000)
        plt.figure()
        plt.subplot(2, 2, 1)
        plt.plot(0.5*fs*w/np.pi, np.abs(h), 'b')
        plt.plot(cutoff, 0.5*np.sqrt(2), 'ko')
        plt.axvline(cutoff, color='k')
        plt.xlim(0, 0.5*fs)
        plt.plot(np.log10(abs(np.fft.fft(data))))
        plt.title("Lowpass Filter Frequency Response")
        plt.xlabel('Frequency [Hz]')
        plt.grid()
        
        y = butter_lowpass_filter(data, cutoff, fs, order,output=output)
        plt.plot(np.log10(abs(np.fft.fft(y))))
        
        plt.subplot(2, 2, 2)
        plt.plot(Image_contrast[1150], 'b-', label='data')
        plt.plot(sig_filtre[1150], 'g-', linewidth=2, label='filtered data')
        plt.grid()
        plt.legend()
        
        plt.subplot(2,2,3);
        plt.pcolormesh(Image)
        
        plt.subplot(2,2,4)
        plt.pcolormesh(sig_filtre)
        
        plt.subplots_adjust(hspace=0.35)
        plt.show()
    
    return sig_filtre,Image


if __name__ == '__main__':
    repertoire='/home/leonard/Bureau/python/ImageCP/'
    name=['Im_Quartz_B1A3_las40_cam40_lasT21_GX+101.npz',\
         'Im_Quartz_B1A3_las40_cam40_lasT21_GX+122.npz',\
         'Im_Quartz_B1A3_las40_cam40_lasT21_GX+143.npz',\
         'Im_Quartz_B1A3_las40_cam40_lasT21_GX+164.npz',\
         'Im_Quartz_B1A3_las40_cam40_lasT21_GX+185.npz',\
         'Im_Quartz_B1A3_las40_cam40_lasT21_GX+206.npz',\
         'Im_Quartz_B1A3_las40_cam40_lasT21_GX+227.npz',\
         'Im_Quartz_B1A3_las40_cam40_lasT21_GX+248.npz',\
         ]
    
    projX=[]
    for nom in name:
        mat=np.load(repertoire + nom)
        Image=mat['Image']
        projX.append(mat['signalX'][1][1])
        im,image=filtre_ligne_butter(Image,order=10,cutoff=60,plot=True,interp=False,output='ba')
    #    x=np.arange(0,2448)
    #    y=np.arange(0,200,12)
    #    z=np.asarray([np.sum(im[1000+i:1002+i],axis=0) for i in y])
    #    x, y = np.meshgrid(x, y)
    #    fig, ax = plt.subplots(subplot_kw=dict(projection='3d'))
    #    ls = LightSource(270, 45)
    #    rgb = ls.shade(z, cmap=cm.gist_earth, vert_exag=0.1, blend_mode='soft')
    #    surf = ax.plot_surface(x, y, z, rstride=1, cstride=1, facecolors=rgb,
    #                           linewidth=0, antialiased=False, shade=False)
    projX_fil=[]    
    for data in projX:
        fs = len(data)       # sample rate, Hz
                
        # Get the filter coefficients so we can check its frequency response.
        data = butter_lowpass_filter(data, 60, fs, 10,output='ba')
        projX_fil.append(data)
        
    plt.figure();[plt.plot(i) for i in projX_fil]
    
    plt.figure();plt.plot(projX_fil[7])