__doc__="""Photodetector.py
Implements a class for the photodetectors. Each photodetector is implemented
in a method which contains allidentifiers and parameters required for operation.
The purpose of this class is to be inherited by the Keithley 2520 class (or
similar SMU system).


Currently supported:
	--Thorlabs S148C      InGaAs integrating sphere detector
	--Keithley 2520-INT       Ge integrating sphere detector


Copyright: Kostas Voutyras, SMART Photonics, 2018

================= Revision History ======================
v0.0.0 May 24th, 2018 - KV - Module was drafted.
v0.0.1 Oct  5th, 2018 - KV - Module was implemented.
v0.0.2 Oct  8th, 2018 - KV - ThorlabsPD and KeithleyPD were implemented.
"""



__version__ = '0.0.2'
__author__  = 'Kostas Voutyras, kostas.voutyras@smartphotonics.nl'



import os, sys
import logging

sys.path.append('../')
from API.Instrument import Instrument

from scipy.interpolate import interp1d
from phiola.utils.datafiles import PhiOlaDataReader



logger=logging.getLogger('test.bt_pd_lib')


class Photodetector(Instrument):
	"""This class implements the Photodetector.
	Contains the methods:
		-- __init__()
		--connect()
	"""

	def __init__(self):

		self.ID = None
		self.dr=PhiOlaDataReader()

		self.find_all_detectors()
		self.lg = logger.getChild(self.__class__.__name__)
		self.lg.info('Photodetector initialized')

		super().__init__()


	def set_ID(self, ID):
		"""Sets the photodetector ID.
		"""

		if self.is_supported(ID):
			self.ID=ID
		else:
			self.lg.error('Photodetector {} not supported'.format(ID))
			raise ValueError('Photodetector {} is not supported.\n Currently supported:{}'.format(ID, self.supported_detectors))

		self.configure()

	def is_supported(self, ID):
		if ID in self.supported_detectors:

			return True
		else:
			return False


	def get_responsivity_file_dir(self):
		"""Sets the base directory
		"""
		if __name__!='__main__':
			rfd=os.path.join('Photodetector','responsivity files')
		else:
			rfd=os.path.join('responsivity files')
		return rfd



	def find_all_detectors(self):
		"""Finds all the supported detectors
		"""
		d=self.get_responsivity_file_dir()
		_, __, fls=os.walk(d).__next__()
		self.supported_detectors = [f.strip('.txt') for f in fls]


	def set_wavelength(self, wvl):
		"""Sets the working wavelength.
		"""

		self.wvl=wvl
		self.lg.debug('Wavelength set to:()'.format(wvl))

	def get_wavelength(self, wvl):
		"""Returns the working wavelength.
		"""
		return self.wvl




	def connect(self,port=None):
		"""
		"""
		super().connect()



	def release(self,**kwargs):
		""" Releases the photodetector.
		"""

		self.lg.debug('Released')
		super().release()


	def get_ID(self):
		"""
		"""
		super().get_ID()
		return self.ID

	def reset(self):
		""" Resets the photodetector
		"""

		self.wvl      = None
		self.r        = None
		self.interp   = None
		self.r_unit   = None
		self.wvl_unit = None

		self.	lg.debug('Photodetector was reset')
		super().reset()

	def configure(self):
		"""Configure the photodetector
		"""

		self.load_configuration_file()
		self.configured=True
		super().configure()


	def is_configured(self):
		"""Returns the boolean status of the configuration.
		"""
		super().is_configured()
		return self.configured

	def get_configuration(self):
		"""Returns the status of the configuration in a dictionary.
		"""

		return {'ID': self.ID,
					'wavelength': self.wvl,
		        'wavelength_unit': self.wvl_unit,
					'responsivity': self.r,
		        'responsivity_unit': self.r_unit,
					'is_configured': self.is_configured(),
					'config_file': self.config_f
					}

	def load_configuration_file(self):
		"""Loads the configuration file from the folder 'responsivity files'.
		"""
		# Form the filename and destination folder

		config_fn = '{}{}'.format(self.get_ID(),'.txt')
		self.config_f = os.path.join(self.get_responsivity_file_dir() , config_fn)

		# Open the file, read the data
		stream = self.dr.read_file(fname=self.config_f)

		w = stream['Wavelength, nm']
		r = stream['Responsivity, A/W']

		self.wvl_unit='nm'
		self.r_unit='A/W'
		self.lg.debug('Read configuration file: {}'.format(self.config_f))

		self.interpolate(w = w, r = r)

	def interpolate(self, w, r):
		"""Performs an 1-D interpolation of the responsivity vs the wavelength.
		"""
		self.interp = interp1d(w, r, kind = 'quadratic')


	def get_responsivity(self, wvl=None):
		"""Returns the responsivity value for a given wavelength.
		"""
		if wvl:
			self.r=self.interp(wvl)
		else: # use the set wavelength
			self.r=self.interp(self.wvl)

		self.	lg.debug('Calculated responsivity value: {} {}, for wavelength: {} {}'.format(self.r,
																																   self.r_unit,
																															      self.wvl,
																																   self.wvl_unit))
		return self.r




class ThorlabsPD(Photodetector):
	"""Implements a Thorlabs S148C photodetector.
	The class inherits from Photodetector.
	"""
	def __init__(self):
		super().__init__()
		super().set_ID(ID='THORLABS S148C')


class KeithleyPD(Photodetector):
	"""Implements a Keithley 2520-INT-Ge photodetector.
	The class inherits from Photodetector.
	"""
	def __init__(self):
		super().__init__()
		super().set_ID(ID='KEITHLEY 2520-INT-Ge')


if __name__=='__main__':

	p=Photodetector()
	p.set_ID(ID='THORLABS S148C')

	p.set_wavelength(wvl=1551)
	r=p.get_responsivity()
	print (r)
	p=ThorlabsPD()
	#p.set_wavelength(wvl=1551)
	r=p.get_responsivity()

	print (r)
	p.release()
