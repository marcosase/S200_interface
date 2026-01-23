# -*- coding: utf-8 -*-
"""
Created on Wed Jun,19 2024

Script for executing LIV and/or Spectral measurements on T1 cells (HS28 platform)

@author: AntonioBonardi

"""

from smu.keithley2520 import Keithley2520
#from osa import Osa203c as OSA
import pyOSA
import yaml
import openepda
import datetime
import matplotlib.pyplot as plt
import os
import time
import tkinter as tk
from tqdm import tqdm
import pandas as pd
import numpy as np
from tkinter import filedialog
from zipfile import ZipFile 

from tec import tec
import wentworth.prober as prober
openEPDA_version = openepda.__version__
t_start = time.time()
#### Pre-defined settings ####
config_file_folder = "C:\\Users\\HP\\Smart Photonics\\Engineering - Test & Measurement\\Internal Projects\\Job generation\\JobGeneratorTemplates\\Bar Tester LIV" # folder from which upload the config files for the zip file

current_dict = {  # Max current value for each FP laser in T1 cell, from Northern side to Southern one
    "FP1500": 0.120,
    "FP1000": 0.120,
    "FP500": 0.120,
    "FP300": 0.090,  
    }

current_dict_inv = {  # Max current value for each FP laser in T1 cell, from Northern side to Southern one
    "FP300": 0.090,
    "FP500": 0.120,
    "FP1000": 0.120,
    "FP1500": 0.090,  
    }

###New current_dic tadded for DBR testing, Marcos 14/08/2024
current_dict2 = {
     "DBRB12":0.120,
     "ID_DBR9":0.120,
     "ID_DBR11":0.120,
     "ID_DBR8":0.120,
     "ID_DBR10":0.120,
     "ID_DBR7":0.120,
     "DBRB6":0.120,
     "ID_DBR3":0.120,
     "ID_DBRB5":0.120,
     "ID_DBR2":0.120,
     "ID_DBRB4":0.120,
     "ID_DBR1":0.120
     }
current_lol = {
     "loli_00":0.120,
     "loli_01":0.120,
     "loli_02":0.120,
     "loli_03":0.120,
     "loli_04":0.120,
     "loli_05":0.120
     }
current_dict_tiger = {  # Max current value for each FP laser in T1 cell, from Northern side to Southern one
    "FP300": 0.144,
    "FP500": 0.24,
    "FP1000": 0.48,
    "FP1500": 0.5, 
    }

# #####Dict for testing the laser bars
# current_dict = {
# "36 P12B#01-09-B":0.120,
# "36 P12B#01-08-B":0.120,
# "36 P12B#01-07-B":0.120,
# "36 P12B#01-06-B":0.120,
# "36 P12B#01-05-B":0.120,
# "36 P12B#01-04-B":0.120,
# "36 P12B#01-03-B":0.120,
# "36 P12B#01-02-B":0.120,
# "36 P12B#01-01-B":0.120,
# "36 P12B#01-00-B":0.120
#     }


#####Dict for testing the laser bars
# current_dict = {
# "ID-DBR9":0.120,
# "ID-DBR8":0.120,
# "ID-DBR7":0.120,
# "ID-DBR3":0.120,
# "ID-DBR2":0.120,
# "ID-DBR1":0.120
#      }


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
##############
#next_wg = 250 # um, distance on y-axis between consecutive FP lasers 
##############

# #next_wvg changed for the DBr lasers testing
next_wg2 = 325 # nm, distance on y-axis between consecutive DBR lasers 

# next_wg = 300 # nm, distance on y-axis between consecutive FP lasers 
    
#### End of predefined settings ####

# Ask for operator ID
operator = input("Operator ID: ")
while len(operator) != 3:
    print(f"ERROR! Operator ID must be a 3-character string, but the string {operator} has been entered. Please provide a correct Operator ID") 
    operator = input("Re-enter Operator ID: ")


