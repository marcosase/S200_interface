#!/usr/bin/python3.8
#coding:utf-8 -*-
# Author: Marcos Eleoterio
# Email: marcos.dasilva.eleoterio@smartphotonics.nl
import pandas as pd
import time
from datetime import datetime
from time import strftime, localtime
import sys, os
import numpy as np
import pyvisa as visa
from PyQt5 import QtGui, QtWidgets, uic, QtCore
from PyQt5.QtWidgets import QTableWidgetItem, QFileDialog, QApplication, QMessageBox
from PyQt5.QtGui import QFont 
from PyQt5.QtCore import QThread, QProcess, QTimer, QObject, pyqtSignal
from zipfile import ZipFile
import pyqtgraph as pg
import serial
from functools import partial
import config
import re
import yaml
import glob
import signal
import subprocess
from subprocess import call
sys.path.insert(1, 'C:/AMS')

try:
	from smu.keithley2602 import keithley2602B
	import pyOSA
	from tec import tec
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
	import openepda
	openEPDA_version = openepda.__version__
	from collections import OrderedDict
	import mes_check as MesCom
	# automated data extraction messageque support
	#from utils.smg import initiate_data_extraction #Commented because it was issuing importing error  MSE
	logger=logging.getLogger('test.AmsCore')
	start_time = time.time()
	ktl= keithley2602B()
except Exception as err:
	print(err)

class Ui(QtWidgets.QMainWindow):
    class Worker(QObject):
        finished = pyqtSignal(str)
        error = pyqtSignal(str)  # Signal emitted when an error occurs
        update_button = pyqtSignal(str, str, str)  # Signal for button updates: (stylesheet, text, border)
	
        def __init__(self, job_method):
		"""Initializes the Worker with a job method to run in a thread."""
		super().__init__()
		self.job_method = job_method
		self.stop_requested = False

        def run(self):
		"""Executes the job method and emits the finished signal when done."""
		try:
			if not self.stop_requested:
				self.job_method()
			self.finished.emit("Jobs finished")
		except Exception as e:
			error_msg = f"Error during job execution: {str(e)}"
			print(error_msg)
			import traceback
			traceback.print_exc()
			self.error.emit(error_msg)

        def stop(self):
		"""Sets the stop_requested flag to True to request stopping the job."""
		self.stop_requested = True
    def __init__(self):
		"""Initializes the main UI window and sets up all widgets, connections, and variables."""
		pg.setConfigOption('background', 'w') #before loading widget
		pg.setConfigOption('foreground', 'k')
		super(Ui, self).__init__() # Call the inherited classes __init__ method
		uic.loadUi('BT_interface.ui', self) # Load the .ui file
		###definitions from core.py
		pg.setConfigOption('background', 'w') #before loading widget
		pg.setConfigOption('foreground', 'k')
		self.q_timer = QtCore.QTimer() #qtimer def
		self.start_time = time.time()
		self.alignment = AlignSample()
		self.loading = LoadSample()
		self.worker = None  # Store worker reference for signal connection
		self.thread = None  # Store thread reference
		self.job_queue = []  # Queue to store jobs to be processed
		self.stop_requested = False  # Flag to stop job processing
		try:
			self.tool_id, self.session_id = generate_session_ID()
		except:
			self.tool_id, self.session_id = 'tool_id', 'session_id'
			print('Session ID generation failed!')
			pass
		
		self.camera_picture_file_list = [] # list of file names of taken pictures
		self.quick_analysis_file_list = [] # list of output file names from quick analysis routine
		self._cell_probing_counter = 0 # counter of probing of the same cell
		self.touch_down_recorder = [] # list of successful/unsuccessful wafer "touch-down"
		self.daq_successful = False # boolean stating the acquistion has been properly performed
		self.terminal_stdout = sys.stdout
		#################
		pg.setConfigOption('background', 'w') #before loading widget
		pg.setConfigOption('foreground', 'k')
		
		###Variable
		self.job_folder_path1 = ''
		self.job_folder_path2 = ''
		#Test for new touchdown methods
		self.btn_touch1.clicked.connect(partial(self.touch_bar, 1))
		self.btn_touch2.clicked.connect(partial(self.touch_bar, 2))
		self.btn_touch3.clicked.connect(partial(self.touch_bar, 3))
		self.btn_touch4.clicked.connect(partial(self.touch_bar, 4))
		self.btn_touch5.clicked.connect(partial(self.touch_bar, 5))
		self.btn_touch6.clicked.connect(partial(self.touch_bar, 6))
		self.btn_touch7.clicked.connect(partial(self.touch_bar, 7))
		
		#Method to select job files for the wafers and show it in the dialog
		self.btn_job.clicked.connect(self.select_job)
		
		self.start_jobs_btn.clicked.connect(self.start_jobs) ###Start the jobs
		self.btn_stop.clicked.connect(self.stop_all) ###Stop the jobs
		#self.start_jobs_btn.clicked.connect(self.start_jobs_in_thread)
		
		self.unload_btn.clicked.connect(self.move_unload)
		self.probe_btn.clicked.connect(self.go_probe)
		self.gup_btn.clicked.connect(self.gross_up)
		self.gdn_btn.clicked.connect(self.gross_down)
		self.change_pos_btn.clicked.connect(self.change_pos)
		self.fineup_btn.clicked.connect(self.fine_up)
		self.finedown_btn.clicked.connect(self.fine_down)
		self.btn_vac_on.clicked.connect(self.vac_on)
		self.btn_vac_off.clicked.connect(self.vac_off)

		##
		self.btn_go_td1.clicked.connect(self.go_td1)
		self.btn_go_td2.clicked.connect(self.go_td2)
		self.btn_go_td3.clicked.connect(self.go_td3)
		self.btn_go_td4.clicked.connect(self.go_td4)
		self.btn_go_td5.clicked.connect(self.go_td5)
		self.btn_go_td6.clicked.connect(self.go_td6)
		self.btn_go_td7.clicked.connect(self.go_td7)
		##
		self.jobs_combo_box.currentTextChanged.connect(self.update_info)
		###LIV/SPC Gui
		self.tec_btn.clicked.connect(self.get_temp)
		self.osa_acq_btn.clicked.connect(self.acq_osa)
		self.liv_gen_btn.clicked.connect(self.gen_liv_config)
		self.btn_mes_check.clicked.connect( lambda:self.run_mes_check(True))
		#####
		#self.die_btn_list.clicked.connect(self.get_liv_list)
		self.die_btn_job.clicked.connect(self.select_die_config)
		self.die_jobs_combo_box.currentTextChanged.connect(self.die_update_info)
		self.die_loaded_cell.currentTextChanged.connect(self.update_load_cells)
		self.mes_search_job.clicked.connect(self.search_jobs)
		self.gen_bar_job.clicked.connect(self.gen_bars_job)
		self.bars_job_refresh.clicked.connect(self.refresh_bars_combo_box)
		self.show() # Show the GUI
		self.bar.setValue(0)
		self.write_values()
		self.showMaximized()
		#######Die measurement stuff
		

		################Keithley controls
		self.ktl_meas_btn.clicked.connect(self.ktl_meas)
		self.ktl_on_btn.clicked.connect(self.ktl_on)
		self.ktl_off_btn.clicked.connect(self.ktl_off)   
    def plot_win(self, x, y1, y2 = None, cell = None):
		"""Plots measurement data on the plot window. Handles both LIV and spectrum plots."""
		print('Plotting data')
		print('#############')
		#print(x,y1,y2,cell)
		#print('###############')
		
		t1 = (0,0,255)
		t2 = (255,0,0)
		tfill = (0,0,0)
		
		pen_t1 = pg.mkPen(color=(0, 0, 255), width=3, style=QtCore.Qt.SolidLine)
		pen_t2 = pg.mkPen(color=(255, 0, 0), width=3, style=QtCore.Qt.SolidLine)
		
		color1 = '#%02x%02x%02x' % t1
		color2 = '#%02x%02x%02x' % t2

		x_label = 'Current(A)'
		y_label = 'voltage(V)'
		y2_label = 'Power(W)'
		title = 'LIV'
		
		self.p1 = self.plotter.plotItem
		self.p1.setLabels(left = y_label)
		
		#Create a new ViewBox
		self.p2 = pg.ViewBox()
		self.p1.showAxis('right')
		self.p1.scene().addItem(self.p2)
		self.p1.getAxis('right').linkToView(self.p2)
		self.p2.setXLink(self.p1)
		self.p1.getAxis('left').setLabel(y_label, color=color1)
		self.p1.getAxis('right').setLabel(y2_label, color=color2)
		self.p1.getAxis('bottom').setLabel(x_label)        
		self.p1.vb.sigResized.connect(self.updateViews)
		self.updateViews()
		self.set_graph(title, x_label, y_label)
		self.clear_plot()
	
		if y2 != None:
			#ic(x, y1, y2)
			x_label = 'Current(A)'
			y_label = 'voltage(V)'
			y2_label = 'Power(W)'
			title = 'LIV'
			self.p1 = self.plotter.plotItem
			self.p1.setLabels(left = y_label)
			#Create a new ViewBox
			self.p2 = pg.ViewBox()
			self.p1.showAxis('right')
			self.p1.scene().addItem(self.p2)
			self.p1.getAxis('right').linkToView(self.p2)
			self.p2.setXLink(self.p1)
			self.p1.getAxis('left').setLabel(y_label, color = color1)
			self.p1.getAxis('right').setLabel(y2_label, color = color2)
			self.p1.getAxis('bottom').setLabel(x_label)        
			self.p1.vb.sigResized.connect(self.updateViews)
			self.updateViews()
			self.set_graph(title, x_label, y_label)
			self.clear_plot()
			
			volt = np.array(y1)
			pcurr = np.array(x)
			power = np.array(y2)
			self.plotter.clear()
			try:
				
				mask = volt <= 5
				volt = volt[mask]
				#power = power[mask]
				#pcurr = pcurr[mask]
				
				y_min = np.min(volt)
				y_max = np.max(volt)
				self.p1.vb.disableAutoRange(axis = pg.ViewBox.YAxis)
				self.p1.vb.setYRange(y_min, y_max)
				
				y2_min = np.min(power)
				y2_max = np.max(power)
				self.p2.setYRange(y2_min, y2_max)
				self.p2.disableAutoRange(axis = pg.ViewBox.YAxis)

				x_min = np.min(p_curr)
				x_max = np.max(p_curr)
				self.p1.vb.setXRange(x_min, x_max)
				
				self.p1.vb.disableAutoRange(axis = pg.ViewBox.YAxis)
				print()
				self.p1.plot(pcurr, volt, pen = pen_t1, name = self.m.current_cell)
				self.plot2 = pg.PlotCurveItem(pcurr, power, pen = pen_t2, name = cell)
				self.p2.addItem(self.plot2)
				pg.QtGui.QGuiApplication.processEvents()
			except Exception as err:
				print(err)
				pass
		else:
			x_label = 'Wavelength(nm)'
			y_label = 'Power (W)'
			title = 'Spectrum'
			self.p1 = self.plotter.plotItem
			self.p1.setLabels(left = y_label)
			self.p1 = self.plotter.plotItem
			self.p1.setLabels(left = y_label)
			val_x, val_y = x, y1
			x_min = np.min(val_x)
			x_max = np.max(val_x)
			self.p1.vb.setXRange(x_min, x_max)
			self.p1.vb.disableAutoRange(axis = pg.ViewBox.YAxis)
			y_min = np.min(val_y)
			y_max = np.max(val_y)
			self.p1.vb.setYRange(y_min, y_max)
			self.p1.vb.disableAutoRange(axis = pg.ViewBox.YAxis)
			self.p1.getAxis('bottom').setLabel('Wavelength(nm)')
			self.p1.getAxis('left').setLabel('Power(W)', color = color1)
			self.p1.vb.disableAutoRange(axis = pg.ViewBox.YAxis)
			self.p1.plot(val_x, val_y, pen = pen_t1, name = cell)
			pg.QtGui.QGuiApplication.processEvents()
    def ktl_meas(self):
		"""Performs a Keithley measurement and updates the voltage display in the UI."""
		address="GPIB0::25::INSTR"
		rm=visa.ResourceManager()
		ktl = rm.open_resource(address)
		current = float(self.ktl_curr.value())/1000
		ktl.write('*RST')
		
		ktl.write("SOUR1:VOLT:PROT 5")
		ktl.write(":SOUR1:FUNC DC")
		ktl.write(f":SOUR1:CURR {current}")
		
		ktl.write(':OUTP ON')
		value = ktl.query(":READ?")
		ktl.write(':OUTP OFF')
		volt = float(value.split(',')[0])
		self.volt_meas.setText(str(volt))
    def ktl_on(self):
		"""Turns on the Keithley source with the specified current."""
		address="GPIB0::27::INSTR"
		rm=visa.ResourceManager()
		ktl = rm.open_resource(address)
		current = float(self.ktl_curr.value())/1000

		ktl.write("smub.source.func = smub.OUTPUT_DCAMPS")
		ktl.write("smub.source.leveli = {}".format(current))
		ktl.write("smub.source.output = smub.OUTPUT_ON")
		
		#ktl.write('*RST')
		#ktl.write("SOUR1:VOLT:PROT 5")
		#ktl.write(":SOUR1:FUNC DC")
		#ktl.write(f":SOUR1:CURR {current}")
		#ktl.write(':OUTP ON')
    def ktl_off(self):
		"""Turns off the Keithley source output."""
		address="GPIB0::27::INSTR"
		rm=visa.ResourceManager()
		ktl = rm.open_resource(address)
		#ktl.write(':OUTP OFF')
		ktl.write("smub.source.output = smub.OUTPUT_OFF")
		rm.close()

