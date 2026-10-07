# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 06:56:48 2026

@author: smp-user
"""

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
from load_sample_V2  import *
from align_sample_V2 import AlignSample
sys.path.insert(1, 'C:\\AMS')
try:
	#from smu.keithley2520 import Keithley2520 # Tool is broken
	from smu.keithley2602B import Keithley2602B
	ktl= Keithley2602B()
	#import pyOSA 
	from tec import tec
	import logging
	logger=logging.getLogger('test.AmsCore')
	from collections.abc import MutableMapping
	import telegram
	import measurement_handler as measurement_handler
	from readers.readers import JOBReader
	
	from measurement_plan_maker.meas_plan_maker import MeasPlan
	print('1')
	
	print('2')
	from utils.identify import Identify
	from utils.misc  import generate_session_ID, get_git_commit_id, get_probes_folder, get_jobs_folder, get_data_folder,get_batch_data_folder, get_backup_folder
	from utils.utils import boolean_operation, select_bar
	
	#Real-time analysis tools
	from realtime_analysis.quick_analysis import QuickAnalysis
	import openepda
	openEPDA_version = openepda.__version__
	from collections  import OrderedDict
	import mes_check as MesCom
	from Yokogawa import AQ6370D as osa
	start_time = time.time()
	from equipment import Equipment
	
except Exception as err:
	print('######LIB NOT LOADED########')
	print(err)
	print('##############')