##### Collect measurement and sample information #####
### Ask user for JOB file ###
job_file_path = ""
answer = input("Is a config file available? [Y/N]")
if answer.upper() == "Y" or answer.upper() == "YES":
    root = tk.Tk()
    job_file_path = filedialog.askopenfilename(
                                               title = "Select JOB file"
                                               )
    
    root.destroy()
    del root
#################
cells_answer = input("Is CellID file available? [Y/N]")
if cells_answer.upper() == "Y" or cells_answer.upper() == "YES":
    root = tk.Tk()
    cells_file_path = filedialog.askopenfilename(
                                               title = "Select cells file"
                                               ) 
    
    root.destroy()
    del root

#################    

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
#cell_type = job_dict.get("cell_type", "T1") ##COMMENTED BY MARCOS
cell_type = job_dict.get("cell_type", "T3")
combi_mode = job_dict.get("combi_mode",None)
cell_ids = job_dict.get("cell_ids", None)

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

# Set the SOA current at which to perform the spectral measurement(s)
if spectrum:
    if not i_soa:
        i_soa = input("SOA current (relative to max allowed SOA current) for spectral measurements (if multiple value, use a comma to separate them) [0-1]: ")

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
    
if cells_answer.upper() == "Y" or cells_answer.upper() == "YES":
    print('####')
    cell_loaded = int(input('How many T1 cells are loaded in the chuck?: '))
    #num_meas = int(input(f'What is the measurement number on batch {lot_id} wafer {wafer_id}?: '))
    
    df = pd.read_csv(cells_file_path, header=None)
    size = df.shape[0]
    new_size = -1*(size - cell_loaded)
    cell_id_list = df[0].values.tolist()[0:cell_loaded]
    n_cells = len(cell_id_list)
    df = df[new_size:]  
    df.to_csv(cells_file_path, index=False, header=False)
        
else:
    # Ask how many cells are loaded on the chuck
    n_cells = int(input("Enter the amount of T1 cells loaded on the chuck: "))
    answer = "N"
    while n_cells > 7 and answer=="N" :
        print(f"WARNING! It has been entered that {n_cells} are loaded on the chuck. This is unlikely given the available space")
        answer = input("Please confirm that {n_cells} are present on the chuck: [Y/N]")
        if answer.upper() != "Y" or answer.upper() != "YES":
            answer == "N"
            n_cells = input("Enter the amount of T1 cells loaded on the chuck: ")
            
    
    # Ask user if he wants to provide cell ID before starting
    while True:
        print("Enter the ID of cells loaded on the chuck (use a comma to separate different entries)")
        cell_id_list = input("If left empty, ID of individual cell will be asked during the measurement loop: ")
        if cell_id_list:
            cell_id_list = cell_id_list.replace(" ","") # remove empty characters, if any
            cell_id_list = cell_id_list.split(",") # split the string in an actual list
            if len(cell_id_list)==n_cells:
                break
            else:
                print("WARNING! The number of entered cell ID does not match the amount of cell loaded on the chuck")
        else:
            break

### Recap before moving to performing measurement loop ###
print("===================================================================")
print("")
print("The following run info was provided:")
print(f"             Cell type: {cell_type}")
print(f"           Operator ID: {operator}")
print(f"           Customer ID: {customer_id}")
print(f"            Product ID: {product_id}")
print(f"                Lot ID: {lot_id}")
print(f"              Wafer ID: {wafer_id}")
print(f"           Selected PL: {pl}")
print(f"     Chuck Temperature: {temp_set}")
print(f"  # Cells on the chuck: {n_cells}")
if cell_id_list:
    print(f" ID Cells on the chuck: {', '.join(cell_id_list)}")
print(f"      LIV measurements: {liv}")
print(f" Spectrum measurements: {spectrum}")
print("")

#if input("Press enter to confirm, or N to cancel: ") != "":
#    print()
#    print()
#    print("          ┻━┻︵ \(°□°)/ ︵ ┻━┻          ")
#    print()
#    raise SystemExit("Job specifics were incorrect, exiting program")

