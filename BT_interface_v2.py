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
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtWidgets import QTableWidgetItem, QFileDialog, QApplication, QMessageBox
from PyQt5.QtGui import QFont 
from PyQt5.QtCore import QThread, QTimer, QObject, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor
import openepda
from openepda import OpenEpdaDataLoader
import pyqtgraph as pg
import serial
from functools import partial
import re
import yaml
import glob
import subprocess
from subprocess import call
import codecs
sys.path.insert(1, 'C:\\AMS')
from smu.keithley2602B import Keithley2602B
ktl = Keithley2602B()
from Yokogawa import AQ6370D as osa


class Ui(QtWidgets.QMainWindow):
	class OutputStream(QObject):
		text_written = pyqtSignal(str)

		def __init__(self, original_stream, parent=None):
			"""Wrap a stream and emit a signal whenever text is written."""
			super().__init__(parent)
			self.original_stream = original_stream

		def write(self, text):
			"""Write text to the wrapped stream and forward it to connected slots."""
			self.original_stream.write(text)
			self.original_stream.flush()
			if text:
				self.text_written.emit(text)

		def flush(self):
			"""Flush the wrapped output stream."""
			self.original_stream.flush()
	class Worker(QObject):
		"""
		Worker class for running measurement commands in a separate thread.
		This class executes a command using subprocess and interacts with the UI via the provided ui_method.
		It supports stopping the process and emits signals when finished or all jobs are done.
		Args:
			cmd (list): The command to execute as a list of arguments for subprocess.
			ui_method (Ui): Reference to the main UI instance for sending commands and updating state.
		Signals:
			finished (str): Emitted when the process finishes or is stopped.
			all_done (): Emitted when all jobs are completed.
		"""
		finished = pyqtSignal(str)
		all_done = pyqtSignal()
		output_ready = pyqtSignal(str)
		
		def __init__(self, cmd, ui_method):
			"""
			Initializes the Worker instance.
			Args:
				cmd (list): The command to execute as a list of arguments for subprocess.
				ui_method (Ui): Reference to the main UI instance for sending commands and updating state.
			"""
			super().__init__()
			self.cmd = cmd
			self.ui_method = ui_method
			self.stop_requested = False
			self.core_process = None

		def run(self):
			"""
			Executes the measurement command in a separate thread.

			- Starts the subprocess for the measurement job.
			- Monitors the process output and emits signals when finished or stopped.
			- Handles user stop requests and cleans up the process.
			"""
			if self.stop_requested:
				self.finished.emit("Execution stopped by user before starting next command")
				return
			
			try:
				self.core_process = subprocess.Popen(
					self.cmd,
					stdout=subprocess.PIPE,
					stderr=subprocess.STDOUT,
					bufsize=0,
				)
				decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')

				while True:
					if self.stop_requested:
						self.core_process.kill()
						self.core_process.wait()
						self.core_process = None
						self.finished.emit("Stopped by user")
						return
					output = self.core_process.stdout.read(4096)
					if not output:
						break
					text = decoder.decode(output)
					if text:
						self.output_ready.emit(text)

				final_text = decoder.decode(b'', final=True)
				if final_text:
					self.output_ready.emit(final_text)
				return_code = self.core_process.wait()
				result = f"Process exited with code {return_code}"
				self.core_process = None
			except OSError as error:
				self.output_ready.emit(f"Failed to run {self.cmd[0]}: {error}\n")
				result = f"Process could not be started: {error}"
			self.finished.emit(result)
			self.all_done.emit()

		def stop(self):
			"""
			Requests the measurement process to stop.
			- Sets the stop_requested flag to True.
			- Attempts to kill and clean up the subprocess if running.
			- Handles exceptions during process termination.
			"""
			self.stop_requested = True
			try:
				if self.core_process:
					self.core_process.kill()
					self.core_process.wait()
					self.core_process = None
					self.reset_start_btn()

			except:
				pass

	def __init__(self):
		"""Initializes the main UI window and sets up all widgets, connections, and variables."""
		pg.setConfigOption('background', 'w') #before loading widget
		pg.setConfigOption('foreground', 'k')
		super(Ui, self).__init__() # Call the inherited classes __init__ method
		uic.loadUi('BT_interface.ui', self) # Load the .ui file
		# redirecting terminal  display  to GUI item
		self._original_stdout = sys.stdout
		self._original_stderr = sys.stderr
		self._stdout_stream = self.OutputStream(sys.stdout, self)
		self._stderr_stream = self.OutputStream(sys.stderr, self)
		self._stdout_stream.text_written.connect(self.display_out)
		self._stderr_stream.text_written.connect(self.display_out)
		sys.stdout = self._stdout_stream
		sys.stderr = self._stderr_stream
		###definitions from core.py
		self.thread = None
		self.jobgen_thread = None
		self.jobgen_worker = None
		self.curr_files = 0
		###Variable
		self.job_folder_path1 = ''
		self.job_folder_path2 = ''
		#qtimer def
		####Qtimer
		self.timer=QTimer(self)
		self.timer.timeout.connect(self.up_var)
		self.timer.start(3000)
		#touchdown methods
		self.btn_touch1.clicked.connect(partial(self.touch_bar, 1))
		self.btn_touch2.clicked.connect(partial(self.touch_bar, 2))
		self.btn_touch3.clicked.connect(partial(self.touch_bar, 3))
		self.btn_touch4.clicked.connect(partial(self.touch_bar, 4))
		self.btn_touch5.clicked.connect(partial(self.touch_bar, 5))
		self.btn_touch6.clicked.connect(partial(self.touch_bar, 6))
		self.btn_touch7.clicked.connect(partial(self.touch_bar, 7))
		# align calls
		self.btn_align1.clicked.connect(partial(self.align, 1))
		self.btn_align2.clicked.connect(partial(self.align, 2))
		self.btn_align3.clicked.connect(partial(self.align, 3))
		self.btn_align4.clicked.connect(partial(self.align, 4))
		self.btn_align5.clicked.connect(partial(self.align, 5))
		self.btn_align6.clicked.connect(partial(self.align, 6))
		self.btn_align7.clicked.connect(partial(self.align, 7))
		#Method to select job files for the wafers and show it in the dialog
		self.btn_job.clicked.connect(self.select_job)
		self.start_jobs_btn.clicked.connect(self.start_jobs) ###Start the jobs
		self.btn_stop.clicked.connect(self.stop_execution) ###Stop the jobs
		self.unload_btn.clicked.connect(self.move_unload)
		self.probe_btn.clicked.connect(self.go_probe)
		self.gup_btn.clicked.connect(self.gross_up)
		self.gdn_btn.clicked.connect(self.gross_down)
		self.change_pos_btn.clicked.connect(self.change_pos)
		self.fineup_btn.clicked.connect(self.fine_up)
		self.finedown_btn.clicked.connect(self.fine_down)
		self.btn_vac_on.clicked.connect(self.vac_on)
		self.btn_vac_off.clicked.connect(self.vac_off)
		self.btn_move_fiber.clicked.connect(self.go_fiber)
		self.btn_move_sphere.clicked.connect(self.go_sphere)
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
		self.refresh_z_set.clicked.connect(self.up_z_set)
		###LIV/SPC Gui
		self.liv_acq_btn.clicked.connect(self.acq_liv)
		self.tec_btn.clicked.connect(self.get_temp)
		self.osa_acq_btn.clicked.connect(self.acq_osa)
		self.liv_gen_btn.clicked.connect(self.gen_liv_config)
		self.btn_mes_check.clicked.connect( lambda:self.run_mes_check(True))
		#####
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

	def up_var(self):
		"""Updates the UI with the latest touchdown value and progress bar for each wafer."""
		if self.thread is not None and self.thread.isRunning():
			try:
			
				if self.curr_files:
					delta_files = len(glob.glob(self.data_folder+"/*.txt"))- self.curr_files
				else:
					delta_files = 0
				files = glob.glob(self.data_folder+"/*.txt")
				self.curr_files = len(files)
				interval_ms = self.timer.interval()/1000  # Convert milliseconds to seconds
				files_per_second = delta_files/interval_ms if interval_ms > 0 else 0
				valid_files = self.curr_files-self.files_before_starting
				progress = int((valid_files / self.total_meas) * 100 if self.total_meas > 0 else 0)
				self.bar.setValue(progress)
				time_to_finish = (self.total_meas - valid_files) / files_per_second if files_per_second > 0 else 0
				total_time = self.total_meas / files_per_second if files_per_second > 0 else 0
				
				self.time_left.setText(str(round(time_to_finish / 60, 1)))
				self.time_total.setText(str(round(total_time / 60, 1)))
				#arrange plot data
				files.sort(key=os.path.getctime)
				#get paramenter from epda files
				fh=openepda.OpenEpdaDataLoader()
				fh_read = fh.read_file(files[-1])
				self.meas_plan = fh_read['Measurement plan'].split('_')[0]
				self.cell = fh_read['Cell']
				
				if self.meas_plan=='LIV':
					x  = fh_read['I_soa, A']
					y1 = fh_read['V_soa, V']
					y2 = fh_read['P_PD, W']
				elif self.meas_plan=='SPECTRUM':
					x  = fh_read['Wavelength, nm']
					y1 = fh_read['Power, dBm']
					y2 = None
				self.plot_win(x,y1,y2)
			except Exception as err:
				print(f'Var update failed: {err}')
		else:
			pass
	def display_out(self, text):
		"""Append text to the interface output display and scroll to the end."""
		self.output_display.moveCursor(QTextCursor.End)
		self.output_display.insertPlainText(text)
		self.output_display.ensureCursorVisible()

	def display_terminal_output(self, text):
		"""Write subprocess output to the application's original terminal stream."""
		if self._original_stdout is not None:
			self._original_stdout.write(text)
			self._original_stdout.flush()

	def display_subprocess_output(self, text):
		"""Forward subprocess output to both the interface and terminal."""
		self.display_out(text)
		self.display_terminal_output(text)

	def get_total_meas(self, start_index, end_index, job_file):
		"""Calculate measurement count between inclusive MMF row labels."""
		start_label = str(start_index).strip()
		end_label = str(end_index).strip()
		if not start_label or not end_label or start_label.lower() == 'nan' or end_label.lower() == 'nan':
			raise ValueError(f"Invalid MMF range: start={start_index!r}, end={end_index!r}")

		with open(job_file, encoding='utf-8') as stream:
			job_data = yaml.safe_load(stream)
		try:
			mmf_name = job_data['acquisition settings']['mmf']
		except (TypeError, KeyError) as error:
			raise ValueError(f"Job file has no acquisition settings MMF: {job_file}") from error

		mmf_path = os.path.join(os.path.dirname(job_file), mmf_name)
		df = pd.read_csv(mmf_path, index_col='Dies/Measurements')
		row_labels = [str(label).strip() for label in df.index]
		if len(row_labels) != len(set(row_labels)):
			raise ValueError(f"MMF contains duplicate row labels: {mmf_path}")
		try:
			start_row = row_labels.index(start_label)
			end_row = row_labels.index(end_label)
		except ValueError as error:
			raise ValueError(
				f"MMF range not found in {mmf_path}: "
				f"start={start_label!r}, end={end_label!r}"
			) from error
		first_row, last_row = sorted((start_row, end_row))
		df_sliced = df.iloc[first_row:last_row + 1]
		total_meas = df_sliced.sum(axis=1).sum()
		print(f'total meas is : {total_meas}')
		return total_meas

	def plot_win(self, x, y1, y2 = None, cell = None):
		"""Plots measurement data on the plot window. Handles both LIV and spectrum plots."""
		t1 = (0,0,255)
		t2 = (255,0,0)
		pen_t1 = pg.mkPen(color=(0, 0, 255), width=3, style=QtCore.Qt.SolidLine)
		pen_t2 = pg.mkPen(color=(255, 0, 0), width=3, style=QtCore.Qt.SolidLine)
		color1 = '#%02x%02x%02x' % t1
		color2 = '#%02x%02x%02x' % t2
		if y2 is not None:
			#ic(x, y1, y2)
			x_label = 'Current(A)'
			y_label = 'voltage(V)'
			y2_label = 'Power(W)'
			title = f'LIV_{self.cell}'
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
				
				#Exclude the first 5 points 
				power = power[5:-1]
				volt = volt[5:-1]
				pcurr = pcurr[5:-1]
				
				y_min = np.min(volt)
				y_max = np.max(volt)
				self.p1.vb.disableAutoRange(axis = pg.ViewBox.YAxis)
				self.p1.vb.setYRange(y_min, y_max)
				
				y2_min = np.min(power)
				y2_max = np.max(power)
				self.p2.setYRange(y2_min, y2_max)
				self.p2.disableAutoRange(axis = pg.ViewBox.YAxis)

				x_min = np.min(pcurr)
				x_max = np.max(pcurr)
				self.p1.vb.setXRange(x_min, x_max)
				self.p1.vb.disableAutoRange(axis = pg.ViewBox.YAxis)

				try:
					self.p1.plot(pcurr, volt, pen = pen_t1, name = cell)
					self.plot2 = pg.PlotCurveItem(pcurr[10:-1], power[10:-1], pen = pen_t2, name = cell)
				except Exception as err:
					print(err)
					self.p1.plot(pcurr, volt, pen = pen_t1, name = None)
					self.plot2 = pg.PlotCurveItem(pcurr, power, pen = pen_t2, name = None)
					
				
				self.p2.addItem(self.plot2)
				pg.QtGui.QGuiApplication.processEvents()
			except Exception as err:
				print(err)
				pass
		else:
			self.p1 = self.plotter.plotItem
			self.clear_plot()
			x_label = 'Wavelength(nm)'
			y_label = 'Power (dBm)'
			self.p1.setLabels(left = y_label)
			self.p1.setLabels(left = y_label)
			val_x, val_y = x, y1
			y_min = np.min(val_y)
			y_max = np.max(val_y)
			y_max_index = np.where(val_y == y_max)[0]
			
			x_min = np.min(val_x)
			x_max = np.max(val_x)
			x_max_peak = val_x[y_max_index]
			
			#print(f'index of max x is {x_max_index} value of max x is')
			self.p1.vb.setXRange(x_min, x_max)
			self.p1.vb.disableAutoRange(axis = pg.ViewBox.YAxis)
			
			self.p1.vb.setYRange(y_min, y_max)
			self.p1.vb.disableAutoRange(axis = pg.ViewBox.YAxis)
			self.p1.getAxis('bottom').setLabel('Wavelength(nm)')
			self.p1.getAxis('left').setLabel('Power(dBm)', color = color1)
			self.p1.vb.disableAutoRange(axis = pg.ViewBox.YAxis)
			
			
			self.p1.plot(val_x, val_y, pen = pen_t1, name = cell)
			##INSERT MARKER
			marker_x = x_max_peak
			marker_y = y_max
			title = f'Spectrum-peak @{x_max_peak[0]:.2f}nm,{y_max:.2f}dBm'
			self.set_graph(title, x_label, y_label)
			marker_point = pg.ScatterPlotItem(
			x=[marker_x], 
			y=[marker_y], 
			size=5, 
			pen=pg.mkPen('r'), 
			brush=pg.mkBrush('r'), 
			symbol='o'  # 'o' voor een cirkel, 'x' voor een kruis, 't' voor een driehoek
			)
			self.p1.addItem(marker_point)
			pg.QtGui.QGuiApplication.processEvents()
	
	def ktl_meas(self):
		"""Performs a Keithley measurement and updates the voltage display in the UI."""
		current = float(self.ktl_curr.value())/1000
		ktl.connect()
		ktl.set_current('a', current)
		volt = ktl.measure_voltage('a')
		ktl.release()
		self.volt_meas.setText(str(volt))

	def ktl_on(self):
		"""Connect to the Keithley, set the selected current, and enable channel A."""
		ktl.connect()
		current = float(self.ktl_curr.value())/1000
		ktl.set_current('a', current)
		ktl.set_channel_state(channel='a', state='on')
		ktl.release()

	def ktl_off(self):
		"""Connect to the Keithley and disable channel A."""
		ktl.connect()
		ktl.set_channel_state(channel='a', state='off')
		ktl.release()