############OSA methods
    def acq_osa(self):
		"""Acquires a spectrum from the OSA and plots the result."""
		Spectrum_settings = { # Settings for running Spectral measurements
			"resolution": 'high',  # 0 = low, 1 = high
			"sensitivity": 'high',  # 0 = low, 1 = medium low, 2 = medium high, 3 = high
			"spectrum_window": 100 # nm, width of wavelength range for spectral measurements
			} 
		print('Initializing OSA')
		try:
			o = pyOSA.initialize()
			resolution = Spectrum_settings["resolution"]
			sensitivity = Spectrum_settings["sensitivity"]
			o.setup(resolution=resolution, sensitivity=sensitivity, autogain=True) 
			print('Starting acquisition')
			time_before = time.time()
			acquisitions = o.acquire(number_of_acquisitions=1)
			print('Measurement ready')
			print(time.time()-time_before)
			acquisition = acquisitions[-1]
			spectrum = acquisition["spectrum"]
			wavelength = spectrum.get_x()
			power = spectrum.get_y()
			peak = spectrum.y_max
			peak_index = power.index(peak)
			self.plot_win(wavelength, power)
			try:
				o.close()
			except Exception as err:
				print(err)
				pass
			return wavelength,power, peak_index
		except Exception as error:
			print("Initialization failed ", error)
			return [],[],[]

############Moving/controlling the probe
    def rel_mov(self, x_inc, y_inc):
		"""Moves the prober stage by the specified x and y increments."""
		xy = self.send_command(b'PSXY\n')
		x = float(re.findall(r"-?\d+", xy)[-2]) + x_inc
		y = float(re.findall(r"-?\d+", xy)[-1]) + y_inc
		command = f'GTXY {x},{y}\n'.encode() # go to the next  laser
		self.send_command(command)
    def gross_up(self):
		'''Method to do the gross up'''
		self.send_command(b'GUP\n')
    def gross_down(self):
		'''Method to do the gross down'''
		self.send_command(b'GDW\n')
    def move_unload(self):
		"""Moves the prober to the unload position."""
		self.send_command(b'LDL\n')
		print('Moving to load position!')
		return
    def go_probe(self):
		"""Moves the prober to the probe position."""
		self.send_command(b'LDC 0\n')
		print('Moving to probe position!')
		return
    def change_pos(self):
		"""Moves the prober to the change position."""
		self.send_command(b'LDS\n')
		print('Moving to change position!')
		return
    def fine_up(self):
		'''Method to do the fine up'''
		self.send_command(b'CUP\n')
    def fine_down(self):
		'''Method to do the fine down'''
		self.send_command(b'CDW\n')
    def vac_on(self):
		'''Method to turn on the vacuum'''
		self.send_command(b'VAC CV,1\n')
	    def vac_off(self):
		'''Method to turn off the vacuum'''
		self.send_command(b'VAC CV,0\n')
    def check_idn(self):
		"""Checks the prober's identity by sending the GID command."""
		value =  self.send_command(b'GID\n')
		if value != '':
			return True
		else:
			return False

