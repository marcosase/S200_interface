#!/usr/bin/python3.8
#coding:utf-8 -*-
import pandas as pd
import time
import datetime
import sys, os
import numpy as np
from PyQt5 import QtGui	
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import *
from zipfile import ZipFile
from PyQt5.QtCore import QProcess, QTimer
import pyqtgraph as pg
import serial
import config
import re
import yaml
import glob
import signal
import subprocess
from subprocess import call
from icecream import ic
from load_sample_V2  import *
from align_sample_V2 import AlignSample
sys.path.insert(1, 'C:/AMS')
import logging
from collections.abc import MutableMapping
import telegram
import measurement_handler as measurement_handler
from readers.readers import JOBReader
from measurement_plan_maker.meas_plan_maker import MeasPlan
from equipment import Equipment
from utils.identify import Identify
from utils.misc  import generate_session_ID, get_git_commit_id, get_probes_folder, get_jobs_folder, get_data_folder,get_batch_data_folder, get_backup_folder
from utils.utils import boolean_operation, select_bar

#Real-time analysis tools
from realtime_analysis.quick_analysis import QuickAnalysis
# automated data extraction messageque support
#from utils.smg import initiate_data_extraction #Commented because it was issuing importing error  MSE
logger=logging.getLogger('test.AmsCore')
start_time = time.time()

