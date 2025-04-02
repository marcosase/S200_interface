"""
Created on Jul 2nd 2018

@author: KostasVoutyras


================= Revision History ======================
v0.0.1   Jul  2nd, 2018 - Module was implemented
v0.0.2 - Sep 27th, 2018 - Added method unload_sample

v0.0.3 - Apr  5th, 2019 - Modified method unload_sample
"""


class LoadSample:

	def __init__(self):
		print('LoadSample initiated')
		self.counter=0
		self.sample_loaded=False
		
		
	def init_loading_process_(self, eq):
		"""
		"""
		print('passed prober instance')
		
		
		self.eq=eq
		self.p=self.eq.prober

		
	def load_sample(self):
		print ('\nLoad the sample\n')
		self.p.set_light(on=True)
		self.p.move_to_manual_load_position()
		
		inp=input('\nPress enter when done:')
		if inp:
			self.counter=1
		
	def close_door(self):
		print ('\nClose the door\n')
		inp=input('\nPress enter when done:')
		if inp:
			self.counter=2
		
		
	def lock_door(self):
		print('Locking door')
		self.p.set_lock_door(lock=True)
		
		inp=input('\nPress enter when done:')
		if inp:
			self.counter=3
			self.sample_loaded=False
		
			
	def is_loaded(self):

		if self.counter==3:
			return self.sample_loaded
		
	def unload_sample(self):
		print ('\nUnloading sample\n')
		self.p.set_light(on=False)
		self.p.move_to_manual_load_position()
