# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 14:48:33 2018

This script tests the interpolation of the responsivity curve.

@author: KostasVoutyras
"""

from Photodetector import Photodetector
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import numpy as np



p=Photodetector()

p.set_ID(ID='THORLABS S148C')
p.load_configuration_file()

w=p.wavelengths
r=p.responsivities



f=interp1d(w,r, kind = 'quadratic')


#w_calc=np.linspace(min(w), max(w), 1500)
#r_interp=f(w_calc)

w_rand=2175.022
r_rand=f(w_rand)

plt.plot(w,r, 'bo')
#plt.plot(w_calc,r_interp)
plt.plot(w_rand,r_rand,'ro')

plt.show()