class Ui(QtWidgets.QMainWindow):
	def __init__(self):
		 ###definitions from core.py
		#self.fe = Frontend()
		self.start_time = time.time()
		self.alignment = AlignSample()
		self.loading = LoadSample()
		self.tool_id, self.session_id = generate_session_ID()
		self.camera_picture_file_list = [] # list of file names of taken pictures
		self.quick_analysis_file_list = [] # list of output file names from quick analysis routine
		self._cell_probing_counter = 0 # counter of probing of the same cell
		self.touch_down_recorder = [] # list of successful/unsuccessful wafer "touch-down"
		self.daq_successful = False # boolean stating the acquistion has been properly performed
		self.terminal_stdout = sys.stdout
		#################
		pg.setConfigOption('background', 'w') #before loading widget
		pg.setConfigOption('foreground', 'k')
		super(Ui, self).__init__() # Call the inherited classes __init__ method
		uic.loadUi('BT_interface.ui', self) # Load the .ui file
		###Variable
		self.job_folder_path1 = ''
		self.job_folder_path2 = ''
		#Methods to perform the first touchdown and save it 
		self.btn_touch1.clicked.connect(self.touch_bar1)
		self.btn_touch2.clicked.connect(self.touch_bar2)
		self.btn_touch3.clicked.connect(self.touch_bar3)
		self.btn_touch4.clicked.connect(self.touch_bar4)
		#Method to select job files for the wafers and show it in the dialog
		self.btn_job.clicked.connect(self.select_job)
		
		self.start_jobs_btn.clicked.connect(self.start_jobs)
		self.unload_btn.clicked.connect(self.move_unload)
		self.probe_btn.clicked.connect(self.go_probe)
		self.gup_btn.clicked.connect(self.gross_up)
		self.gdn_btn.clicked.connect(self.gross_down)
		##
		self.btn_go_td1.clicked.connect(self.go_td1)
		self.btn_go_td2.clicked.connect(self.go_td2)
		self.btn_go_td3.clicked.connect(self.go_td3)
		self.btn_go_td4.clicked.connect(self.go_td4)
		##
		self.jobs_combo_box.currentTextChanged.connect(self.update_info)
		
		self.show() # Show the GUI
		self.bar.setValue(0)
		self.write_values()
		self.showMaximized()
	def gross_up(self):
		'''Method to do the gross up'''
		self.send_command(b'GUP\n')
	def gross_down(self):
		'''Method to do the gross down'''
		self.send_command(b'GDW\n')
	def move_unload(self):
		self.send_command(b'LDL\n')
		print('Moving to load position!')
		return
	def go_probe(self):
		self.send_command(b'LDC 0\n')
		print('Moving to probe position!')
		return
	def save_value(self):
		#method to save all values in interface
		print('saved!')
	def write_values(self):
		try:
			df = pd.read_csv('backup_values.csv')
			# set xy touch down values
			self.table_bar1.setItem(0, 0, QTableWidgetItem(str( int(df.X1[0]) )))
			self.table_bar1.setItem(0, 1, QTableWidgetItem(str( int(df.Y1[0]) )))
			self.table_bar2.setItem(0, 0, QTableWidgetItem(str( int(df.X2[0]) )))
			self.table_bar2.setItem(0, 1, QTableWidgetItem(str( int(df.Y2[0]) )))
			self.table_bar3.setItem(0, 0, QTableWidgetItem(str( int(df.X3[0]) )))
			self.table_bar3.setItem(0, 1, QTableWidgetItem(str( int(df.Y3[0]) )))
			self.table_bar4.setItem(0, 0, QTableWidgetItem(str( int(df.X4[0]) )))
			self.table_bar4.setItem(0, 1, QTableWidgetItem(str( int(df.Y4[0]) )))
			self.table_bar5.setItem(0, 0, QTableWidgetItem(str( int(df.X5[0]) )))
			self.table_bar5.setItem(0, 1, QTableWidgetItem(str( int(df.Y5[0]) )))
			self.line_start1.setText(df.start_index1[0])
			self.line_start2.setText(df.start_index2[0])
			self.line_start3.setText(df.start_index3[0])
			self.line_start4.setText(df.start_index4[0])
			self.line_start5.setText(df.start_index5[0])
			self.line_end1.setText(df.end_index1[0])
			self.line_end2.setText(df.end_index2[0])
			self.line_end3.setText(df.end_index3[0])
			self.line_end4.setText(df.end_index4[0])
			self.line_end5.setText(df.end_index5[0])
			
			#Set job files
			self.update_info(str(df.job[0]))
		except Exception as error:
			print(error)
			print('Write to csv  backup failed!!!')
			pass
	def ser_connect(self):
		try:
			self.ser = serial.Serial(port = 'COM1', baudrate = 38400, parity = serial.PARITY_EVEN, bytesize = serial.SEVENBITS, stopbits = serial.STOPBITS_TWO, timeout = 0.2)
			return self.ser
		except ValueError:
			self.ser.close()
			print(ValueError)
		return self.ser
	def wait_ser(self):
		while True:
			value =  self.send_command(b'GID\n')
			if value != '':
				break		
			else:
				time.sleep(0.5)
				print('waiting...')
		time.sleep(1)
	def send_command(self, command):
		ser = self.ser_connect()
		ser.flush()
		ser.write(command)
		resp = ser.readall().decode()
		ser.close()
		return resp
	def file_save(self, val):
		dic = {	'X1':[val[0]],'Y1':[val[5]],
		'X2':[val[1]],'Y2':[val[6]],
		'X3':[val[2]],'Y3':[val[7]],
		'X4':[val[3]],'Y4':[val[8]],
		'X5':[val[4]],'Y5':[val[9]],
		'job':[val[10]],
		'start_index1':[val[11]],'end_index1':[val[16]],
		'start_index2':[val[12]],'end_index2':[val[17]],
		'start_index3':[val[13]],'end_index3':[val[18]],
		'start_index4':[val[14]],'end_index4':[val[19]],
		'start_index5':[val[15]],'end_index5':[val[20]],
		}
		df = pd.DataFrame(dic)
		df.to_csv('backup_values.csv')
	def collect(self):
		
		x_td_arr      = [self.table_bar1.item(0, 0).text(),
					self.table_bar2.item(0, 0).text(),
					self.table_bar3.item(0, 0).text(),
					self.table_bar4.item(0, 0).text(),
					self.table_bar5.item(0, 0).text()]
		y_td_arr      = [self.table_bar1.item(0, 1).text(),
					self.table_bar2.item(0, 1).text(),
					self.table_bar3.item(0, 1).text(),
					self.table_bar4.item(0, 1).text(),
					self.table_bar5.item(0, 1).text()]
		#Job file names
		job_file_arr   = [self.job_id.text()]
		
		start_index_arr = [self.line_start1.text(),
					self.line_start2.text(),
					self.line_start3.text(),
					self.line_start4.text(),
					self.line_start5.text()]
		end_index_arr = [self.line_end1.text(),
					self.line_end2.text(),
					self.line_end3.text(),
					self.line_end4.text(),
					self.line_end5.text()]
					
		val_array = [*x_td_arr, *y_td_arr, job_file_arr[0], *start_index_arr, *end_index_arr]
		return val_array
	def touch_bar1(self):
		self.start_jobs_btn.setStyleSheet('background-color: rgb(255, 255, 0)')
		self.start_jobs_btn.setStyleSheet('border: 2px solid red')
		self.start_jobs_btn.setText("Wafer1 touchdown")
		self.start_jobs_btn.repaint()
		self.send_command(b'GUP\n') # Do a Gross up
		self.send_command(b'LDC\n')
		self.send_command(b'LDPH 0\n') #Go to local and the asks the user to perform a touchdown
		self.wait_ser()
		xy = self.send_command(b'PSXY\n')
		x1 = float(re.findall("-?\d+", xy)[-2])
		y1 = float(re.findall("-?\d+", xy)[-1])
		self.table_bar1.setItem(0, 0, QTableWidgetItem(str(x1)))
		self.table_bar1.setItem(0, 1, QTableWidgetItem(str(y1)))
		#save values
		self.file_save(self.collect())
		self.reset_start_btn()
	def touch_bar2(self):
		self.start_jobs_btn.setStyleSheet('background-color: rgb(255, 255, 0)')
		self.start_jobs_btn.setStyleSheet('border: 2px solid red')
		self.start_jobs_btn.setText("Wafer2 touchdown")
		self.start_jobs_btn.repaint()
		self.send_command(b'GUP\n') # Do a Gross up
		self.send_command(b'LDC\n')
		self.send_command(b'LDPH 0\n') #Go to local and the asks the user to perform a touchdown
		self.wait_ser()
		xy = self.send_command(b'PSXY\n')
		x2 = float(re.findall("-?\d+", xy)[-2])
		y2 = float(re.findall("-?\d+", xy)[-1])
		self.table_bar2.setItem(0, 0, QTableWidgetItem(str(x2)))
		self.table_bar2.setItem(0, 1, QTableWidgetItem(str(y2)))
		#save values
		self.file_save(self.collect())
		self.reset_start_btn()
	def touch_bar3(self):
		self.start_jobs_btn.setStyleSheet('background-color: rgb(255, 255, 0)')
		self.start_jobs_btn.setStyleSheet('border: 2px solid red')
		self.start_jobs_btn.setText("Wafer3 touchdown")
		self.start_jobs_btn.repaint()
		self.send_command(b'GUP\n') # Do a Gross up
		self.send_command(b'LDC\n')
		self.send_command(b'LDPH 0\n') #Go to local and the asks the user to perform a touchdown
		self.wait_ser()
		print('Touch Down Done!!!!!!')
		xy = self.send_command(b'PSXY\n')
		x3 = float(re.findall("-?\d+", xy)[-2])
		y3 = float(re.findall("-?\d+", xy)[-1])
		self.table_bar3.setItem(0, 0, QTableWidgetItem(str(x3)))
		self.table_bar3.setItem(0, 1, QTableWidgetItem(str(y3)))
		#save values
		self.file_save(self.collect())
		self.reset_start_btn()
	def touch_bar4(self):
		self.start_jobs_btn.setStyleSheet('background-color: rgb(255, 255, 0)')
		self.start_jobs_btn.setStyleSheet('border: 2px solid red')
		self.start_jobs_btn.setText("Wafer4 touchdown")
		self.start_jobs_btn.repaint()
		self.send_command(b'GUP\n') # Do a Gross up
		self.send_command(b'LDC\n')
		
		self.send_command(b'LDPH 0\n') #Go to local and the asks the user to perform a touchdown
		self.wait_ser()
		print('Touch Down Done!!!!!!')
		xy = self.send_command(b'PSXY\n')
		x4 = float(re.findall("-?\d+", xy)[-2])
		y4 = float(re.findall("-?\d+", xy)[-1])
		self.table_bar4.setItem(0, 0, QTableWidgetItem(str(x4)))
		self.table_bar4.setItem(0, 1, QTableWidgetItem(str(y4)))
		#save values
		self.file_save(self.collect())
		self.reset_start_btn()
	def touch_bar5(self):
		self.start_jobs_btn.setStyleSheet('background-color: rgb(255, 255, 0)')
		self.start_jobs_btn.setStyleSheet('border: 2px solid red')
		self.start_jobs_btn.setText("Wafer4 touchdown")
		self.start_jobs_btn.repaint()
		self.send_command(b'GUP\n') # Do a Gross up
		self.send_command(b'LDC\n')
		
		self.send_command(b'LDPH 0\n') #Go to local and the asks the user to perform a touchdown
		self.wait_ser()
		print('Touch Down Done!!!!!!')
		xy = self.send_command(b'PSXY\n')
		x4 = float(re.findall("-?\d+", xy)[-2])
		y4 = float(re.findall("-?\d+", xy)[-1])
		self.table_bar5.setItem(0, 0, QTableWidgetItem(str(x4)))
		self.table_bar5.setItem(0, 1, QTableWidgetItem(str(y4)))
		#save values
		self.file_save(self.collect())
		self.reset_start_btn()
	def update_combo_box(self,combo_object, array):
		combo_object.addItems(array)
	def select_job(self):
		job_root='C:/Users/HP/Smart Photonics/Engineering - Test & Measurement/Internal Projects/Job generation/'
		self.job_folder_path1 = QFileDialog.getExistingDirectory(self,("Open Batch Folder"), job_root)
		self.jobs_combo_box.clear()
		#Fill the first combo box with Jobs available
		job_folder_selection = glob.glob(self.job_folder_path1+'/*JOB.yaml')
		job_folder_corr = [r'{}'.format(i) for i in job_folder_selection]
		job_folder_corr = [i.replace('\\','/') for i in job_folder_corr]
		job_folder_corr = job_folder_corr[0]
		self.update_combo_box(self.jobs_combo_box, job_folder_selection)
	def update_info(self, path1=''):
		#Open selected jobfile
		if path1 != '':
			path1 = r'{}'.format(path1)
			path1 = path1.replace('\\','/')
			job_selected = path1
			filename = path1
		else:
			job_selected = self.jobs_combo_box.currentText()
			job_selected_raw = r'{}'.format(job_selected)
			job_selected_corr = job_selected_raw.replace('\\','/')
			filename = job_selected_corr

		job_root_folder = '/'.join(filename.split('/')[0:-1]) +'/'
		job_folder_selection = glob.glob(job_root_folder+'/*JOB.yaml')
		#job_folder_corr = [r'{}'.format(i) for i in job_folder_selection]
		#job_folder_corr = [ i.replace('\\','/') for i in job_folder_corr]
		#job_folder_corr = job_folder_corr[0]
		
		self.update_combo_box(self.jobs_combo_box, job_folder_selection)
		time.sleep(0.2)
		print('################')
		print(filename)
		with open(filename, 'r') as f:
			yaml_open = yaml.safe_load(f)
		acq_dict = yaml_open['acquisition settings']
		batch_dict = yaml_open['batch_information']
		cust_id = batch_dict['customer']
		batch_id =batch_dict['batch'] 
		wafer_id = batch_dict['wafers']
		prod_id = batch_dict['product']
		mmf_file = acq_dict['mmf']
		ccf_file = acq_dict['ccf']
		mdf_file = acq_dict['mdf']
		#Update the labels
		self.cust_id.setText(cust_id)
		self.batch_id.setText(batch_id)
		self.wafer_id.setText(wafer_id)
		self.prod_id.setText(prod_id)
		self.job_id.setText(filename)
		#getting the MMF
		mmf_path =  job_root_folder+ mmf_file
		df = pd.read_csv(mmf_path)
		first_td = df.iloc[0][0]
		total_files = sum(df.sum(axis=1))
		self.file_save(self.collect())
	def go_td1(self):
		self.send_command(b'LI1\n')
		xtd = self.table_bar1.item(0, 0).text()
		ytd = self.table_bar1.item(0, 1).text()
		
		command = f'GTXY {xtd},{ytd}\n'.encode()
		x = self.send_command(command)	
	def go_td2(self):
		self.send_command(b'LI1\n')
		xtd = self.table_bar2.item(0, 0).text()
		ytd = self.table_bar2.item(0, 1).text()
		
		command = f'GTXY {xtd},{ytd}\n'.encode()
		self.send_command(command)
	def go_td3(self):
		self.send_command(b'LI1\n')
		xtd = self.table_bar3.item(0, 0).text()
		ytd = self.table_bar3.item(0, 1).text()
		
		command = f'GTXY {xtd},{ytd}\n'.encode()
		self.send_command(command)
	def go_td4(self):
		self.send_command(b'LI1\n')
		xtd = self.table_bar4.item(0, 0).text()
		ytd = self.table_bar4.item(0, 1).text()
		command = f'GTXY {xtd},{ytd}\n'.encode()
		self.send_command(command)	
	def go_td5(self):
		self.send_command(b'LI1\n')
		xtd = self.table_bar5.item(0, 0).text()
		ytd = self.table_bar5.item(0, 1).text()
		command = f'GTXY {xtd},{ytd}\n'.encode()
		self.send_command(command)	
	def start_jobs(self):
		#Read from interface all wafer theta and wafers touchdown(in milidegrees and um)
		#Before starting it has to check if the check boxes are checked!
		stat_bar1 = self.check_bar1.isChecked()
		stat_bar2 = self.check_bar2.isChecked()
		stat_bar3 = self.check_bar3.isChecked()
		stat_bar4 = self.check_bar4.isChecked()
		stat_bar5 = self.check_bar4.isChecked()
		bar1 = self.check_bar1.text()
		bar2 = self.check_bar2.text()
		bar3 = self.check_bar3.text()
		bar4 = self.check_bar4.text()
		bar5 = self.check_bar4.text()
		prog_arr = ['bar1','bar2','bar3','bar4','bar5']
		stat_arr = [stat_bar1, stat_bar2, stat_bar3, stat_bar4, stat_bar5]
		
		user_name_arr  = [self.op_id.currentText(),
						self.op_id.currentText(),
						self.op_id.currentText(),
						self.op_id.currentText(),
						self.op_id.currentText()]
		job_file_arr   = [self.job_id.text(), 
						self.job_id.text(), 
						self.job_id.text(), 
						self.job_id.text(),
						self.job_id.text()]
		
		x_td_arr      = [int( self.table_bar1.item(0, 0).text().split('.')[0] ),
						int( self.table_bar2.item(0, 0).text().split('.')[0] ),
						int( self.table_bar3.item(0, 0).text().split('.')[0] ),
						int( self.table_bar4.item(0, 0).text().split('.')[0] ),
						int( self.table_bar5.item(0, 0).text().split('.')[0])]
						
		y_td_arr      = [int(self.table_bar1.item(0, 1).text().split('.')[0]),
						int(self.table_bar2.item(0, 1).text().split('.')[0]),
						int(self.table_bar3.item(0, 1).text().split('.')[0]),
						int(self.table_bar4.item(0, 1).text().split('.')[0]),
						int(self.table_bar5.item(0, 1).text().split('.')[0])]
						
		cell_index_start =[self.line_start1.text(),
						self.line_start2.text(),
						self.line_start3.text(),
						self.line_start4.text(),
						self.line_start5.text()]
				
		cell_index_end = [self.line_end1.text(),
						self.line_end2.text(),
						self.line_end3.text(),
						self.line_end4.text(),
						self.line_end5.text(),]
		if stat_arr==[False,False,False,False,False]:
				self.start_jobs_btn.setStyleSheet('background-color: rgb(255, 255, 0)')
				self.start_jobs_btn.setText("Check a wafer to measure")
				self.start_jobs_btn.repaint()
				time.sleep(1)
		for job, user, x_td, y_td, check_bar, start_index, end_index, prog in  zip(job_file_arr, user_name_arr, x_td_arr, y_td_arr,stat_arr, cell_index_start, cell_index_end, prog_arr):
			#before starting, move it to the center of the wafer
			if check_bar:
				self.go_probe()
				self.start_jobs_btn.setStyleSheet('background-color: rgb(255, 255, 0)')
				self.start_jobs_btn.setText(f"{prog} in progress")
				self.start_jobs_btn.repaint()
				self.run(job, user, x_td, y_td, check_bar, start_index, end_index, prog)
			self.send_command(b'LDB\n')
		self.reset_start_btn()
	def reset_start_btn(self):
		self.start_jobs_btn.setStyleSheet('background-color: rgb(85, 255, 127)')
		self.start_jobs_btn.setText("START")
		self.start_jobs_btn.repaint()
	def stop_all(self):
		pass
	#####core.py  starts here

	def set_job_folder_fullpath(self, fp):
		"""Sets the job folder fullpath.
		Useful callback when core is run through the GUI.
		"""
		self.job_fullpath=fp
	def find_configuration_files(self, job):
		"""Looks inside self.job_fullpath for:
			*EDF.yaml
			*MDF.yaml
			*JOB.yaml
			*CCF.csv
			*MMF.csv
			*AMF.yaml
			<probecard>.yaml #treated as dummy for now

			Finds the files and assigns fullpaths.
		"""
			 
		# for each config file, add the job folder to the path or ask the user to provide one
		if self.mdf_fullpath:
			self.mdf_fullpath = os.path.join(self.job_folder,self.mdf_fullpath)
		else:    
			self.fe.get_specified_configuration_files(mdf=True)
			self.mdf_fullpath = self.fe.mdf

		if self.ccf_fullpath:
			self.ccf_fullpath = os.path.join(self.job_folder,self.ccf_fullpath)
		else:
			self.fe.get_specified_configuration_files(ccf=True)
			self.ccf_fullpath = self.fe.ccf

		if self.mmf_fullpath:    
			self.mmf_fullpath = os.path.join(self.job_folder,self.mmf_fullpath)
		else:    
			self.fe.get_specified_configuration_files(mmf=True)
			self.mmf_fullpath  = self.fe.mmf

		if self.edf_fullpath:# Note: edf is located in main config files folder
			self.edf_fullpath = os.path.join(get_jobs_folder(), self.edf_fullpath)
		else:
			self.fe.get_specified_configuration_files(edf=True)
			self.edf_fullpath = self.fe.edf

		if self.amf_fullpath:    
			self.amf_fullpath = os.path.join(self.job_folder,self.amf_fullpath)
		else:    
			self.fe.get_specified_configuration_files(amf=True)
			self.amf_fullpath  = self.fe.amf

		if self.probes_fullpath:# Note: probes are located on a different folder       
			self.probes_fullpath = os.path.join(get_probes_folder(), self.probes_fullpath)
		else:
			self.fe.get_specified_configuration_files(probes=True)
			self.probes_fullpath = self.fe.probes
	

		print ('\n\n\n\n\n\n===== Configuration files =====')
		print ('job file',self.job_fullpath)
		print ('mdf file',self.mdf_fullpath)
		print ('edf file',self.edf_fullpath)
		print ('ccf file',self.ccf_fullpath)
		print ('mmf file',self.mmf_fullpath)
		print ('amf file',self.amf_fullpath)
		print ('probecard file',self.probes_fullpath)
		# print ('probecard name', self.probename)
		# print ('\n\n\n\n\n\n')

		logger.info('===== Configuration files =====')
		logger.info('job file {}'.format(self.job_fullpath))
		logger.info('mdf file {}'.format(self.mdf_fullpath))
		logger.info('edf file {}'.format(self.edf_fullpath))
		logger.info('ccf file {}'.format(self.ccf_fullpath))
		logger.info('mmf file {}'.format(self.mmf_fullpath))
		logger.info('amf file {}'.format(self.amf_fullpath))
		logger.info('probecard  file {}'.format(self.probes_fullpath))        
		logger.info('===============================')
	def read_job(self):
		"""Reads the job file
		"""
		job                 = load_yaml_file(self.job_fullpath)
		self.batch          = job['batch_information']['name']
		self.wafer         = job['batch_information']['wafers'] #TODO: chagne into wafer instead of waferS
		self.meas_procedure = job['measurement_procedure']
	def read_ccf(self):
		"""Reads the ccf
		"""
		self.ccfr.read_csv(self.ccf_fullpath)
	def read_mmf(self):
		"""Reads the measurement matrix
		"""
		self.mmfr.read_csv(self.mmf_fullpath)
	def read_job_v2(self,job): # ABI: this function should replace read_job()
		""" Reads the JOB file and sets the general acquisition settings
		"""

		self.job_fullpath = job
		self.job_folder = os.path.dirname(self.job_fullpath)
				
		# reads JOB file and extract config files from it
		self.job = JOBReader.from_yaml_file(job_path=self.job_fullpath)

		# load config file path
		self.edf_fullpath = self.job.get_edf_path
		self.ccf_fullpath = self.job.get_ccf_path
		self.mmf_fullpath = self.job.get_mmf_path
		self.mdf_fullpath = self.job.get_mdf_path
		self.amf_fullpath = self.job.get_amf_path
		self.probes_fullpath = self.job.get_probecard_file_path

		# load sample ids
		self.batch = self.job.get_batch
		self.wafer = self.job.get_wafer
		self.customer = self.job.get_customer
		self.product = self.job.get_product

		# load acquisition and post-acquisition settings
		self.meas_procedure = self.job.get_meas_procedure
		self.save_output_on_file = self.job.get_acquistion_settings
		self.zip_output_files, self.quick_analysis = self.job.get_post_acquistion_settings

		logger.debug('Info from job file loaded')
	def generate_meas_plan(self,start_index, end_index ): 
		"""Reads config files (CCF, MMF, MDF, and probes) and generates the measurements plan"""
		self.mp = MeasPlan.from_files(self.ccf_fullpath,self.mmf_fullpath,self.mdf_fullpath,self.probes_fullpath)
		self.probename=self.mp.probes.get_probe_name()
		if self.job.get_sample_type=='bar': # select a sub-samples of cells from MMF/CCF
			self.first_cell, self.last_cell =   start_index, end_index
		else:
			self.first_cell, self.last_cell =   start_index, end_index
		# rescale all cell positions to the first cell one, and invert the obtained values
		self.mp.rescale_cell_positions_to_first_cell(first_cell=self.first_cell)
	def run(self,job, user, x_td, y_td, check_bar, start_index, end_index, prog):
		"""Runs the core
		"""
		self.init_process(job, user, x_td, y_td, check_bar, start_index, end_index, prog)
		self.start_alignment_process()
		self.match_coordinates()
		t,s=generate_session_ID()
		self.session_start_time=s.strip(t+'_')
		self.perform_measurement_loop()
		self.daq_successful = True
		
	def init_process(self,job, user, x_td, y_td, check_bar, start_index, end_index, prog):
		"""Initializes the process:
				Identifies the operator
				Identifies the wafers (in the future)
				Looks for the configuration files
				Reads the cell coord file
		"""
		self.identify(user)
		self.read_job_v2(job)
		self.find_configuration_files(job)
		self.generate_meas_plan(start_index, end_index)# ABI: new function
		self.init_equipment()
		self.loading.init_loading_process_(self.eq)
		self.start_loading_process()
		self.init_meas_handler()
	def start_loading_process(self):
		"""Load the sample
		"""
		#self.loading.load_sample()

		if self.eq.prober.get_ID() == 'Pegasus S200:LM,Lock':
			self.loading.close_door()
			self.loading.lock_door()
	def select_sample_v2(self):
		"""Asks the user to select the north-most and south-most cell of the
		sample.
		"""
		self.first_cell, self.last_cell = select_bar()
		self.mp.slice_cells_sample(first_cell=self.first_cell, last_cell=self.last_cell)
	def slice_cell_files(self):
		"""Slices the Measurement Matrix File and Cell Coordinate file based
		on input from the user.
		"""
		self.mmfr.df=self.mmfr.slice_dataframe_including_min_and_max(first_ = self.first_cell,
																 last_ = self.last_cell,
																on_column='Dies/Measurements')
	def start_alignment_process(self):
		"""Align the sample
		"""
		self.alignment.start_alignment_process_(self.eq,first_cell=self.first_cell)
		#print ('Initial xy:',self.alignment.x0,self.alignment.y0)
	def match_coordinates(self, x_td, y_td):
		"""Matches the wafer coordinates with the tool coordinates
		"""
		self.mp.match_cell_positions_to_probing_stage(x0=x_td, y0=y_td)
	def set_current_cell(self,cell):
		self.current_cell=cell
	def init_probemonitor(self, port):
		import serial
		self.probe_mon=serial.Serial(port)
	def probemonitor(self): #TODO: check if we can reduce 10 reads to 1
		res=[]
		for i in range(10):
			#self.probe_mon.write(b'0') #writing one bit initiates measurement #Commented by marcos  microcontroler is dead
			#res.append(str(self.probe_mon.readline())[2:][:-5]) #receive measured data
			pass
		res=','.join(str(e) for e in res)
		return res
	def logfile(self, data):
		timedate=time.strftime("%d-%m-%Y", time.gmtime())
		header='time,probecard,cellid,fcn,val0,val1,val2,val3,val4,val5,val6,val7,val8,val9\n' #es measurement is acquired 10 times, some noise observed in the past
		fname='d:/PRODUCTION/probes/monitor/probemonitor_{}.csv'.format(timedate)
		
		#write header if file does not exist. Should use a proper method with init wich solves this nicely.
		if not os.path.isfile(fname):
			with open(fname,'a') as f:
				f.write(header)

		try:
			with open(fname,'a') as f:
				loctime=time.strftime("%H.%M.%S", time.gmtime())
				f.write(loctime+","+data)
		except:
			pass
	def go_to_cell_v2(self, cl): # ABI: new simpler version
		"""
		Checks if x,y are different than current x, y coordinates.
		If they are different, it moves the prober to relative x,y.
		"""
		x, y = self.mp.get_cell_position(cell_name=cl)

		self.current_x, self.current_y = self.eq.prober.get_chuck_xy()
		print('\nCurrent xy:',self.current_x, self.current_y)

		## Is the prober there already?
		if (int(self.current_x), int(self.current_y)) != (int(x),int(y)):
			print('moving from x{} y{} to x{} y{}'.format(self.current_x,self.current_y,x,y))
			self.eq.prober.move_chuck_fine_down()
			# check edge sensor status after "Fine down" movement
			time.sleep(0.2)
			edge_sensor_open = self.eq.prober.get_edge_sensor_status()
			if(edge_sensor_open):
				message = "WARNING! CRITICAL ERROR!\nEdge sensor open when chuck is in 'Fine down' position\nThe script execution has been terminated"
				print(message)
				logger.critical(message)
				raise ProberError("EdgeSensorFineDown")                    
			#measure ES voltage
			#es_voltage=self.probemonitor() # commented by Marcos microcontroller is dead
			#self.es_checker(es_voltage) # commented by Marcos microcontroller is dead
			# print("{} ES_CDW={}".format(cell_id, es_voltage))
			
			#self.logfile(f"{self.probename},{cl},ES_CDW,{es_voltage}\n") # commented by Marcos microcontroller is dead
			self.eq.prober.go_to_xy(x,y)
	def perform_measurement_loop(self, progress_bar): # ABI: this function is aimed at replacing init_measurement_loop()
		"""This method is responsible for executing the measurement loop.
		
		The measurement loop can be either "die_wise" (i.e. all measurments are performed on one
		die, then the next die is measured) or "meas_wise" (i.e. one measurment is performed on 
		all dies, then the next measurement is performed)
		"""
		cnt = 0
		progress_bar = r'{}'.format(progress_bar)
		logger.info('Starting the measurement loop...')

		if self.meas_procedure == 'die_wise': # all measurements on one die in one go
			start_time = time.time()
			work_size = len(self.mp.get_cell_names)
			for cell in self.mp.get_cell_names:
				
				self.go_to_cell_v2(cl=cell)
				for ms in self.mp.get_meas_plan_for_cell(cell_name=cell):
					if ms == 'PICTURE':
						self.take_picture(picture_name='_'.join([self.wafer, self.batch, cell, ms])) 
					else:
						self.perform_touch_down(cell=cell)                         
						self.perform_measurement(ms=ms, cl=cell)
				cnt = cnt+1
				progress = round( 100*(1-(work_size-cnt)/work_size), 1)
		if self.meas_procedure == 'meas_wise': # each measurement on all dies, before passing to next measurement
			for ms in self.mp.planned_meas:
				work_size = len(self.mp.planned_meas)
				progress = round( 100*(1-(work_size-cnt)/work_size), 1)
				#for ms in tqdm(self.mp.planned_meas, bar_format='{l_bar}%s{bar:75}%s{r_bar}' % (Fore.YELLOW, Fore.RESET),desc='Measurement Progress'):

				#for cell in self.mp.get_cells_for_meas_plan(meas_name=ms):
				for cell in self.mp.get_cells_for_meas_plan(meas_name=ms):
					self.go_to_cell_v2(cl=cell)
					if ms == 'PICTURE':
					
						self.take_picture(picture_name='_'.join([self.wafer, self.batch, cell, ms])) 
					else:
						self.perform_touch_down(cell=cell)
						self.perform_measurement(ms=ms, cl=cell)
				cnt = cnt+1
	def take_picture(self, picture_name): # ABI: new function, dedicated to taking pictures with monitoring camera
		pass    
		'''
		print('taking picture...')
		#light on
		self.eq.prober.set_light(on=True)
		#takes some time to activate the light
		time.sleep(2) 
		#take picture
		self.eq.camera.read_single_frame()
		#save picture
		self.eq.camera.save_frame(name=picture_name+'.png', location=get_batch_data_folder(self.m.data_folder))
		#add file name to the file names list
		self.camera_picture_file_list.append(os.path.join(get_batch_data_folder(self.m.data_folder),picture_name+'.png'))
		#light off
		self.eq.prober.set_light(on=False)
		#takes some time for the light to turn off
		time.sleep(1)
		'''
	def perform_touch_down(self, cell): # ABI: new function, dedicated to perform the probecard touch down once the cell is in position
		edge_sensor_open = self.eq.prober.get_edge_sensor_status()
		if(not edge_sensor_open and not self.eq.prober.is_chuck_in_fineup()): # this line prevents to perform a "fine up" if chuck is already in fine up position
			self.eq.prober.move_chuck_fine_up()
			# measure chuck z-position
			z=self.eq.prober.get_chuck_z()
			#get edge sensor status
			edge_sensor_open = self.eq.prober.get_edge_sensor_status()
			logger.info('Cell {} successfully probed: {}'.format(cell, edge_sensor_open))
			td_date, td_time = [datetime.datetime.now().strftime('%Y.%m.%d'), datetime.datetime.now().strftime('%H.%M.%S')]
			self.touch_down_recorder.append([cell, z, td_date, td_time, edge_sensor_open])
			
			#probe monitor 
			#es_voltage=self.probemonitor() #Commented by marcos  microcontroler is dead
			# print("{} ES_CUP={}".format(cell_id,es_voltage))
			# self.logfile("{},ES_CUP,{}\n".format(cell,es_voltage))
			#self.logfile(f"{self.probename},{cell},ES_CUP,{es_voltage}\n")
			
			zup=self.eq.prober.get_chuck_z()
			# print("{},Z_at_CUP,{}\n".format(cell_id,zup))
			
			# self.logfile("{},Z_at_CUP,{}\n".format(cell,zup))
			self.logfile(f"{self.probename},{cell},Z_at_CUP,{zup}\n")
	def perform_measurement(self, ms, cl):
		"""Sets the measurement plan.
		   Passes identifiers for the measurement file to the MeasurementHandler.
		   Checks the temperature.
		   Starts the measurement.
		"""
		self.m.tool_id            = self.tool_id
		self.m.session_id         = self.session_id
		self.m.operator           = self.operator
		self.m.session_start_time = self.session_start_time

		self.m.current_batch      = self.batch
		self.m.current_wafer      = self.wafer
		self.m.current_customer   = self.customer
		self.m.current_product    = self.product
		self.m.current_cell       = cl
		self.m.pl_value           = self.mp.get_physical_parameter('PL_wavelength') #PL was not broadcasted
		# Set the measurement plan
		self.m.set_plan(meas_plan = ms) # Replaced with self.m.get_plans_from_mdf()
		self.m.plan = ms
		self.m.plan_settings = self.mp.get_settings_for_measurement(meas_name=ms) # broadcast the plan setting dict to measurement_handler
		
		
		print('pre-set T_set')
		T_set = self.m.get_plan_setting(setting='T_set')
		print(' perform_measurement method sets temperature = to:', T_set)
		self.eq.tec._set(T_set = T_set, T_win=0.5)
		print ('tec status:', self.eq.tec.is_stable())
		while not self.eq.tec.is_in_T_win(T_set = T_set, T_win=0.5):
			print('tec status: T={} not in Twin {}<->{}'.format(self.eq.tec.get_temperature(),T_set-0.5,T_set+0.5))
			time.sleep(1)
		while not self.eq.tec.is_stable():
			time.sleep(1)
			print('tec status: Not stable, T={}'.format(self.eq.tec.get_temperature()))
			

		# Measure
		self.m.start_measurement()
	def identify(self, user):
		'''Identify the operator
		'''
		self.operator         =    user
	def init_equipment(self):
		"""Initializes the equipment
		"""
		self.eq=Equipment(fullpath=self.edf_fullpath)
		self.eq.import_classes() # AB: this line is probably redoundant
		self.eq.connect_()
		self.eq.get_ID_()
	def init_meas_handler(self):
		"""Initializes the measurement handler.
		"""
		self.m=measurement_handler.MeasurementHandler(equipment=self.eq)
	def get_mdf_fullpath(self):
		"""Returns the mdf fullpath"""
		return self.mdf_fullpath
	def get_ccf_fullpath(self):
		"""Returns the ccf fullpath"""
		return self.ccf_fullpath
	def get_edf_fullpath(self):
		""" Returns the edf fullpath"""
		return self.ccf_fullpath
	def performance_monitor(self, cell, start, end):

		
		with open('performance_monitor.txt','a') as f:
			f.write('\n Cell: {}, Start: {}, Iter duration: {}'.format(cell, start,end-start))
			f.close()
	def compress_output_files(self,zipping_files=None): # ABI: function added by me
		self._zipped_output_files = []
		if(zipping_files==None):
			zipping_files = self.zip_output_files
		if zipping_files:
			folders = list(sorted(set([os.path.split(f)[0] for f in self.m.written_files_list])))
			for folder in folders: # maybe it is not needed -> one folder only per run
				# ABI: I think I have to change the way the zip file name is given -> get it from "folder"
				zip_file_name = ("_").join([self.customer,self.batch,self.wafer,"SessionStart",self.session_start_time+".zip"])
				zip_file_name = zip_file_name.replace(':','-') #removing illegal ":" character                
				with ZipFile(os.path.join(folder,zip_file_name), 'w') as zipObj:
					# Saving config files inside the zip file
					config_files = [self.edf_fullpath, self.mdf_fullpath, self.job_fullpath, self.ccf_fullpath, self.mmf_fullpath, self.amf_fullpath, self.probes_fullpath, self.git_commit_file_name]
					for c_file in config_files:
						fname = os.path.join('config_files',os.path.split(c_file)[1]) # name of zipped file inside the zip folder stripped of the path location
						zipObj.write(c_file,arcname=fname)
					# Iterate over all the output files in directory
					for filename in self.m.written_files_list:
						if folder in filename:
							fname = os.path.join('rawdata',os.path.split(filename)[1]) # name of zipped file inside the zip folder stripped of the path location
							# Add file to zip
							zipObj.write(filename,arcname=fname)
							# deleting the zipped file
							os.remove(filename)
					# Iterate over all the picture files
					for pic_name in self.camera_picture_file_list:
						if folder in filename:
							fname = os.path.join('pictures',os.path.split(pic_name)[1]) # name of zipped file inside the zip folder stripped of the path location
							# Add file to zip
							zipObj.write(pic_name,arcname=fname)
							# deleting the zipped file
							os.remove(pic_name)                                            
					# Iterate over quick analysis output files
					for qa_file in self.quick_analysis_file_list:
						if os.path.split(folder)[1] in qa_file:
							fname = os.path.join('quick_analysis',os.path.split(qa_file)[1]) # name of zipped file inside the zip folder stripped of the path location
							# Add file to zip
							zipObj.write(qa_file,arcname=fname)
							# deleting the zipped file
							os.remove(qa_file)                                            
					# append zip file name to the list
					self._zipped_output_files.append(os.path.join(folder,zip_file_name))

			print("All output files zipped and removed!")
	def backup_output_files(self):
		cmd_success = []
		for output_file in self._zipped_output_files:
			# strip <data folder path> from the file path
			relative_filename = os.path.relpath(output_file, get_data_folder())
			relative_path = os.path.split(relative_filename)[0]
			# define the filename at the destination location
			destination_filename = os.path.join(get_backup_folder(), relative_filename)
			# check if the destination folder on backup location exists, if not creates it
			if not os.path.exists(os.path.join(get_backup_folder(), relative_path)):
				os.makedirs(os.path.join(get_backup_folder(), relative_path))
			# copy file to the back up location
			cmd_success.append([os.system((" ").join(['copy', '"'+output_file+'"', '"'+destination_filename+'"'])), output_file])
		self.end_time= time.time()
		self.total_time = round((self.end_time-self.start_time)/60,2)
		print('##################################')
		print(self.total_time,'Minutes')
		print('##################################')

		failed_backup = [filename for failure, filename in cmd_success if failure==1]
		if len(failed_backup)==0 and len(self._zipped_output_files)>0:
			print("All output zip files have been copied at backup location!")
		else:
			for failed_file in failed_backup:
				print("Warning! File {} have NOT been copied at backup location!".format(failed_file))
	def release_equipment(self):
		self.eq.release_()
	def end(self):
		"""Ends the core.
		"""
		self.eq.tec._set(T_set = 20, T_win=0.5)
		self.loading.unload_sample()
		self.release_equipment()
		
		#send telegram message it is done

		msg = "{}: Batch {} Wafer {} bar {} to {} finished".format(self.tool_id,self.batch,self.wafer,self.first_cell,self.last_cell)
		
		operator_telegram={
			'EHN':'728365163',
			'ABI':'989990208',
			'JVP':'1363687370',
			'JNP':'5040360753',
			'AJI':'5170533169',
			'EAN':'5608377269',
			'MSE':'6946485264' 
			
			}
		
		try:
			telegram_id = operator_telegram.get(self.operator.upper())
			telegram.bot_sendtext(msg,telegram_id)
			
		except:
			print('No message sent, operator ID unknown')
			pass
		
		logging.shutdown() # release the log file

		if(self.save_output_on_file):
			sys.stdout = self.terminal_stdout # going back to printing to terminal
			self.f_stdout.close()

		print("\nMeasurement run finished!\n")
		
		print("Number of attempted 'touch-down': {}".format(len(self.touch_down_recorder)))
		print("Number of successful 'touch-down': {}".format(sum([1 for cell, _, _, _, td_boolean in self.touch_down_recorder if td_boolean == True])))
		print("Number of unsuccessful 'touch-down': {}\n".format(sum([1 for cell, _, _, _, td_boolean in self.touch_down_recorder if td_boolean == False])))
	def post_acquisition_operations(self):
		""" Executes post-acquisition operations on output files
		"""
		# performing quick analysis
		if(self.quick_analysis):
			qa = QuickAnalysis()
			qa.run(type_of_analysis=self.quick_analysis, input_files=self.m.written_files_list) # ABI: for the moment it works for Probecard check only
			self.quick_analysis_file_list = qa.list_quick_analyzed_files
		# compress output files in a zip file
		self.compress_output_files() # set to True for zipping output files, do not enter any value for relying on Job file
		# make a backup copy of the compressed zip file
		self.backup_output_files()

if __name__ == '__main__': # only executes the below code if it python has run it as the main
	app = QtWidgets.QApplication(sys.argv)
	print('Exiting job execution')
	window = Ui()
	app.exec_()