# make a folder for storing raw data
path = f'D:\PRODUCTION\data\{customer_id}\manual_BT_liv\{product_id}_{lot_id}'
if not os.path.isdir(path):
    os.makedirs(path)

##### End of sample information collection and subsequent actions #####

#### Connect the instruments ####
tec = tec.Tec()          # TEC
tec.connect(port="COM4")

ktl = Keithley2520()    # SMU
ktl.connect()

p = prober.Prober()     # Bar Tester
p.connect()
p.set_light(on=True)
p.move_to_manual_load_position()
p.move_testhead(position='sphere')

# Connect the OSA, if needed
if spectrum:
    o = pyOSA.initialize()
    resolution = Spectrum_settings["resolution"]
    sensitivity = Spectrum_settings["sensitivity"]
    window_width = Spectrum_settings.get("spectrum_window")
    start_spectrum = pl - window_width / 2
    end_spectrum = pl + window_width / 2
    o.setup(resolution=resolution, sensitivity=sensitivity, autogain=True) 

### Set the chuck temperature ###
print("Connecting Tec and setting temperature to {}".format(temp_set))
#tec.set_temperature(temp_set)
tec._set_enable()
print("Waiting for temperature to stabilise...")
#tec._set(T_set=temp_set, T_win=0.5)
#### End of connecting instruments (OSA is connected later, if needed) ####

### Load the samples ###
print(f"Are {cell_id_list} cells loaded on the chuck?")
if input("Press enter to confirm, or type \'kill\' to exit procedure: ") == "kill":
    p.release()
    tec.release()
    ktl.release()
    o.close()
    raise SystemExit("User canceled procedure, exiting program")
p.move_to_probing_zone_center()

##### Start the acquisition run  #####   
# go to default position (next to integrating sphere)
p.go_to_xy('002500', '100700')
     
cells_list = []     
session_start = str(datetime.datetime.now()).replace(' ', '_')
measurement_counter = 0
kill = 0
list_rawdata_files = []
p.run_probe_height_screen()
x_td = p.get_chuck_x()
y_td = p.get_chuck_y()

temp_arr = temp_set
print(temp_arr)
print('########################################')
time.sleep(10)

if tec.get_temperature() > 50:
    temp_arr = np.flip(temp_set)