############Updating GUI
    def save_value(self):
		"""Saves all current values from the interface."""
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
			self.table_bar6.setItem(0, 1, QTableWidgetItem(str( int(df.X6[0]) )))
			self.table_bar6.setItem(0, 1, QTableWidgetItem(str( int(df.Y6[0]) )))
			self.table_bar7.setItem(0, 1, QTableWidgetItem(str( int(df.X7[0]) )))
			self.table_bar7.setItem(0, 1, QTableWidgetItem(str( int(df.Y7[0]) )))
			
			
			
			self.line_start1.setText(str(df.start_index1[0]))
			self.line_start2.setText(str(df.start_index2[0]))
			self.line_start3.setText(str(df.start_index3[0]))
			self.line_start4.setText(str(df.start_index4[0]))
			self.line_start5.setText(str(df.start_index5[0]))
			self.line_start6.setText(str(df.start_index6[0]))
			self.line_start7.setText(str(df.start_index7[0]))
			
			
			
			self.line_end1.setText( str(df.end_index1[0]))
			self.line_end2.setText( str(df.end_index2[0]))
			self.line_end3.setText( str(df.end_index3[0]))
			self.line_end4.setText( str(df.end_index4[0]))
			self.line_end5.setText( str(df.end_index5[0]))
			self.line_end6.setText( str(df.end_index6[0]))
			self.line_end7.setText( str(df.end_index7[0]))
			
			#Set job files
			self.update_info(str(df.job[0]))
		except Exception as error:
			print(error)
			print('Write to csv  backup failed!!!')
			pass
    def is_connected(self):
		"""Checks if the prober is connected by sending a GID command."""
		value = self.send_command(b'GID\n')
		if value =='':
			return False
		else:
			return True
    def ser_connect(self):
		"""Establishes and returns a serial connection to the prober."""
		try:
			self.ser = serial.Serial(port = 'COM5', baudrate = 38400, parity = serial.PARITY_EVEN, bytesize = serial.SEVENBITS, stopbits = serial.STOPBITS_TWO, timeout = 0.2)
			return self.ser
		except ValueError:
			self.ser.close()
			print(ValueError)
		return self.ser
    def wait_ser(self):
		"""Waits until the prober responds to a GID command, indicating readiness."""
		
		while True:
			button = QMessageBox.question(
			self,
			"Prober busy dialog",
			"Is positioning finished?",
			buttons=QMessageBox.Yes
			)
			#button.setStyleSheet("background-color: rgb(0, 0, 0);")
			if button == QMessageBox.Yes:
				time.sleep(1)
				if not(self.check_idn()): 
					button = QMessageBox.question(
					self,
					"Prober busy dialog",
					"Is positioning finished?",
					buttons=QMessageBox.Yes
					)
				else :
					break
    def send_command(self, command):
		"""Sends a command to the prober via serial and returns the response."""
		ser = self.ser_connect()
		ser.flush()
		ser.write(command)
		resp = ser.readall().decode()
		ser.close()
		return resp
    def file_save(self, val):
		"""Saves the provided values to a CSV backup file."""
		dic = {	'X1':[val[0]],'Y1':[val[7]],
		'X2':[val[1]],'Y2':[val[8]],
		'X3':[val[2]],'Y3':[val[9]],
		'X4':[val[3]],'Y4':[val[10]],
		'X5':[val[4]],'Y5':[val[11]],
		'X6':[val[5]],'Y6':[val[12]],
		'X7':[val[6]],'Y7':[val[13]],
		
		
		'job':[val[14]],
		'start_index1':[val[15]],'end_index1':[val[22]],
		'start_index2':[val[16]],'end_index2':[val[23]],
		'start_index3':[val[17]],'end_index3':[val[24]],
		'start_index4':[val[18]],'end_index4':[val[25]],
		'start_index5':[val[19]],'end_index5':[val[26]],
		'start_index6':[val[20]],'end_index6':[val[27]],
		'start_index7':[val[21]],'end_index7':[val[28]],
		'Z':[val[29]]
		}
		df = pd.DataFrame(dic)
		df.to_csv('backup_values.csv')
    def collect(self):
		"""Collects X/Y touchdown, job file, start/end indices, and Z values from the interface."""
		x_td_arr      = [self.table_bar1.item(0, 0).text(),
					self.table_bar2.item(0, 0).text(),
					self.table_bar3.item(0, 0).text(),
					self.table_bar4.item(0, 0).text(),
					self.table_bar5.item(0, 0).text(),
					self.table_bar6.item(0, 0).text(),
					self.table_bar7.item(0, 0).text(),]
					
		y_td_arr      = [self.table_bar1.item(0, 1).text(),
					self.table_bar2.item(0, 1).text(),
					self.table_bar3.item(0, 1).text(),
					self.table_bar4.item(0, 1).text(),
					self.table_bar5.item(0, 1).text(),
					self.table_bar6.item(0, 1).text(),
					self.table_bar7.item(0, 1).text(),]
					
		#Job file names
		job_file_arr   = [self.job_id.text()]
		
		start_index_arr = [self.line_start1.text(),
					self.line_start2.text(),
					self.line_start3.text(),
					self.line_start4.text(),
					self.line_start5.text(),
					self.line_start6.text(),
					self.line_start7.text(),]
		end_index_arr = [self.line_end1.text(),
					self.line_end2.text(),
					self.line_end3.text(),
					self.line_end4.text(),
					self.line_end5.text(),
					self.line_end6.text(),
					self.line_end7.text(),]
		try:
			z = self.z_touchdown
		except:
			z = z_touch = pd.read_csv('backup_values.csv').Z[0]

		val_array = [*x_td_arr, *y_td_arr, job_file_arr[0], *start_index_arr, *end_index_arr, z]
		return val_array

#############Die LIV measurement methods
    def select_die_config(self):
			"""Selects the die measurement configuration file and updates the interface."""
			job_root='C:/Users/HP/Smart Photonics/Engineering - Test & Measurement/Internal Projects/Job generation/'
			self.die_job_folder_path = QFileDialog.getExistingDirectory(self,("Open Batch Folder"), job_root)
			self.die_jobs_combo_box.clear()
			#Fill the first combo box with Jobs available
			job_folder_selection = glob.glob(self.die_job_folder_path+'/*ManualLIV_JOB.yaml')
			self.update_combo_box(self.die_jobs_combo_box, job_folder_selection)
			
			job_folder_selection = glob.glob(self.die_job_folder_path+'/*.csv')
			self.update_combo_box(self.die_list_combo_box, job_folder_selection)
    def die_update_info(self):
			"""Updates the die measurement information when any changes occurs with the dropdow based on the selected configuration file."""
			#Get info from the selected .yaml job file
			#Open the file and opens as a dictionary
			job_file_path=self.die_jobs_combo_box.currentText()
			cell_list=self.die_list_combo_box.currentText()
			if job_file_path:
				with open(job_file_path, 'r') as f:
					job_dict = yaml.safe_load(f)
					f.close()
			else: 
				job_dict = {}
			#Get parameters from the job dictionary
			customer_id   = job_dict.get("batch_information").get('customer')
			lot_id        = job_dict.get("batch_information").get("lot")
			product_id    = job_dict.get("batch_information").get("product")
			wafer_id      = job_dict.get("batch_information").get("wafer")
			temp_set      = job_dict.get("acquisition settings").get("T_set")
			temp_set      = " ".join(str(x) for x in temp_set)
			liv           = job_dict.get("acquisition settings").get("LIV")
			spectrum      = job_dict.get("acquisition settings").get("Spectrum")
			i_soa         = job_dict.get("acquisition settings").get("Spectrum I_SOA")
			cell_type     = job_dict.get("acquisition settings").get("cell_type")
			cell_ids      = pd.read_csv(cell_list)
			pl            = job_dict.get("acquisition settings").get("PL")
			amf           = job_dict.get("acquisition settings").get("amf")
			combi_mode    = job_dict.get("acquisition settings").get("combi_mode")
			cells_loaded  = self.die_loaded_cell.currentText()
			
			#Update the interface with the job parameters
			self.die_cust_id.setText(str(customer_id))
			self.die_batch_id.setText(str(lot_id))
			self.die_wafer_id.setText(str(wafer_id))
			self.die_prod_id.setText(str(product_id))
			self.die_pl.setText(str(pl))
			self.die_temp.setText(temp_set)
			self.liv_cells_loaded.setText(cell_ids[0:cells_loaded])
    def update_load_cells(self):
		cell_list     =self.die_list_combo_box.currentText()
		cell_ids      = pd.read_csv(cell_list).values
		cells_loaded  = self.die_loaded_cell.currentText()
		self.liv_cells_loaded.setText(cell_ids[0:cells_loaded])
    def search_jobs(self):
		try:
			work_order,prod_id,lot_id = self.run_mes_check(False)
			print(work_order,prod_id,lot_id)
			#folder_path = 'C:/Users/HP/Smart Photonics/Engineering - Test & Measurement/Internal Projects/Job generation/'+work_order+'/'+prod_id+'/'+lot_id+'/'+'TM0002'
			folder_path = 'C:/Users/MarcosDaSilvaEleoter/OneDrive - Smart Photonics/Test & Measurement/Internal Projects/Job generation/'+work_order+'/'+prod_id+'/'+lot_id+'/'+'TM0002'
			print(folder_path)
			job_folder_selection = glob.glob(folder_path+'/*_JOB.yaml')
			self.update_combo_box(self.die_jobs_combo_box, job_folder_selection)
			
			job_folder_selection = glob.glob(folder_path+'/*.csv')
			self.update_combo_box(self.die_list_combo_box, job_folder_selection)
		except Exception as err:
			print(err)
    def die_start(self):
		"""Starts die measurements. (Currently not implemented)"""
		job_file = self.die_jobs_combo_box.currentText()
		cell_file = self.die_list_combo_box.currentText()

