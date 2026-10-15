__doc__="""test_pd.py
This is a test script used for checking the Photodetector class.
Last revision: May 24th, 2018 : Module was implemented

Copyright: Kostas Voutyras | SMART Photonics, 2018
"""
__author__='Kostas Voutyras, kostas.voutyras@smartphotonics.nl'
__version__=0.0






import logger,logging

from photodetector import Photodetector


logger = logging.getLogger('test.test_bt')
logger.propagate=True


logger.info('I initialized the photodetector')
p=Photodetector()
print ('Using Keithley detector values')
p.keithley_detector(wavelength=1550)
print (p.return_values())

logger.info('I released the photodetector')