for temp_val in temp_arr:
    tec._set(T_set = temp_val, T_win = 0.5)
    p.go_to_xy(x_td, y_td)
    time.sleep(0.5)
    delta_t = abs(tec.get_temperature() - temp_val)
    
    while delta_t > 1:
        print('Temp. not stable!', tec.get_temperature() - temp_val)
        time.sleep(1)
        delta_t = abs(tec.get_temperature() - temp_val)
        print(delta_t)
    print(delta_t)
    #input('\nPress enter when done:')
        
    for idx in tqdm(range(n_cells)): # For loop on individual cells
        # acquisition is stopped if "Kill" command has been sent
        if kill == 1: 
             break
        # Go to the idx-th cell  
        print('Press the RIGHT red button to toggle to XY')
        if idx == 0:
            print('Use the joystick to go to first cell')
        else:
            print('Use the joystick to go to the next cell')
    
        # if cell ID is not already provided, ask for cell ID, then do consistency checks
        if cell_id_list:
            try:
                cell_id = cell_id_list[idx]
                cell_id = cell_id.split('\t')[0]
            except:
                cell_id = cell_id_list[idx]
            
        else:
            print('Then press the RIGHT red button again to toggle to Z for focus the cell, and read the cell ID')
            cell_id = input("Cell ID: ")
    
        nok = True
        #while nok:
        #    while cell_id in cells_list:
        #        print(f"ERROR! Cell ID must be unique. Entered value {cell_id} has been already assigned")
        #        cell_id = input("Re-enter Cell ID: ")
        #        
        #    while not cell_id.startswith(str(cell_type)+" "):
        #        print(f"WARNING! Cell ID must start with the give cell type, i.e. \'{cell_type}\', and have a whitespace after it")
        #        #answer = input(f"Cell ID will be converted to {cell_type} {cell_id}. Do you accept the proposed new name? [Y/N]") 
        #        answer = 'Y'
        #        if answer.upper()=="Y" or answer.upper()=="YES":
        cell_id = f"{cell_type} {cell_id}"
        #        else:
        #            answer = input("Do you want to provide a new cell ID? [Y/N] If not, entered one will be kept")
        #            if answer.upper()=="Y" or answer.upper()=="YES":
        #                cell_id = input("Re-enter Cell ID: ")
        #            elif not cell_id in cells_list:
        #                nok=False
        
        if cell_id.startswith(str(cell_type)+" ") and not cell_id in cells_list:
                 nok = False
                
        cells_list.append(cell_id)
        if cell_type=='TD1':
            current_dict = current_dict_inv
        elif cell_type=='T3':
            current_dict = current_lol
        elif cell_type=='T1_tiger':
            current_dict=current_dict_tiger
        else:
            current_dict = current_dict
            
        for device_idx, (device_id, max_current) in enumerate(current_dict.items()): # for loop on individual FP lasers in each cell
            if kill == 1: # acquisition is stopped if "Kill" command has been sent
                 break
            print('{} {} {} {}'.format(product_id, lot_id, cell_id, device_id))
            print('')
            if device_idx==0: # adjust probe height for first laser of every cell
                print('Press the RIGHT red button to toggle to XY')
                print(
                    f'Use the joystick to go to cell {cell_id}, device {device_id}')
                if idx==0:
                    print('Align probes in X-direction manually using the screw-micrometer')
                    print('')
                print('Press the RIGHT red button to toggle to Z')
                print('Move chuck up UNTIL the first Edge Sensor Opens.')
                print('')
                ########
                #p.run_probe_height_screen()
                #input('\nPress enter when done:')
            else:                
                print('Aligning with next device...')
                print('')
                #p.set_light(on=True)
                p.move_chuck_fine_down()
                #p.run_probe_height_screen()
                # overrules gross up from initial alignment to allow microscope focus
                # p._write('WKGM 8480') # useless?
                # p.move_chuck_gross_up()  # should be 8480 for focus
                if device_id=='ID_DBR7' and cell_type=='T3':
                    next_wg=350
                elif cell_type =='T3':
                    next_wg=620
                elif cell_type=='T1':
                    next_wg=250
                elif cell_type=='TD1':
                    next_wg=250
                
                p.go_to_xy(p.get_chuck_x(), (p.get_chuck_y() + next_wg))
                print('')
                print(
                    f'Align probes in X-direction with {device_id}-pad manually using the screw-micrometer')
                print('')
                #input('Press <Enter> to confirm the alignment') #COMMENTED BY MARCOS
            print('\n setting temperature \n')
            temperature = tec.get_temperature()
            print('t={}'.format(temperature))
            #t = input('\n Start measurement?')
            p.move_chuck_fine_up()
            if liv: # Execute LIV measurements
              
                #while True:
                p.move_testhead(position='sphere')
                c, v, pd = ktl.LIVpulsedsweep(sweepstart=0,
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
                power = [-c * resp for c in pd.magnitude]
                fig, ax1 = plt.subplots()
                ax1.plot(c[5:], v[5:], "b") # skip first data point (not reliable)
                # ax1.set_ylim([0,5])
                ax1.set_ylabel("Voltage [V]", color="b")
                ax1.set_xlabel("Current [A]")
                # ax1.set_ylim([0,2])
                ax2 = ax1.twinx()
                ax2.plot(c[5:], power[5:], "r")
                ax2.set_ylabel("Power in [W]", color="r")
                plt.grid(True)
                plt.draw()
                plt.title(f'{cell_id} - {device_id} - LIV')
                plt.show()
                #t = input(
                #    "OK? (enter for ok, type 'kill' to exit loop, anything else to retry)") #COMMENTED BY MARCOS
                plt.close()
                t='go'                
                if t == 'kill':
                    kill = 1
                    break
                #elif t: # anything not kill
                #    print("Measurement discarded.. retrying...")
                #    t =""
                else:  # press enter, save data, close plot
                    measurement_plan = 'LIV_{}'.format(device_id) + '_' + str(round(temp_val)) + 'C'
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
                        'OperatorID': operator,
                        'PL_wavelength': pl,
                        'MeasurementSession': 'TM0002_{}'.format(session_start),
                        'Session_start_time': session_start,
                        'SetTemperature': int(temp_val),
                        'Wafer': wafer_id,
                        'Current LD, [A]': c.magnitude,
                        'Voltage LD, [V]': v.magnitude,
                        'Photocurrent PD, [A]': pd.magnitude,
                        'Power PD, [W]': power
                        
                    }
                    w = openepda.OpenEpdaDataDumper()
                    with open(os.path.join(path, fname), 'w', newline="\n") as f:
                        w.write(f, **data)
                    list_rawdata_files.append(os.path.join(path, fname))    
                    measurement_counter += 1
                                     
                
                
                if combi_mode:
                    print('#################################')
                    print('Starting pulsed mode measurement')
                    print('#################################')
                    c, v, pd = ktl.LIVpulsedsweep(sweepstart=0,
                                                  sweepstop=max_current*3,
                                                  step_size=LIV_settings["step_size"],
                                                  smua_ilimit=0.5,  # not used, limit is internally calculated for best performance
                                                  smua_vlimit=5,
                                                  pulse_delay=LIV_settings["pulse_delay"],
                                                  pulse_width=LIV_settings["pulse_width"],
                                                  pulse_mode="PULS",
                                                  )
                            
                    if pl == 1310:
                        resp = LIV_settings["resp_at_1310"]
                    if pl == 1550:
                        resp = LIV_settings["resp_at_1550"]
                    power = [-c * resp for c in pd.magnitude]
                    fig, ax1 = plt.subplots()
                    ax1.plot(c[5:], v[5:], "b") # skip first data point (not reliable)
                    # ax1.set_ylim([0,5])
                    ax1.set_ylabel("Voltage [V]", color="b")
                    ax1.set_xlabel("Current [A]")
                    # ax1.set_ylim([0,2])
                    ax2 = ax1.twinx()
                    ax2.plot(c[5:], power[5:], "r")
                    ax2.set_ylabel("Power in [W]", color="r")
                    plt.grid(True)
                    plt.draw()
                    plt.title(f'Pulsed {cell_id} - {device_id} - LIV')
                    plt.show()
                    #t = input(
                    #    "OK? (enter for ok, type 'kill' to exit loop, anything else to retry)") #COMMENTED BY MARCOS
                    plt.close()
                    t='go'                
                    if t == 'kill':
                        kill = 1
                        break
                    #elif t: # anything not kill
                    #    print("Measurement discarded.. retrying...")
                    #    t =""
                    else:  # press enter, save data, close plot
                        measurement_plan = 'LIV_{}'.format(device_id) + '_' + str(round(temperature)) + 'C'
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
                            'Mode': "Pulsed",
                            'ObservationID': measurement_counter,
                            'OperatorID': operator,
                            'PL_wavelength': pl,
                            'MeasurementSession': 'TM0002_{}'.format(session_start),
                            'Session_start_time': session_start,
                            'SetTemperature': int(temp_val),
                            'Wafer': wafer_id,
                            'Current LD, [A]': c.magnitude,
                            'Voltage LD, [V]': v.magnitude,
                            'Photocurrent PD, [A]': pd.magnitude,
                            'Power PD, [W]': power
                        }
                        w = openepda.OpenEpdaDataDumper()
                        with open(os.path.join(path, fname), 'w', newline="\n") as f:
                            w.write(f, **data)
                        list_rawdata_files.append(os.path.join(path, fname))    
                        break
                    break
            if spectrum: # Execute Spectral measurements
                p.move_testhead(position='fiber')
                for soa_current in i_soa:
                    while True:
                        spec_current = max_current * soa_current  # sets used current as a factor of max LIV currents
                        ktl.reset()
                        ktl.set_current(1, spec_current)
                        ktl.set_channel_state(1, 'on')
                                                               
                        acquisitions = o.acquire(number_of_acquisitions=1)
                        acquisition = acquisitions[-1]
                        spectrum = acquisition["spectrum"]
                        wavelength = spectrum.get_x()
                        power = spectrum.get_y()
                        peak = spectrum.y_max
                        peak_index = power.index(peak)
                        
                        ktl.set_channel_state(1, 'off')
                        fig, ax1 = plt.subplots()
                        ax1.plot(wavelength[peak_index-500:peak_index+500], power[peak_index-500:peak_index+500], "b")
                        ax1.set_ylabel("Power [W]", color="b")
                        ax1.set_xlabel("Wavelength [nm]")
                        plt.draw()
                        plt.grid(True)
                        plt.title(
                            f'{cell_id} - {device_id} - Spectrum at {round(spec_current,4)}A')
                        plt.show()
                        t = ''
                        #t = input(
                        #    "OK? (enter for ok, type 'kill' to exit loop, anything else to retry)")
                        plt.close()
                        if t == 'kill':
                            kill = 1
                            break
                        elif not t:  # press enter, save data, close plot
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
                                'OperatorID': operator,
                                'PL_wavelength': pl,
                                'MeasurementSession': 'TM0002_{}'.format(session_start),
                                'Session_start_time': session_start,
                                'SetTemperature': int(temp_val),
                                'Wafer': wafer_id,
                                'Sourcing_current [A]': round(spec_current, 4),
                                'Wavelength, [nm]': wavelength,
                                'Power, [W]': power
                            }
                            w = openepda.OpenEpdaDataDumper()
                            with open(os.path.join(path, fname), 'w', newline="\n") as f:
                                w.write(f, **data)
                            list_rawdata_files.append(os.path.join(path, fname))    
                            measurement_counter += 1
                            break
                    if kill: break # interrupt the for loop if "Kill" command
            if device_idx==3 and (cell_type=='T1' or cell_type=='TD1'):
                p.move_chuck_fine_down()
                p.go_to_xy(p.get_chuck_x(), (p.get_chuck_y() + 3255)) 
                p.set_light(on=True)
                #p.run_probe_height_screen()
                               