############# TOUCHDOWN METHODS
    def touch_bar(self, bar_index):
		"""Performs touchdown for the specified bar and updates the interface with X/Y values."""

		self.start_jobs_btn.setStyleSheet('background-color: rgb(255, 255, 0)')
		self.start_jobs_btn.setStyleSheet('border: 2px solid red')
		self.start_jobs_btn.setText(f"Wafer{bar_index} touchdown")
		self.start_jobs_btn.repaint()
		self.send_command(b'GUP\n')
		self.send_command(b'LDC\n')
		self.send_command(b'LDPH 0\n')
		self.wait_ser()

		#z = self.send_command(b'PSGM\n')
		#z_fine_lift = self.send_command(b'RKFM\n')
		#xy = self.send_command(b'PSXY\n')
		#z = int(z.split('PSGM')[1])
		#z_fine_lift = int(z_fine_lift.split('RKFM')[1])
		#self.z_touchdown = z + z_fine_lift

		xy = self.send_command(b'PSXY\n')
		x = float(re.findall(r"-?\d+", xy)[-2])
		y = float(re.findall(r"-?\d+", xy)[-1])
		getattr(self, f'table_bar{bar_index}').setItem(0, 0, QTableWidgetItem(str(x)))
		getattr(self, f'table_bar{bar_index}').setItem(0, 1, QTableWidgetItem(str(y)))
		self.file_save(self.collect())
		self.reset_start_btn()