############OSA methods
	def acq_osa(self):
		"""Acquires a spectrum from the OSA and plots the result."""
		cont_mode_state = self.spec_cont_mode.isChecked()
		if cont_mode_state:
			while cont_mode_state:
				self.get_spectrum()
				cont_mode_state = self.spec_cont_mode.isChecked()
		else:
			self.get_spectrum()

	def get_spectrum(self):
		"""Acquire one OSA spectrum, plot it, and return wavelength, power, and peak data."""
		Spectrum_settings = { # Settings for running Spectral measurements
			"resolution": 1,  # 0 = low, 1 = high
			"sensitivity": 1,  # 0 = low, 1 = medium low, 2 = medium high, 3 = high
			"spectrum_window": int(self.line_range_wav.text()), # nm, width of wavelength range for spectral measurements
			"speed": 0,
			"center_wav": int(self.line_center_wav.text()),
			"autogain":True
			}
		start_wav = Spectrum_settings["center_wav"] - Spectrum_settings["spectrum_window"]
		stop_wav = Spectrum_settings["center_wav"] + Spectrum_settings["spectrum_window"]
		res = Spectrum_settings["resolution"]
		sens = Spectrum_settings["sensitivity"]
		speed = Spectrum_settings["speed"]
		interval = Spectrum_settings["spectrum_window"]
		autogain = Spectrum_settings["autogain"]
		try:
			o = osa.Osa203c()
			o.connect()
			resolution = Spectrum_settings["resolution"]
			sensitivity = Spectrum_settings["sensitivity"]
			o.set_resolution_mode(resolution)
			o.set_sensitivity_mode(sensitivity)
			o.set_auto_gain(autogain)
			time_before = time.time()
			x,y,units = o._perform_measurement(start_wav, stop_wav, res, sens, speed, interval)
			wavelength = x
			power = y
			peak = max(x)
			peak_index = np.where(power==peak)
			self.plot_win(wavelength, power, None)
			try:
				o.release()
			except Exception as err:
				print(err)
				pass
			return wavelength,power, peak_index
		except Exception as error:
			print("Initialization failed ", error)
			return [],[],[]
			
	def responsivity(self, v_meas, wavelength_nm, r_int=1):
		"""Convert measured voltage to optical power using wavelength-specific responsivity."""
		photocurrent = v_meas*r_int
		if wavelength_nm == 1310:
			a, b, c = 7.50196297e-04, -2.01470493e+00, 1.48709813e+03
		elif wavelength_nm == 1550:
			a, b, c = 2.61822186e-04, -7.83412220e-01, 7.13068194e+02
		else:
			raise ValueError("Wavelength outside the optimized 1310nm or 1550nm bands.")
		# Calculate 1/R using the polynomial
		inv_R = a * (wavelength_nm ** 2) + b * wavelength_nm + c
		# Power = Current * (1/R)
		power_W = photocurrent*inv_R
		return power_W

	def acq_liv(self):
		"""Performs an LIV measurement"""
		LIV_settings = { # Settings for running LIV measurements
		"current":0.35,
		"step_size":5E-4,
		"pulse_delay": 2.E-5,  # s
		"pulse_width": 0.001,  # s
		"pulse_mode": 'DC',  # i.e. "Staircase" mode
		"pl":  1310,
		}
		ktl.connect()
		c,v,pd = ktl.LIVsweep(sweepstart=0, 
							sweepstop=LIV_settings["current"],
							nsteps = int(abs(LIV_settings["current"]-0)/LIV_settings["step_size"]), 
							step_size = LIV_settings["step_size"], 
							smua_ilimit=1, 
							smua_vlimit=5, 
							pd_revbias=-5, 
							measdelay=0.00, 
							pulse_width=LIV_settings["pulse_width"], 
							nplc=0.01) 
		if LIV_settings["pl"] == 1550:
			power = [self.responsivity(i, 1550) for i in pd.magnitude]
		elif LIV_settings["pl"] == 1310:
			power = [self.responsivity(i, 1310) for i in pd.magnitude]
		self.plot_win(c, v, power)