######## Ending the measurement #######
### Return BT to load position and disconnect tools ###
print('returning chuck to loading position and releasing equipment')
p.set_light(on=False)
p.move_chuck_fine_down()
p.move_chuck_gross_down()
p.move_to_manual_load_position()
p.release()
tec.release()
ktl.release()
try:
    o.release()
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
            
        # Add the config files which are necessary for the Automated DE
        amf = os.path.join(config_file_folder, amf_filename)
        mmf = os.path.join(config_file_folder, "BT_LIV_dummy_MMF.csv")
        ccf = os.path.join(config_file_folder, "BT_LIV_dummy_CCF.csv")
        if job_file_path:
            job = job_file_path
        else:
            job = os.path.join(config_file_folder, "Customer_Product_Wafer_ManualLIV_JOB.yaml")
            
        for config_file in [amf, mmf, ccf, job]:
            zip_fname = os.path.join('config_files',os.path.split(config_file)[1]) # name of zipped config file inside the zip folder
            zipObj.write(config_file,arcname=zip_fname)
            
    
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
try:
    df.to_csv(cells_file_path, index=False, header=False)
except:
    pass
t_finish = time.time()
time_meas = (t_finish - t_start)/60
print('**************************************')
print(f'Meas time: {time_meas} min')
print('**************************************')