############# TOUCHDOWN METHODS		
    def update_combo_box(self,combo_object, array):
		"""Adds items from the array to the specified combo box."""
		combo_object.addItems(array)
    def select_job(self):
		"""Opens a folder dialog and populates the job combo box with available jobs."""
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
		"""Updates job info and labels based on the selected job file."""
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
		"""Moves the prober to the touchdown position for bar 1."""
		self.file_save(self.collect())
		self.go_probe()
		self.send_command(b'LI1\n')
		xtd = self.table_bar1.item(0, 0).text()
		ytd = self.table_bar1.item(0, 1).text()
		command = f'GTXY {xtd},{ytd}\n'.encode()
		x = self.send_command(command)
    def go_td2(self):
		"""Moves the prober to the touchdown position for bar 2."""
		self.file_save(self.collect())
		self.go_probe()
		self.send_command(b'LI1\n')
		xtd = self.table_bar2.item(0, 0).text()
		ytd = self.table_bar2.item(0, 1).text()
		command = f'GTXY {xtd},{ytd}\n'.encode()
		self.send_command(command)
	    def go_td3(self):
		"""Moves the prober to the touchdown position for bar 3."""
		self.file_save(self.collect())
		self.go_probe()
		self.send_command(b'LI1\n')
		xtd = self.table_bar3.item(0, 0).text()
		ytd = self.table_bar3.item(0, 1).text()
		command = f'GTXY {xtd},{ytd}\n'.encode()
		self.send_command(command)
    def go_td4(self):
		"""Moves the prober to the touchdown position for bar 4."""
		self.file_save(self.collect())
		self.go_probe()
		self.send_command(b'LI1\n')
		xtd = self.table_bar4.item(0, 0).text()
		ytd = self.table_bar4.item(0, 1).text()
		command = f'GTXY {xtd},{ytd}\n'.encode()
		self.send_command(command)
    def go_td5(self):
		"""Moves the prober to the touchdown position for bar 5."""
		self.file_save(self.collect())
		self.go_probe()
		self.send_command(b'LI1\n')
		xtd = self.table_bar5.item(0, 0).text()
		ytd = self.table_bar5.item(0, 1).text()
		command = f'GTXY {xtd},{ytd}\n'.encode()
		self.send_command(command)	
    def go_td6(self):
		"""Moves the prober to the touchdown position for bar 6."""
		self.file_save(self.collect())
		self.go_probe()
		self.send_command(b'LI1\n')
		xtd = self.table_bar6.item(0, 0).text()
		ytd = self.table_bar6.item(0, 1).text()
		command = f'GTXY {xtd},{ytd}\n'.encode()
		self.send_command(command)
    def go_td7(self):
		"""Moves the prober to the touchdown position for bar 7."""
		self.file_save(self.collect())
		self.go_probe()
		self.send_command(b'LI1\n')
		xtd = self.table_bar7.item(0, 0).text()
		ytd = self.table_bar7.item(0, 1).text()
		command = f'GTXY {xtd},{ytd}\n'.encode()
		self.send_command(command)
    def temp_job_finder(self):
		"""Finds temporary job files for the current wafer."""
		root_folder = '/'.join(self.job_id.text().split('/')[0:-1])
		wafer = self.wafer_id.text()
		job_temp = glob.glob(root_folder + f'/*{wafer}*'+'_JOB.yaml')
		if 5-len(job_temp)>0:
			for i in range(5-len(job_temp)):
				job_temp.append([])
		return job_temp
    def bar_start(self):
		"""Starts bar measurements for all checked bars."""
		stat_bar1 = self.check_bar1.isChecked()
		stat_bar2 = self.check_bar2.isChecked()
		stat_bar3 = self.check_bar3.isChecked()
		stat_bar4 = self.check_bar4.isChecked()
		stat_bar5 = self.check_bar5.isChecked()
		stat_bar6 = self.check_bar6.isChecked()
		stat_bar7 = self.check_bar7.isChecked()
		
		bar1 = self.check_bar1.text()
		bar2 = self.check_bar2.text()
		bar3 = self.check_bar3.text()
		bar4 = self.check_bar4.text()
		bar5 = self.check_bar5.text()
		bar6 = self.check_bar6.text()
		bar7 = self.check_bar7.text()
		prog_arr = ['bar','bar','bar','bar','bar','bar','bar']
		stat_arr = [stat_bar1, stat_bar2, stat_bar3, stat_bar4, stat_bar5, stat_bar6,stat_bar7]
		user_name_arr  = [self.op_id.currentText(),
						self.op_id.currentText(),
						self.op_id.currentText(),
						self.op_id.currentText(),
						self.op_id.currentText(),
						self.op_id.currentText(),
						self.op_id.currentText()]
		if self.check_temp_meas.isChecked():
			job_file_arr = self.temp_job_finder()
		else:
			job_file_arr = [self.job_id.text(),
						self.job_id.text(),
						self.job_id.text(),
						self.job_id.text(),
						self.job_id.text(),
						self.job_id.text(),
						self.job_id.text()]

		x_td_arr = [int( self.table_bar1.item(0, 0).text().split('.')[0] ),
						int( self.table_bar2.item(0, 0).text().split('.')[0] ),
						int( self.table_bar3.item(0, 0).text().split('.')[0] ),
						int( self.table_bar4.item(0, 0).text().split('.')[0] ),
						int( self.table_bar5.item(0, 0).text().split('.')[0] ),
						int( self.table_bar6.item(0, 0).text().split('.')[0] ),
						int( self.table_bar7.item(0, 0).text().split('.')[0] )]

		y_td_arr = [int(self.table_bar1.item(0, 1).text().split('.')[0]),
						int(self.table_bar2.item(0, 1).text().split('.')[0]),
						int(self.table_bar3.item(0, 1).text().split('.')[0]),
						int(self.table_bar4.item(0, 1).text().split('.')[0]),
						int(self.table_bar5.item(0, 1).text().split('.')[0]),
						int(self.table_bar6.item(0, 1).text().split('.')[0]),
						int(self.table_bar7.item(0, 1).text().split('.')[0])]

		cell_index_start =[self.line_start1.text(),
						self.line_start2.text(),
						self.line_start3.text(),
						self.line_start4.text(),
						self.line_start5.text(),
						self.line_start6.text(),
						self.line_start7.text()]
				
		cell_index_end = [self.line_end1.text(),
						self.line_end2.text(),
						self.line_end3.text(),
						self.line_end4.text(),
						self.line_end5.text(),
						self.line_end6.text(),
						self.line_end7.text()]
		if stat_arr==[False,False,False,False,False,False,False]:
				self.start_jobs_btn.setStyleSheet('background-color: rgb(255, 255, 0)')
				self.start_jobs_btn.setText("Check a wafer to measure")
				self.start_jobs_btn.repaint()
				time.sleep(1)
		print(self.check_temp_meas.isChecked())
		print('############################################')
		print(job_file_arr)
		print('############################################')
		try:
			self.tool_id, self.session_id = generate_session_ID()
		except:
			self.tool_id, self.session_id = 'tool_id', 'session_id'
			print('Session ID generation failed!')
			pass

		if self.check_repeat.isChecked():
			repetition = int(self.drop_repeat.currentText())
		else: 
			repetition = 1
		
		# Build job queue instead of processing immediately
		self.job_queue = []
		self.stop_requested = False
		
		for rep in range(repetition):
			for job, user, x_td, y_td, check_bar, start_index, end_index, prog in  zip(job_file_arr, user_name_arr, x_td_arr, y_td_arr,stat_arr, cell_index_start, cell_index_end, prog_arr):
				if check_bar:
					self.job_queue.append({
						'job': job,
						'user': user,
						'x_td': x_td,
						'y_td': y_td,
						'check_bar': check_bar,
						'start_index': start_index,
						'end_index': end_index,
						'prog': prog
					})
		
		# Start processing the job queue
		if self.job_queue:
			self.process_next_job()
		else:
			self.start_jobs_btn.setStyleSheet('background-color: rgb(255, 255, 0)')
			self.start_jobs_btn.setText("No bars selected")
			self.start_jobs_btn.repaint()
			time.sleep(1)
			self.reset_start_btn()
    def process_next_job(self):
		"""Process the next job in the queue without blocking the GUI."""
		if self.stop_requested:
			print('Job processing stopped by user')
			self.job_queue = []
			self.reset_start_btn()
			return
		
		if not self.job_queue:
			# All jobs completed
			print('All jobs completed')
			self.reset_start_btn()
			return
		
		# Get next job from queue
		current_job = self.job_queue.pop(0)
		
		# Update UI
		self.start_jobs_btn.setStyleSheet('background-color: rgb(255, 255, 0)')
		self.start_jobs_btn.setText(f"{current_job['prog']} in progress ({len(self.job_queue)})")
		self.start_jobs_btn.repaint()

		# Run job on the main Qt thread to avoid cross-thread QObject/UI errors
		try:
			self.run(
				current_job['job'], current_job['user'], current_job['x_td'], current_job['y_td'],
				current_job['check_bar'], current_job['start_index'], current_job['end_index'], current_job['prog']
			)
		except Exception as err:
			self.on_job_error(str(err))
			return

		# Schedule next job after current one completes
		if not self.stop_requested:
			QTimer.singleShot(0, self.process_next_job)
    def on_job_error(self, error_message):
		"""Handle errors that occur during job execution."""
		print(f"Job error occurred: {error_message}")
		# Clear remaining jobs from queue
		self.job_queue = []
		self.stop_requested = True
		# Reset button
		self.reset_start_btn()
		# Show error message to user
		QMessageBox.critical(self, "Measurement Error", 
						 f"An error occurred during measurement:\n\n{error_message}\n\nRemaining jobs have been cancelled.")

####misc. table
    def gen_liv_config(self):
		# read values from gui
		wafer_array = AllItems = [self.liv_wafers_combo_box.itemText(i) for i in range(self.liv_wafers_combo_box.count())]
		now=time.time()
		for wafers_num in wafer_array:
			val_20c = 20*self.liv_temp_20c.isChecked()
			val_40c = 40*self.liv_temp_40c.isChecked()
			val_55c = 55*self.liv_temp_55c.isChecked()
			val_80c = 80*self.liv_temp_80c.isChecked()
			val_85c = 85*self.liv_temp_85c.isChecked()
			
			temp_arr = [val_20c,val_40c, val_55c, val_80c, val_85c]
			temp_arr_clean = []
			for i in temp_arr:
				if i >0:
					temp_arr_clean.append(i)
			if len(temp_arr_clean)==0:
				temp_arr_clean = [20]
			#######Writing values in a .yaml
			dict_to_write = {
			'acquisition settings': dict(
			all_measurements_in_one_die=True,
			amf="MANUAL_BT_LIV_AMF_MULTI_TEMP.yaml",
			ccf='dummy',
			mdf='dummy',
			mmf='dummy',
			probecard='T1',
			sample_type='wafer',
			save_shell_output=True,
			PL=int(self.liv_wvgl_box.currentText()),
			T_set = temp_arr_clean,
			LIV = eval(self.liv_meas_box.currentText()),
			Spectrum = eval(self.spec_meas_box.currentText()),
			Spectrum_I_SOA = float(self.spec_curr.currentText()),
			cell_type = self.liv_cell_box.currentText(),
			t1_version = eval(self.t1_version.currentText()),
			combi_mode = eval(self.combi_meas_box.currentText())
			),
			'batch_information': dict(
			batch=self.liv_batch_line.text(),
			customer=self.liv_cust_line.text(),
			lot=self.liv_batch_line.text(),
			product=self.liv_prod_line.text(),
			wafers= wafers_num
			#cell_ids = eval(self.liv_cell_ids_input.toPlainText()).split(product_id+cell_type)[1:]
			),
			'date_and_version': dict(
			author=self.op_id.currentText(),
			date=strftime('%d-%b-%y %H.%M.%S', localtime(now)).split(' ')[0],
			email='marcos.dasilva.eleoterio@smartphotonics.nl',
			time=strftime('%d-%b-%y %H.%M.%S', localtime(now)).split(' ')[-1],
			),
			'post-acquisition settings': dict(
			compressing_files=True,
			job_type='PROD',
			quick_analysis=False
			),
			'setup': 'TM0002'
			}
			
			yaml_filename = wafers_num + '_ManualLIV_JOB'
			root_path = 'C:/Users/HP/Smart Photonics/Engineering - Test & Measurement/Internal Projects/Job generation'
			folder_location = root_path+f"/{self.liv_cust_line.text()}/{self.liv_prod_line.text()}/{self.liv_batch_line.text()}/TM0002"
			##Creating directory if it is not there
			if not os.path.exists(folder_location):
				os.makedirs(folder_location)
			with open(folder_location + '/'+yaml_filename+'.yaml' , 'w') as outfile:
				yaml.dump(dict_to_write, outfile, default_flow_style=False)
			df = pd.DataFrame({})
			df.to_csv(folder_location + f'/{wafers_num}.csv')
			try:
				os.startfile(folder_location)
			except Exception as e:
				print(e)
    def run_mes_check(self, update_gui=True):
		traveler_info = {}
		#update label
		self.label_warning.setText("Retrieving traveler information from MES...")
		new_font = QFont("Arial", 20)
		new_font.setBold(True)
		self.label_warning.setFont(new_font)
		self.label_warning.setStyleSheet("color:red;background-color: yellow;")
		QtWidgets.QApplication.processEvents()  # Force GUI update
		start_connect = time.time()
		
		while traveler_info == {}:
			rpc = MesCom.EzMesClient()
			traveler_info = rpc.mes_get_traveler_information(self.wafers_line.text())
			conn_time_delta = time.time() - start_connect
			print(conn_time_delta)
			if conn_time_delta>30:
				self.label_warning.setText("Conn. timeout, try again!")
				break
		self.label_warning.setText("Mes data acquisition done.")
		self.label_warning.setStyleSheet("color:blue;background-color: green;")
		QtWidgets.QApplication.processEvents()  # Force GUI update
		rpc.connection.close()
		try:
			print('###############')
			print(rpc)
			print('###############')
			lot_id = traveler_info['LotID']
			wafers = traveler_info['Wafers']
			prod_id = traveler_info['RequestedPart']
			curr_step = traveler_info['CurrentStep']
			wafers_arr = [wafers[i]['WaferId'] for i, key in enumerate(wafers)]
			work_order = traveler_info['WorkOrder']
			match = re.search(r'BLN03|PNC15|DFB01|DFB03|DFB04|BLN01|PNC21|PNC06|MPO06|MPS25|MPC057|OLSG2|T1|OMP05|MAC01|AOT01', prod_id)
			if match:
				prod_id = match.group(0)
			else:
				prod_id = prod_id
			if update_gui:
				self.liv_batch_line.setText(lot_id)
				self.liv_prod_line.setText(prod_id)
				self.liv_wafers_combo_box.clear()
				self.liv_wafers_combo_box.addItems(wafers_arr)
				self.liv_cust_line.setText(work_order)
			else:
				print('No update')
				return work_order,prod_id,lot_id
		except Exception as err:
			print(err)