############Moving/controlling the probe
	def read_gross_lift(self):
		"""Checks the prober's Gross height value."""
		value =  self.send_command(b'RKGM\n')
		value = int(value.split(' ')[-1])
		return value
	def read_fine_lift(self):
		"""Checks the prober's Gross height value."""
		value =  self.send_command(b'RKFM\n')
		value = int(value.split(' ')[-1])
		return value
	def read_overtravel(self):
		"""Checks the prober's overtravel value."""
		value =  self.send_command(b'RZIM\n')
		value = int(value.split(' ')[-1])
		return value
	def rel_mov(self, x_inc, y_inc):
		"""Moves the prober stage by the specified x and y increments."""
		xy = self.send_command(b'PSXY\n')
		x = float(re.findall(r"-?\d+", xy)[-2]) + x_inc
		y = float(re.findall(r"-?\d+", xy)[-1]) + y_inc
		command = f'GTXY {x},{y}\n'.encode() # go to the next  laser
		self.send_command(command)
	def gross_up(self):
		"""Send the prober command for a gross upward stage movement."""
		self.send_command(b'GUP\n')
	def gross_down(self):
		"""Send the prober command for a gross downward stage movement."""
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
	def go_fiber(self):
		"""Move the detector stage to the fiber position."""
		self.send_command(b'TSTHD 1\n')
		return
	def go_sphere(self):
		"""Move the detector stage to the integrating-sphere position."""
		self.send_command(b'TSTHD 2\n')
		return
	def align(self, bar_index):
		"""Performs touchdown for the specified bar and updates the interface with X/Y values."""
		#table names: table_bar1, table_bar2,...
		#button names: btn_align1, btn_align2,...
		self.start_jobs_btn.setStyleSheet('background-color: rgb(255, 255, 0)')
		self.start_jobs_btn.setStyleSheet('border: 2px solid red')
		self.start_jobs_btn.setText(f"Wafer{bar_index} Align")
		self.start_jobs_btn.repaint()
		self.send_command(b'LDALN\n') # Run alignment screen without focus setting
		self.wait_ser()
		th = self.send_command(b'PSTH\n') # asks for the theta value
		th = int(re.findall(r"-?\d+", th)[-1])
		getattr(self, f'table_bar{bar_index}').setItem(0, 2, QTableWidgetItem(str(th)))
		self.file_save(self.collect())
		self.reset_start_btn()

	def change_pos(self):
		"""Moves the prober to the change position."""
		self.send_command(b'LDS\n')
		print('Moving to change position!')
		return
	def fine_up(self):
		"""Send the prober command for a fine upward stage movement."""
		self.send_command(b'CUP\n')
	def fine_down(self):
		"""Send the prober command for a fine downward stage movement."""
		self.send_command(b'CDW\n')
	def vac_on(self):
		"""Turn on the prober vacuum."""
		print('Vac ON command sent')
		self.send_command(b'VAC CV,1\n')
	def vac_off(self):
		"""Turn off the prober vacuum."""
		print('Vac Off command sent')
		self.send_command(b'VAC CV,0\n')
	def check_idn(self):
		"""Checks the prober's identity by sending the GID command."""
		value =  self.send_command(b'GID\n')
		if value != '':
			return True
		else:
			return False

