__doc__="""photodetector.py
Implements a class for the photodetectors. Each photodetector is implemented 
in a method which contains allidentifiers and parameters required for operation. 
The purpose of this class is to be inherited by the Keithley 2520 class (or 
similar SMU system).


Currently supported: --Keithley 2520-INT       Ge integrating sphere detector
					 --Thorlabs S148C Ext. InGaAs integrating sphere detector


Last revision: 
		-May 24th, 2018 : Module was implemented

		
		
Copyright: Kostas Voutyras | SMART Photonics, 2018		
"""
__author__='Kostas Voutyras, kostas.voutyras@smartphotonics.nl'
__version__=0.0




import logging


logger=logging.getLogger('test.bt_pd_lib')


class Photodetector:
	"""This implements a class for the photodetectors. Each photodetector is implemented in a method which contains all
	identifiers and parameters required for operation. 
	
	The purpose of this class is to be inherited by the Keithley 2520 class (or similar SMU system).
	
	"""
	
	def __init__(self):
		"""Instance variables required:
			--self.color_code 				: Color code identifier for operator. It should feature a combination of color & pattern (for colorblind operators)
			--self.serial					: Serial number of a photodetector
			--self.model					: Photodetector model
			--self.manufacturer				: Photodetector manufacturer
			--self.detector_material		: Photodetector material
		
			--self.source_mode				: Describes if the detector should be biased with current or voltage. String 'I' or 'V'
			--self.sense_mode				: Describes whether the detector spits out current or voltage. String 'I' or 'V'
			--self.polarity					: Describes the polarity of the current flowing (if self.sense_mode=='I'. Values +1 or -1.
			--self.responsivity_curve 		: This will be an array or an polyfit instance based on the calibration array. 
								 			  **Reason**: Responsivity data is taken with a 10 nm step, we might need higher accuracy.
								 
			--self.wavelength_range	 		: This will be an array with equal length to the reponsivity_curve
		
			--self.wavelength 				: The working wavelength for a specific measurement in [nm]
			--self.responsivity				: The responsivity value for a specific self.wavelength
			--self.calib_dark_current		: Measured dark current for a specific self.bias
			--self.current_range			: Current range of the K2520 for the detector port in [mA]
			--self.bias 					: Reverse bias value for the detector to operate
			--self.max_bias       		    : Maximum permissible reverse bias allowed from manufacturer
			--self.calibrated     		    : Boolean. Sphere calibrated or not.
			--self.last_calibration_date:   : String with last calibration date. 
		
		"""
		

	def keithley_detector(self,wavelength):
		
		self.color_code					=''
		self.serial						=''
		self.model						='2520 INT-Ge'
		self.manufacturer				='Keithley'
		self.detector_material			='Ge'
		
		self.source_mode				='V'
		self.sense_mode					='I'
		self.polarity					=+1

		self.responsivity_curve			='' 
		self.wavelength_range			=''
	
		self.wavelength					=wavelength
		self.responsivity				=''
		self.calib_dark_current			=''
		
		self.current_range				=0.05 # [mA]
		self.bias						=-5   # [V]				
		self.max_bias					=-5   # [V]	
		self.calibrated					=True
		self.last_calibration_date		=''
		
		logger.info('Selected photodetector: {}, {}'.format(self.manufacturer, self.model))
		logger.info('Selected wavelength:    {} [nm]'.format(self.wavelength))


	def thorlabs_detector(self,wavelength):
		
		self.color_code					=''
		self.serial						=''
		self.model						='S148C'
		self.manufacturer				='Thorlabs'
		self.detector_material			='Extended InGaAs'
		
		self.source_mode				='V'
		self.sense_mode					='I'
		self.polarity					=+1
		
		self.responsivity_curve			='' 
		self.wavelength_range			=''
	
		self.wavelength					=wavelength
		self.responsivity				=''
		self.calib_dark_current			=''
		
		self.current_range				=0.05 # [mA]
		self.bias						=0.	  # [V]			
		self.max_bias					=-1.8 # [V]
		self.calibrated					=True
		self.last_calibration_date		=''
		
		logger.info('Selected photodetector: {}, {}'.format(self.manufacturer, self.model))
		logger.info('Selected wavelength:    {} [nm]'.format(self.wavelength))

	def return_values(self):
		return vars(self)
		
		
if __name__=='__main__':
	print (__doc__)
	p=Photodetector()
	print ('Using Keithley detector values')
	p.keithley_detector(wavelength=1550)
	print (p.return_values())
	
	print ('Using THORLABS detector values')
	p.thorlabs_detector(wavelength=1550)
	print (p.return_values())