####Methods for MLIV meas
    def get_temp(self):
		tec_t = tec.Tec()          # TEC
		tec_t.connect(port="COM4")
		temp = tec_t.get_temperature()
		self.temp_tec.setText(str(temp) +  '°C')
		tec_t.release()
    def chunker(self, seq, size):
		return(seq[pos:pos+size] for pos in range(0, len(seq),size))
    def spc_start(self):
		#### Pre-defined settings ####
		current_dict = {
			"DBRB12":0.120,
			#"ID_DBR9":0.120,
			#"ID_DBR11":0.120,
			#"ID_DBR8":0.120,
			#"ID_DBR10":0.120,
			#"ID_DBR7":0.120,
			#"DBRB6":0.120,
			#"ID_DBR3":0.120,
			#"ID_DBRB5":0.120,
			#"ID_DBR2":0.120,
			#"ID_DBRB4":0.120,
			#"ID_DBR1":0.120
			}

		LIV_settings = { # Settings for running LIV measurements
			"pulse_delay": 1.E-3,  # s
			"pulse_width": 1.E-5,  # s
			"pulse_mode": 'DC',  # i.e. "Staircase" mode
			"step_size": 5.E-4,  # A
			"resp_at_1310": -166.25,  # PD responsivity for wavelength 1310 nm = -166.25
			"resp_at_1550": -133.51,  # PD responsivity for wavelength 1550 nm = -133.51
			}
		Spectrum_settings = { # Settings for running Spectral measurements
			"resolution": 'high',  # 0 = low, 1 = high
			"sensitivity": 'high',  # 0 = low, 1 = medium low, 2 = medium high, 3 = high
			"spectrum_window": 100 # nm, width of wavelength range for spectral measurements
			} 
		next_wg = 325 # um, distance on y-axis between consecutive DBR lasers 
		operator_id = self.op_id_spc.currentText()
		
		##### Collect measurement and sample information #####
		### Ask user for JOB file ###
		job_file_root = "C:/Users/HP/Smart Photonics/Engineering - Test & Measurement/Internal Projects/Job generation/SPC/TM0002/T3/"
		job_file = "PM-DEV-206600_1NS23035PFE021_ManualLIV_JOB.yaml"
		cells_file = "cells_wafer_021.csv"
		job_file_path = job_file_root + job_file
		cells_file_path = job_file_root + cells_file
		### Open the JOB file, if provided, and feed it into the job_dict ###

		if job_file_path:
			with open(job_file_path, 'r') as f:
				job_dict = yaml.safe_load(f)
				f.close()
		else: 
			job_dict = {}

		### Get information out of the JOB file, ask the Operator for the missing ones ###
		customer_id = job_dict.get("customer", None)
		lot_id = job_dict.get("lot", None)
		product_id = job_dict.get("product", None)
		wafer_id = job_dict.get("wafer", None)
		pl = job_dict.get("PL", None)
		temp_set= job_dict.get("T_set", None)
		liv = job_dict.get("LIV", False)
		spectrum = job_dict.get("Spectrum", False)
		i_soa = job_dict.get("Spectrum I_SOA", None)
		cell_type = job_dict.get("cell_type", "T3")

		if not customer_id:
			customer_id = input("Customer ID: ")
		if not product_id:
			product_id = input("Product ID: ")
		if not lot_id:
			lot_id = input("Lot ID: ")
		if not wafer_id:
			wafer_id = input("Wafer ID: ")
		if not pl:
			pl = int(input("PL wavelength [1310 or 1550]: "))
		if not temp_set:
			temp_set = int(input("Chuck set temperature: "))                   
		while not (liv or spectrum):
			print("No measurement type has been entered")
			answer=("Perform LIV measurements? [Y/N]")
			if answer.upper() != "Y" or answer.upper() != "YES":
				liv=True
			answer=("Perform Spectral measurments? [Y/N]")
			if answer.upper() != "Y" or answer.upper() != "YES":
				spectrum=True
		print('Configs loaded...')
		# Set the SOA current at which to perform the spectral measurement(s)
		if spectrum:
			if not i_soa:
				#i_soa = input("SOA current (relative to max allowed SOA current) for spectral measurements (if multiple value, use a comma to separate them) [0-1]: ")
				i_soa = '1'
			# convert i_soa in an array of numbers
			i_soa = i_soa.replace(" ","") # remove empty characters, if any
			i_soa = i_soa.split(",")
			try: # convert strings into numerical float values
				i_soa = [float(i) for i in i_soa]
				if any(i>1 or i<0 for i in i_soa): # check if the numerical values of I_SOA are meaningful
					print(f"ERROR! The values of current must be between 0 and 1, while the following values {', '.join(i_soa)} were entered")
					raise ValueError
			except:
				print(f"ERROR! Impossible to convert the entered values {', '.join(i_soa)} to a numerical value")
				raise ValueError
		# Check provided PL wavelength
		while (pl != 1550) and (pl != 1310):
			print("ERROR! PL wavelength must be either 1550 or 1310")
			raise SystemExit("Not configured PL value entered, exiting program")

		df = pd.read_csv(cells_file_path)
		cell_id_list = df.CellID.values.tolist()
		n_cells = len(cell_id_list)
		# make a folder for storing raw data
		path = f'D:/PRODUCTION/data/{customer_id}/manual_BT_liv/{product_id}_{lot_id}'
		if not os.path.isdir(path):
			os.makedirs(path)
		##### End of sample information collection and subsequent actions #####
		#### Connect the instruments ####
		
		tec_t = tec.Tec()          # TEC
		tec_t.connect(port="COM4")
		
		ktl = keithley2602B()    # SMU
		ktl.connect()
		print('Is connected!!!!!!!!!!!!')
		while True:
			if not(self.is_connected()):
				self.stat_probe.setText("NOT CONNECTED!!!")
				new_font = QFont("Arial", 30)
				new_font.setBold(True)
				self.stat_probe.setFont(new_font)
				self.stat_probe.setStyleSheet("color:red;background-color: yellow;")
				time.sleep(0.1)
				QApplication.processEvents()
			else:
				self.stat_probe.setText("CONNECTED!!!")
				new_font = QFont("Arial", 30)
				new_font.setBold(True)
				self.stat_probe.setFont(new_font)
				self.stat_probe.setStyleSheet("color:green;background-color: yellow;")
				QApplication.processEvents()
				break

		#set light on
		self.send_command(b'LI1\n')
		self.send_command(b'TSTHD 2\n') #---sphere
		
		### Set the chuck temperature ###
		print("Connecting Tec and setting temperature to {}".format(temp_set))
		tec_t.set_temperature(temp_set)
		tec_t._set_enable()
		print("Waiting for temperature to stabilise...")
		tec_t._set(T_set = temp_set, T_win = 2)

		self.go_probe()
		self.gross_up()
		cells_list = []     
		session_start = str(datetime.datetime.now()).replace(' ', '_')
		measurement_counter = 0
		kill = 0
		list_rawdata_files = []
		n_cell_to_measured = 3
		self.go_probe()
		for loaded_cells in self.chunker(cell_id_list, n_cell_to_measured):
			for idx in loaded_cells: # For loop on individual cells
				cell_id = idx
				
				for device_idx, (device_id, max_current) in enumerate(current_dict.items()): # for loop on individual FP lasers in each cell
					if kill == 1: # acquisition is stopped if "Kill" command has been sent
						break
					if device_idx == 0: # adjust probe height for first laser of every cell
				
						if idx == 0:
							print('Align probes in X-direction manually using the screw-micrometer')
							print('')
				
						self.send_command(b'LDPH 0\n') #Go to local and the asks the user to perform a touchdown
						self.wait_ser()
				
					else:
						self.send_command(b'CDW\n')#fine down
						if device_id=='ID_DBRB7':
							next_wg=350
						else:
							next_wg=325
						self.rel_mov(0, next_wg)

					temperature = tec_t.get_temperature()
					print('t={}'.format(temperature))
					self.send_command(b'CUP\n')#fine up
					if liv: # Execute LIV measurements
						while True:
							self.send_command(b'TSTHD 2\n') ##move test head to Sphere
							c, v, pds = ktl.LIVpulsedsweep(sweepstart=0,
														  sweepstop=max_current,
														  step_size=LIV_settings["step_size"],
														  smua_ilimit=0.5,  # not used, limit is internally calculated for best performance
														  smua_vlimit=5,
														  pulse_delay=LIV_settings["pulse_delay"],
														  pulse_width=LIV_settings["pulse_width"],
														  pulse_mode=LIV_settings["pulse_mode"],
														  )
							
							
							if pl == 1310:
								resp = LIV_settings["resp_at_1310"]
							if pl == 1550:
								resp = LIV_settings["resp_at_1550"]
							power = [-i_c * resp for i_c in pds.magnitude]
							c = [i for i in c.magnitude]
							v = [i for i in v.magnitude]
							
							###Add a method to plot pyqt......
							x, y1, y2, cell = c[1:], v[1:], power[1:], device_id
							
							ic(x, y1, y2, cell)
							self.plot_win(x, y1, y2, cell)
							
							measurement_plan = 'LIV_{}'.format(device_id)
							now = str(datetime.datetime.now()).replace(' ', '_')
							now = now.replace(':', '.')
							fname = '{}_{}_{}_{}.txt'.format(
								wafer_id, cell_id, measurement_plan, now)
							data = {
								'_openEPDA_version': openEPDA_version,
								'CustomerID': customer_id,
								'LotID': lot_id,
								'ProductID': product_id,
								'Cell': cell_id,
								'Filename': fname,
								'ToolID': 'TM0002',
								'Measurement plan': measurement_plan,
								'Mode': LIV_settings["pulse_mode"],
								'ObservationID': measurement_counter,
								'OperatorID': operator_id,
								'PL_wavelength': pl,
								'MeasurementSession': 'TM0002_{}'.format(session_start),
								'Session_start_time': session_start,
								'SetTemperature': temp_set,
								'Wafer': wafer_id,
								'Current LD, [A]': c,
								'Voltage LD, [V]': v,
								'Photocurrent PD, [A]': pds.magnitude,
								'Power PD, [W]': power
							}
							w = openepda.OpenEpdaDataDumper()
							with open(os.path.join(path, fname), 'w', newline="\n") as f:
								w.write(f, **data)
							list_rawdata_files.append(os.path.join(path, fname))    
							measurement_counter += 1
							break
					if device_idx == 11 and not(spectrum):
						self.send_command(b'CDW\n')#fine down
						self.rel_mov(0, 400)
						
				if spectrum:
					rev_curr_dict = OrderedDict(reversed(list(current_dict.items())))
					for device_idx, (device_id, max_current) in enumerate(rev_curr_dict.items()): # for loop on individual FP lasers in each cell
						self.send_command(b'CDW\n')#fine down
						if device_id=='DBRB6':
							next_wg=-350
						elif device_id=='ID_DBR1':
							next_wg = 0
						else:
							next_wg=-325
						self.rel_mov(0, next_wg)
						self.send_command(b'CUP\n')#fine up
						
						if spectrum: # Execute Spectral measurements
							self.send_command(b'TSTHD 1\n') #---Fiber
							for soa_current in i_soa:
								spec_current = max_current * soa_current  # sets used current as a factor of max LIV currents
								ktl.reset()
								ktl.set_current(1, spec_current)
								ktl.set_channel_state(1, 'on')
								wavelength, power, peak_index = self.acq_osa()
								ktl.set_channel_state(1, 'off')
								x = wavelength[peak_index - 500:peak_index + 500]
								y1 = power[peak_index - 500:peak_index + 500]
								cell = device_id
								self.plot_win(x, y1, cell)
								#save data
								measurement_plan = 'SPECTRAL_{}_{}'.format(
								device_id, round(spec_current, 4))
								now = str(datetime.datetime.now()).replace(' ', '_')
								now = now.replace(':', '.')
								fname = '{}_{}_{}_{}.txt'.format(
								wafer_id, cell_id, measurement_plan, now)
								data = {
								'_openEPDA_version': openEPDA_version,
								'CustomerID': customer_id,
								'LotID': lot_id,
								'ProductID': product_id,
								'Cell': cell_id,
								'Filename': fname,
								'ToolID': 'TM0002',
								'Measurement plan': measurement_plan,
								'Mode': "DC",
								'ObservationID': measurement_counter,
								'OperatorID': operator_id,
								'PL_wavelength': pl,
								'MeasurementSession': 'TM0002_{}'.format(session_start),
								'Session_start_time': session_start,
								'SetTemperature': int(temp_set),
								'Wafer': wafer_id,
								'Sourcing_current [A]': round(spec_current, 4),
								'Wavelength, [nm]': wavelength,
								'Power, [W]': power
								}
								w = openepda.OpenEpdaDataDumper()
								with open(os.path.join(path, fname), 'w', newline="\n") as f:
									w.write(f, **data)
								list_rawdata_files.append(os.path.join(path, fname))    
								
						if device_idx == 11 and spectrum:
							self.send_command(b'CDW\n')#fine down
							self.rel_mov(0, 4025)
							
		######## Ending the measurement #######
		### Return BT to load position and disconnect tools ###
		print('returning chuck to loading position and releasing equipment')
		self.send_command(b'LI0\n')
		self.send_command(b'CDW\n')#fine down
		self.gross_down()
		self.move_unload()
		tec_t.release()
		ktl.release()

		#####Data Extraction
		file_root = "C:/Users/HP/Smart Photonics/Engineering - Test & Measurement/Internal Projects/Job generation/SPC/TM0002/T3/" 
		de_file = "Data_extractor_no_entry.py"
		de_file_path = file_root + de_file
		data_path = path
		call(['python',de_file_path, data_path])
		###Change DE column names
		
		try:
			A_corr = []
			de_folder = data_path + '\\analyses_results'
			de_results = glob.glob(de_folder+'\\*metadata.csv')
			df = pd.read_csv(de_results[0])
			for i in de_results:
				df_clean = df.loc[:, ~df.columns.str.startswith('_meta')]
				A = df_clean.columns
				for x in enumerate(A):
					if x[0]<8:
						A_corr.append(x[1])
					else:
						A_corr.append('DLT_SSP_EET_' + x[1])
				df_clean.columns = A_corr
				time_sufix = time.time()
				df_clean.to_csv( f'O:/06 Customers/rawdata backup/TM0002/PM-DEV-206600/SPC/DataExtraction/{customer_id}_{product_id}_{lot_id}_{wafer_id}_{time_sufix}.csv')
		except:
			pass
		### Zip rawdata files, if any ####
		zip_file_name=""
		
		if list_rawdata_files:
			folder = [os.path.split(f)[0] for f in list_rawdata_files][0]
			# ABI: I think I have to change the way the zip file name is given -> get it from "folder"
			zip_file_name = ("_").join([customer_id, product_id , lot_id, wafer_id,"SessionStart",session_start+".zip"])
			zip_file_name = zip_file_name.replace(':','-') #removing illegal ":" character  
			zip_file_name = os.path.join(folder,zip_file_name) # add the folder location to the zip file name  
			with ZipFile(zip_file_name, 'w') as zipObj:
				# Iterate over all the output files in directory
				for filename in list_rawdata_files:
					zip_fname = os.path.join('rawdata',os.path.split(filename)[1]) # name of zipped file inside the zip folder
					# Add file to zip
					zipObj.write(filename,arcname=zip_fname)
					# deleting the zipped file
					os.remove(filename)
			
			print("All output files zipped and removed!")

		### Save Zip file in backup location ###
		if zip_file_name:
			zip_file_name_stripped = os.path.split(zip_file_name)[1] # name of zip file stripped of path location
			backup_folder = f"O:\\06 Customers\\rawdata backup\\TM0002\\{customer_id}\\{lot_id}"
			destination_filename = os.path.join(backup_folder, zip_file_name_stripped)
			# check if the destination folder on backup location exists, if not creates it
			if not os.path.exists(backup_folder):
				os.makedirs(backup_folder)
			
			# copy file to the back up location
			cmd_failure = os.system((" ").join(['copy', '"'+zip_file_name+'"', '"'+destination_filename+'"']))

			if cmd_failure==0:
				print(f"Zip file {zip_file_name_stripped} has been copied at backup location!")
			else:
				print(f"Warning! Zip file {zip_file_name_stripped} has NOT been copied at backup location!")
    def start_jobs_in_thread(self):
		current_tab_index = self.meas_tab.currentIndex()
		if current_tab_index == 0:
			job_method = self.bar_start
		elif current_tab_index == 1:
			job_method = self.die_start
		elif current_tab_index == 2:
			job_method = self.spc_start

		self.worker_thread = QThread()
		self.worker = Worker(job_method)
		self.worker.moveToThread(self.worker_thread)
		self.worker_thread.started.connect(self.worker.run)
		self.worker.finished.connect(self.on_jobs_finished)
		self.worker_thread.start()
    def on_jobs_finished(self, msg):
		print(msg)
		self.worker_thread.quit()
		self.worker_thread.wait()
    def start_jobs(self):
		###########
		#Indexes of the tables
		#0: Bar measurements
		#1: Dies measurements
		#2: SPC
		print('########################')
		current_tab_index = self.meas_tab.currentIndex()
		print('########################')
		if current_tab_index == 0:
			self.bar_start()
		elif current_tab_index == 1:
			self.die_start()
		elif current_tab_index == 2:
			self.spc_start()
    def reset_start_btn(self):
		self.start_jobs_btn.setStyleSheet('background-color: rgb(85, 255, 127)')
		self.start_jobs_btn.setText("START")
		self.start_jobs_btn.repaint()
	    def gen_bars_job(self):
		#Collect the info
		work_dir = os.getcwd() + '\\Job_gen_files\\'
		costumer = self.liv_cust_line.text()
		ccf_filepath = self.bar_ccf_file.currentText()
		
		val_20c = 20*self.bar_job_temp_20c.isChecked()
		val_25c = 25*self.bar_job_temp_25c.isChecked()
		val_40c = 40*self.bar_job_temp_40c.isChecked()
		val_55c = 55*self.bar_job_temp_55c.isChecked()
		val_75c = 75*self.bar_job_temp_75c.isChecked()
		val_80c = 80*self.bar_job_temp_80c.isChecked()
		val_85c = 85*self.bar_job_temp_85c.isChecked()
		
		temperatures = [val_20c,val_25c,val_40c, val_55c, val_75c, val_80c, val_85c ]
		temp_arr_clean = []
		for i in temperatures:
			if i >0:
				temp_arr_clean.append(i)
		if len(temp_arr_clean)==0:
			temp_arr_clean = [20]


		#get all wafers in the combo box
		AllItems = [self.liv_wafers_combo_box.itemText(i) for i in range(self.liv_wafers_combo_box.count())]
		run_info = []
		for i in AllItems:
			arr_temp = [self.liv_batch_line.text(), self.liv_prod_line.text(), i]
			run_info.append(arr_temp)
			
		run_job_file = work_dir+self.bar_job_file.currentText()
		run_job_file = run_job_file.replace('\\', '/')
		run_ccf_file = work_dir+self.bar_ccf_file.currentText()
		run_ccf_file = run_ccf_file.replace('\\', '/')
		#calling the job file gen
		info_arr = [run_job_file, run_ccf_file, run_info, costumer, temp_arr_clean]
		try:
			print(run_job_file, run_ccf_file, run_info, costumer, temp_arr_clean)
			print("*********************************************")				
			subprocess.Popen([
				'python',
				info_arr[0],
				info_arr[1],
				repr(info_arr[2]),
				info_arr[3],
				repr(info_arr[4])
			])
		except Exception as e:
			print(e)
			QMessageBox.about(self, "Error", "Failed to start job file generation script:\n" + str(e))
    def refresh_bars_combo_box(self):
		curr_dir = os.getcwd()
		work_folder = os.path.join(curr_dir, 'Job_gen_files')
		ccf_files = glob.glob(work_folder+'/*CCF.csv')
		job_files = glob.glob(work_folder+'/*JOB.py')
		self.bar_job_file.clear()
		self.bar_ccf_file.clear()
		job_files = [i.split('\\')[-1] for i in job_files]
		ccf_files = [i.split('\\')[-1] for i in ccf_files]	
		self.bar_job_file.addItems(job_files)
		self.bar_ccf_file.addItems(ccf_files)
    def _abort_if_stop_requested(self):
		"""Process UI events and abort current run if Stop was requested."""
		QtWidgets.QApplication.processEvents()
		if self.stop_requested:
			raise RuntimeError('Measurement stopped by user')
    def stop_all(self):
		"""Stops the currently running thread/worker and clears the job queue."""
		# Set stop flag to prevent processing more jobs from queue
		self.stop_requested = True
		QtWidgets.QApplication.processEvents()
		# Clear remaining jobs in queue
		if hasattr(self, 'job_queue'):
			remaining_jobs = len(self.job_queue)
			self.job_queue = []
			if remaining_jobs > 0:
				print(f'Cleared {remaining_jobs} pending jobs from queue')
		
		if hasattr(self, 'worker') and self.worker is not None:
			print('Stopping current worker...')
			self.worker.stop()
			if hasattr(self, 'thread') and self.thread is not None and self.thread.isRunning():
				self.thread.quit()
				# Don't use wait() here - it would block the GUI!
				# The thread will clean up asynchronously
				QTimer.singleShot(3000, lambda: self._force_terminate_thread())
				self.end()

				print('Thread stop requested')
			QMessageBox.about(self, "Stopped", "Stop requested. Finishing current step and shutting down...")
		else:
			QMessageBox.about(self, "Stopped", "Stop requested. Finishing current step and shutting down...")
    def _force_terminate_thread(self):
		"""Force terminate thread if it hasn't stopped gracefully."""
		if hasattr(self, 'thread') and self.thread is not None and self.thread.isRunning():
			print('Force terminating thread...')
			self.thread.terminate()
			self.thread.wait(1000)
    def cleanup(self):
		print(print("Doing cleanup in end()"))
		QtWidgets.QApplication.quit()
    def closeEvent(self, event):
		print("Window closed")
		try:
			self.end()
		except:
			pass
		event.accept()
def main():
	app = QtWidgets.QApplication(sys.argv)
	window = Ui()
	window.show()
	sys.exit(app.exec_())

if __name__ == '__main__': # only executes the below code if it python has run it as the main
	main()