############Updating GUI
	def up_z_set(self):
		#print(self.read_gross_lift())
		#print(self.read_fine_lift())
		#print(self.read_overtravel())
		self.gup_display.setText(str(self.read_gross_lift())+' um')
		self.fup_display.setText(str(self.read_fine_lift())+' um')
		self.overt_display.setText(str(self.read_overtravel())+' um')
	
	def save_value(self):
		"""Saves all current values from the interface."""
		#method to save all values in interface
		print('saved!')
	def write_values(self):
		"""Load saved touchdown coordinates and measurement ranges into the interface."""
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
		"""Establishes and returns a serial connection to the prober. Changed COM5 to COM1"""
		try:
			self.ser = serial.Serial(port = 'COM1', baudrate = 38400, parity = serial.PARITY_EVEN, bytesize = serial.SEVENBITS, stopbits = serial.STOPBITS_TWO, timeout = 0.2)
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
			job_root='C:/Users/smp-user/OneDrive - Smart Photonics/Test  Measurement - Engineering/Internal Projects/Job generation'
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
		"""Update the displayed loaded-cell list from the selected cell-list CSV."""
		cell_list     =self.die_list_combo_box.currentText()
		cell_ids      = pd.read_csv(cell_list).values
		cells_loaded  = self.die_loaded_cell.currentText()
		self.liv_cells_loaded.setText(cell_ids[0:cells_loaded])

	def search_jobs(self):
		"""Retrieve traveler details and populate die job and cell-list selections."""
		try:
			work_order,prod_id,lot_id = self.run_mes_check(False)
			print(work_order,prod_id,lot_id)
			folder_path = 'C:/Users/smp-user/OneDrive - Smart Photonics/Test  Measurement - Engineering/Internal Projects/Job generation/'+work_order+'/'+prod_id+'/'+lot_id+'/'+'TM0002'
			#folder_path = 'C:/Users/MarcosDaSilvaEleoter/OneDrive - Smart Photonics/Test & Measurement/Internal Projects/Job generation/'+work_order+'/'+prod_id+'/'+lot_id+'/'+'TM0002'
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

		xy = self.send_command(b'PSXY\n')
		x = float(re.findall(r"-?\d+", xy)[-2])
		y = float(re.findall(r"-?\d+", xy)[-1])
		getattr(self, f'table_bar{bar_index}').setItem(0, 0, QTableWidgetItem(str(x)))
		getattr(self, f'table_bar{bar_index}').setItem(0, 1, QTableWidgetItem(str(y)))
		self.file_save(self.collect())
		self.reset_start_btn()

