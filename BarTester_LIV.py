# -*- coding: utf-8 -*-
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
import argparse
openEPDA_version = openepda.__version__
t_start = time.time()

#read command line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description='Bar Tester LIV Script')
    parser.add_argument('--cust', type=str, help='Customer ID')
    parser.add_argument('--user', type=str, help='User ID with 3 letters')
    parser.add_argument('--lot', type=str, help='Lot ID')
    parser.add_argument('--prod', type=str, help='Product ID')
    parser.add_argument('--wafer', type=str, help='Wafer ID')
    parser.add_argument('--pl', type=str, help='Wavelength')
    parser.add_argument('--temperatures', type=str, help='Array  with temperatures')
    parser.add_argument('--liv_bol', type=str, help='LIV boolean')
    parser.add_argument('--spec_bol', type=str, help='Spectrum boolean')
    parser.add_argument('--i_soa', type=float, help='Spectrum I_SOA')
    parser.add_argument('--cell_type', type=str, help='Cell type')  
    parser.add_argument('--combi_mode', type=str, help='Combi mode')
    parser.add_argument('--cells', type=str, help='Cells ID list to measure ')
    return parser.parse_args()

args = parse_arguments()
customer_id = args.cust
operator = args.user
lot_id = args.lot
product_id = args.prod
wafer_id = args.wafer
pl = args.pl
temp_set = args.temperatures
liv_bol = args.liv_bol
spec_bol = args.spec_bol
cell_type = args.cell_type
combi_mode = args.combi_mode
cells = args.cells
i_soa = args.i_soa

#### Pre-defined settings ####
config_file_folder = "C:\\Users\\HP\\Smart Photonics\\Engineering - Test & Measurement\\Internal Projects\\Job generation\\JobGeneratorTemplates\\Bar Tester LIV" # folder from which upload the config files for the zip file
# make a folder for storing raw data
path = f'D:\PRODUCTION\data\{cust}\manual_BT_liv\{prod}_{lot}'
if not os.path.isdir(path):
    os.makedirs(path)
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

# Ask for operator ID
operator = input("Operator ID: ")
while len(operator) != 3:
    print(f"ERROR! Operator ID must be a 3-character string, but the string {operator} has been entered. Please provide a correct Operator ID") 
    operator = input("Re-enter Operator ID: ")
    
### Get information out of the JOB file, ask the Operator for the missing ones ###
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
print(f"      LIV measurements: {liv_bol}")
print(f" Spectrum measurements: {spec_bol}")
print("")

# Connect the OSA, if needed
if spec_bol:
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
       
        cell_id = f"{cell_type} {cell_id}"
        
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
            if liv_bol: # Execute LIV measurements

                
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
                    
                    t='go'                
                    if t == 'kill':
                        kill = 1
                        break
                    
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