############# TOUCHDOWN METHODS
	def update_combo_box(self,combo_object, array):
		"""Adds each item once, removing duplicates already present."""
		seen = set()
		duplicates = []
		for index in range(combo_object.count()):
			item = combo_object.itemText(index)
			if item in seen:
				duplicates.append(index)
			else:
				seen.add(item)

		was_blocked = combo_object.blockSignals(True)
		for index in reversed(duplicates):
			combo_object.removeItem(index)
		combo_object.blockSignals(was_blocked)

		for item in array:
			if item not in seen:
				combo_object.addItem(item)
				seen.add(item)
	
	def select_job(self):
		"""Opens a folder dialog and populates the job combo box with available jobs."""
		#job_root='C:/Users/smp-user/OneDrive - Smart Photonics/Test  Measurement - Engineering/Internal Projects/Job generation/'
		job_root='C:/Users/HP/Smart Photonics/Engineering - Test & Measurement/Internal Projects/Job generation/'
		self.job_folder_path1 = QFileDialog.getExistingDirectory(self,("Open Batch Folder"), job_root)
		if not self.job_folder_path1:
			return
		self.jobs_combo_box.clear()
		#Fill the first combo box with Jobs available
		job_folder_selection = glob.glob(self.job_folder_path1+'/*JOB.yaml')
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
		first_td = df.iloc[0,0]
		#total_files = sum(df.sum(axis=1))
		total_files = df.sum(numeric_only=True).sum()
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
		#core_script = r"C:\Users\marco\Coding\cori.py"
		core_script = r"C:\AMS\core.py"
		#Get values from interface
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
				time.sleep(0.2)

		if self.check_repeat.isChecked():
			repetition = int(self.drop_repeat.currentText())
		else: 
			repetition = 1
		# Build job queue instead of processing immediately
		commands = []
		self.stop_requested = False
		for rep in range(repetition):
			for job, user, x_td, y_td, check_bar, start_index, end_index, prog in  zip(job_file_arr, user_name_arr, x_td_arr, y_td_arr,stat_arr, cell_index_start, cell_index_end, prog_arr):
				if check_bar:
					cmd_arr = [sys.executable, '-u',
								core_script,
								job, user, 
								str(x_td), str(y_td), 
								str(check_bar), 
								start_index, 
								end_index, 
								prog]
					commands.append(cmd_arr)
		# Start processing the job queue
		self.run_core(commands)

	def run_core(self, commands):
			"""Runs the provided list of measurement commands sequentially."""
			self.commands = commands
			self.current_index = 0
			self.start_next_command()

	def start_next_command(self):
			"""Starts the next measurement command in the sequence."""
			if self.current_index >= len(self.commands):
				print('done')
				self.reset_start_btn()
				self.gross_down()
				return
			cmd = self.commands[self.current_index]
			
			###setting the state of the button
			self.start_index = cmd[8]
			self.end_index = cmd[9]
			prog = cmd[10]
			self.data_folder = 'D:\\PRODUCTION\\data\\'+self.cust_id.text()+'\\'+'\\'+self.batch_id.text()+'\\'+self.wafer_id.text()
			try:
				self.total_meas = self.get_total_meas(
					start_index=self.start_index,
					end_index=self.end_index,
					job_file=cmd[3],
				)
			except (OSError, ValueError, yaml.YAMLError, pd.errors.ParserError) as error:
				print(f"Could not count measurements for {cmd[3]}: {error}")
				self.total_meas = 0
			self.files_before_starting = len(glob.glob(self.data_folder+'/*.txt'))
			self.start_jobs_btn.setStyleSheet('background-color: rgb(255, 255, 0)')
			self.start_jobs_btn.setText(f"{prog} in progress")
			self.start_jobs_btn.repaint()
			##
			self.thread = QThread()
			self.worker = Ui.Worker(cmd, self)
			self.worker.moveToThread(self.thread)
			self.thread.started.connect(self.worker.run)
			self.worker.output_ready.connect(self.display_subprocess_output)
			self.worker.finished.connect(self.handle_result)
			self.worker.finished.connect(self.thread.quit)
			self.worker.finished.connect(self.worker.deleteLater)
			self.thread.finished.connect(self.thread.deleteLater)
			#self.thread.finished.connect(self.start_next_command)
			self.thread.finished.connect(self.on_thread_finished)
			self.thread.start()

	def on_thread_finished(self):
		"""Clear the completed worker thread and launch the next queued measurement."""
		self.thread = None
		self.start_next_command()

	def handle_result(self, result):
			"""Handles the result after a measurement command finishes."""
			print('Process finished.', result)
			self.current_index +=1

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
		"""Generate manual LIV job YAML and placeholder cell-list CSV files for selected wafers."""
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
			root_path = 'C:/Users/smp-user/OneDrive - Smart Photonics/Test  Measurement - Engineering/Internal Projects/Job generation'
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
		"""Retrieve traveler data from MES and optionally update the LIV form.

		When ``update_gui`` is false, return the work order, product ID, and lot ID.
		"""
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
			lot_id = traveler_info['LotID']
			wafers = traveler_info['Wafers']
			prod_id = traveler_info['RequestedPart']
			curr_step = traveler_info['CurrentStep']
			wafers_arr = [wafers[i]['WaferId'] for i, key in enumerate(wafers)]
			work_order = traveler_info['WorkOrder']
			match = re.search(r'BLN03|PNC15|DFB01|DFB03|DFB04|BLN01|PNC21|PNC06|MPO06|MPS25|MPC057|OLSG2|T1|OMP05|MAC01|AOT01|MAC02|RSL01|WGM01', prod_id)
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
			#QMessageBox.about(self, "Error", "Failed to retrieve traveler information")

		####Methods for MLIV meas
	def get_temp(self):
		"""Read the TEC temperature and display it in the interface."""
		tec_t = tec.Tec()          # TEC
		tec_t.connect(port="COM4")
		temp = tec_t.get_temperature()
		self.temp_tec.setText(str(temp) +  '°C')
		tec_t.release()

	def chunker(self, seq, size):
		"""Yield consecutive slices of ``seq`` containing at most ``size`` items."""
		return(seq[pos:pos+size] for pos in range(0, len(seq),size))
	
	def start_jobs_in_thread(self):
		"""Run the selected measurement-tab handler from a worker thread."""
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
		"""Handle completion of the threaded job handler and stop its thread."""
		print(msg)
		self.worker_thread.quit()
		self.worker_thread.wait()
	def start_jobs(self):
		"""Dispatch job execution to the handler for the currently selected tab."""
		###########
		#Indexes of the tables
		#0: Bar measurements
		#1: Dies measurements
		#2: SPC
		current_tab_index = self.meas_tab.currentIndex()
		if current_tab_index == 0:
			self.bar_start()
		elif current_tab_index == 1:
			self.die_start()
		elif current_tab_index == 2:
			self.spc_start()
	def reset_start_btn(self):
		"""Restore the start button to its idle label and styling."""
		self.start_jobs_btn.setStyleSheet('background-color: rgb(85, 255, 127)')
		self.start_jobs_btn.setText("START")
		self.start_jobs_btn.repaint()
	def gen_bars_job(self):
		"""Run the selected bar job generator and stream its output to the UI."""
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
			cmd = [
				sys.executable,
				'-u',
				info_arr[0],
				info_arr[1],
				repr(info_arr[2]),
				info_arr[3],
				repr(info_arr[4])
			]
			if self.jobgen_thread is not None and self.jobgen_thread.isRunning():
				QMessageBox.about(self, "Job generation", "Job file generation is already running.")
				return
			self.jobgen_thread = QThread(self)
			self.jobgen_worker = Ui.Worker(cmd, self)
			self.jobgen_worker.moveToThread(self.jobgen_thread)
			self.jobgen_thread.started.connect(self.jobgen_worker.run)
			self.jobgen_worker.output_ready.connect(self.display_subprocess_output)
			self.jobgen_worker.finished.connect(self.on_jobgen_finished)
			self.jobgen_worker.finished.connect(self.jobgen_thread.quit)
			self.jobgen_worker.finished.connect(self.jobgen_worker.deleteLater)
			self.jobgen_thread.finished.connect(self.jobgen_thread.deleteLater)
			self.jobgen_thread.finished.connect(self.on_jobgen_thread_finished)
			self.jobgen_thread.start()
		except Exception as e:
			print(e)
			QMessageBox.about(self, "Error", "Failed to start job file generation script:\n" + str(e))

	def on_jobgen_finished(self, result):
		"""Report the job-generation subprocess result."""
		print("Job file generation finished.", result)

	def on_jobgen_thread_finished(self):
		"""Release references to the completed job-generation thread and worker."""
		self.jobgen_thread = None
		self.jobgen_worker = None
	def refresh_bars_combo_box(self):
		"""Reload available bar job-generator scripts and CCF files into their selectors."""
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

	def set_graph(self, titulo, eixo_x, eixo_y):
		"""Configure the active plot title, axis labels, grid, and legend."""
		# THESE PARAMETERS ARE FOR RESIZING AND MOVING THE POSITION OF THE LEGEND BOX
		# I INCREASED X-SIZE AND Y-OFFSET
		self.p1.addLegend(size=(110, 0) ,offset=(10, 10))
		self.p1.setTitle('<font size="2">Active Power</font>') #,**titleStyle)
		self.a = self.p1.getAxis('bottom')
		self.a.showValues='false'
		self.a = self.p1.getAxis('bottom')
		self.p1.showAxis('left')
		self.a = self.p1.getAxis('left')
		self.p1.showAxis('right')
		self.a = self.p1.getAxis('right')
		self.p1.showLabel('left', show=True)
		self.p1.showLabel('right', show=True)
		self.p1.showGrid(x=True, y=True, alpha=0.2)
		self.p1.getAxis('bottom').setTickSpacing(major=50,minor=25)
		#self.p1.getAxis('left').setTickSpacing(major=0.2,minor=0.1)
		
		titleStyle = {'color': '#000', 'size': '18pt'}
		self.p1.setTitle(titulo, **titleStyle)
		# SET AND CHANGE THE FONT SIZE AND COLOR OF THE PLOT AXIS LABEL
		labelStyle = {'color': '#000', 'font-size': '16px'}
		self.p1.setLabel('bottom', eixo_x, **labelStyle)
		self.p1.setLabel('left', eixo_y, **labelStyle)
		self.p1.setLabel('top',)
	def clear_plot(self):
		"""Clear the plot and remove any secondary-axis curve."""
		self.plotter.clear()
		self.p1.clear()
		if hasattr(self, 'plot2') and self.plot2 is not None:
			self.p2.removeItem(self.plot2)
			self.plot2 = None
	def updateViews(self):
		"""Synchronize the secondary plot view geometry with the primary view."""
		self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
		self.p2.linkedViewChanged(self.p1.vb, self.p2.XAxis)
	def stop_execution(self):
		"""Requests the worker to stop execution of the current measurement command."""
		print('Stop requested!')
		if self.worker:
			self.worker.stop()

	def closeEvent(self, event):
		"""Handle window closure and accept the close event after cleanup."""
		print("Window closed")
		try:
			self.end()
		except:
			pass
		event.accept()

def main():
	"""Create the Qt application, show the main window, and run its event loop."""
	app = QtWidgets.QApplication(sys.argv)
	window = Ui()
	window.show()
	sys.exit(app.exec_())

if __name__ == '__main__': # only executes the below code if it python has run it as the main
	main()
