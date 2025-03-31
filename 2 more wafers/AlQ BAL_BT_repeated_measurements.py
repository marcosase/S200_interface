# -*- coding: utf-8 -*-

import yaml
import sys
import numpy as np
sys.path.insert(0, '../../../..')
import MDF_library as mdf
import pandas as pd
from AMF_library import analysis_dict_v2 as ad
import parameter_names as pn
import pandas as pd
sort=False
yaml.Dumper.ignore_aliases = lambda *args : True
import device_area
# %% Settings

mdf_version='1.0.0'

pc = 'SMP-NB145'
author = 'JNP'
email = 'joep.nieuwdorp@smartphotonics.nl'

job_version='1.0.3'

customer='PM-SUB-104300'

run_info=[
    ['PNC20'  ,'24D72','P8536 003 FB'],
    ['PNC20'  ,'24D72','P8536 018 FB'],
    ]

CCF_filepath='PM-SUB-104300_PNC20_CCF_bars_v4.csv'

#LIV settings
osa_auto_gain='True'             #Bool
osa_resolution=1                 #range, which is low and which is high?
osa_sensitivity=0                #range?
soa_compliance_voltage=5         #V
pulse_settings=[
    [20e-6,20e-4,'PULS'],        #min pulse width in pulse mode
    [5e-3,20e-6,'DC'],           #default LIV setting
    ]

device_current = 0

ccf = pd.read_csv(CCF_filepath)

cell_types = ["FPI"]
# sorted(list(set(ccf.CellType.tolist())))


temperatures=[20, 40, 55, 80] #degC
# repetitions = ["none"] # repeated measurement ('burn-in' effect)

current_density=12000
stepsize=1e-4                    #A
PL=1550                          #nm
ascending=False                  #For EF reverse MMF. CCF must be reversed as well!
wavelength_span=200              #nm
spectrum_current=0.300 # it was 0.100 #TODO:define it based on device ID (needs to be done subthreshold)

for lot,product,wafer in run_info: 
     
    
     # %% JOB

     filename_format='{}_{}_{}'.format(customer, lot, wafer)
     filename_format_ccf='{}_{}'.format(customer, lot)
     
     #%% AMF dict aanmaken
     amf={}
     vcol='V_soa, V'
     acol='I_soa, A'
     pdcol='P_PD, W'
 
     wvl_col="Wavelength, nm"
     power_col="Power, mW"
     
     # %% JOB
     code=mdf.info_v2(pc=pc, author=author, 
               email=email, job_version=job_version,
               )
     final_job={}
     final_job.update(code)
     code=mdf.batch_information_v3(wafer=wafer,
                                   customer=customer,
                                   product=product,
                                   lot=lot,
                                   batch=lot
                                   )
     final_job.update(code)
     
     code=mdf.job_acquisition_settings(
         die_wise=True, #one meas per die, next die. True=all measurements on one die
         sample_type='bar',
         save_shell_output=False,
         edf_filename='C:\\PRODUCTION\\edf\\bt_with_2520_v2_EDF.yaml',
         amf_filename=f'{filename_format}_AMF.yaml',
         mdf_filename=f'{filename_format}_MDF.yaml',
         ccf_filename=CCF_filepath,
         mmf_filename=f'{filename_format}_MMF.csv',
         probecard_filepath='C:\\PRODUCTION\\probes\\PowerDC_v3.yaml',
         )
     final_job.update(code)
     
     code=mdf.job_postacquisition_settings(file_compression=True,
                                           quick_analysis=False)
     final_job.update(code)
    
     measurement_settings = {}
    
     
     for temperature in temperatures:
        
     
        with open(f'{filename_format}_JOB.yaml', 'w') as file:
            yaml.dump(data=final_job, stream=file, default_flow_style=False)

        # %% MDF and AMF
    
        
        for device in cell_types:
            max_current = 0.5
            # max_current=device_area.max_current(str(device))
            if max_current >=1:
                stepsize=0.001
            # osa_current=device_area.spectral_current(device, temperature)
            # for temperature in temperatures:
            device_name=str(device).replace("-","_")
            function=None
            # function=repetition
            circuit='ridge' #=None/PCM
            step=stepsize
            cbb='ridge'

                
            for pulse_width,pulse_delay,pulse_mode in pulse_settings:
                sweep_stop = max_current
                
                sweep_start=0
                if pulse_mode == 'DC': # limit DC current to 0.499 A (safer for probehead)
                    # if sweep_stop >= 0.5:
                    sweep_stop = 0.3
                    step=stepsize
                    pm_param=f'_DC#{temperature}deg'
                    meas_name="DC"
                elif pulse_mode=="PULS":
                    pm_param=f'_PULSED#{temperature}deg'
                    meas_name="PULSED"
                    step=stepsize
                   
                
                code=mdf.LIVmoduleBarTestPulsed2520(
                    temperature = temperature,
                    start_value = sweep_start,
                    end_value   = sweep_stop,
                    step_size   = step,
                    pulse_width = pulse_width,
                    pulse_delay = pulse_delay,
                    pulse_mode  = pulse_mode,
                    dummy       = '{}_{}_'.format(device,meas_name)
                                          )
                measurement_settings.update(code)

                analysis={
                    list(code.keys())[0]:{
                        ad.get('LIV_FP_LASER'):{
                            'li_voltage_column':vcol,
                            'li_current_column':acol,
                            'li_pd_column':pdcol,
                            'fwd_current_column':acol,
                            'fwd_voltage_column':vcol,
                            'rs_voltage_column':vcol,
                            'rs_current_column':acol,
                            'multifile':False,
                            'parameters':{
                                #key is from DE, value is what goes in parameter name
                                'ITH'        :f'{circuit}-{cbb}-{device_name}-{pn.ith}{pm_param}-{function}',
                                'SLOPE10'    :f'{circuit}-{cbb}-{device_name}-{pn.slope10}{pm_param}-{function}',
                                'SLOPE_IN_ITH_80' :f'{circuit}-{cbb}-{device_name}-{pn.slope_ith_80}{pm_param}-{function}',
                                # 'SLOPE_IN_150_200' :f'{circuit}-{cbb}-{device_name}-SLOPE_IN_150_200{pm_param}-{function}',
                                # 'SLOPE_IN_ITH50_ITH150' :f'{circuit}-{cbb}-{device_name}-SLOPE_IN_ITH50_ITH150{pm_param}-{function}',
                                'IPD10'      :f'{circuit}-{cbb}-{device_name}-{pn.ipd10}{pm_param}-{function}',
                                'IPD_AT_100' :f'{circuit}-{cbb}-{device_name}-IPD_AT_100{pm_param}-{function}',
                                'IPDMAX'     :f'{circuit}-{cbb}-{device_name}-{pn.ipdmax}{pm_param}-{function}',
                                'SOA_I_PDMAX':f'{circuit}-{cbb}-{device_name}-{pn.soa_i_pdmax}{pm_param}-{function}',
                                'VF1'        :f'{circuit}-{cbb}-{device_name}-{pn.vf1}{pm_param}-{function}',
                                'VF100'      :f'{circuit}-{cbb}-{device_name}-VF100{pm_param}-{function}',
                                'VF150'      :f'{circuit}-{cbb}-{device_name}-VF150{pm_param}-{function}',
                                'VF200'      :f'{circuit}-{cbb}-{device_name}-VF200{pm_param}-{function}',
                                'VF250'      :f'{circuit}-{cbb}-{device_name}-VF250{pm_param}-{function}',
                                'VF290'      :f'{circuit}-{cbb}-{device_name}-VF300{pm_param}-{function}',
                                'VFTH'       :f'{circuit}-{cbb}-{device_name}-{pn.vfth}{pm_param}-{function}',
                                'RSTH'       :f'{circuit}-{cbb}-{device_name}-{pn.rsth}{pm_param}-{function}',
                                'RS10'       :f'{circuit}-{cbb}-{device_name}-{pn.rs10}{pm_param}-{function}',
                                'RS80'       :f'{circuit}-{cbb}-{device_name}-{pn.rs80}{pm_param}-{function}',
                                'RS100'       :f'{circuit}-{cbb}-{device_name}-RS100{pm_param}-{function}',
                                'RS150'       :f'{circuit}-{cbb}-{device_name}-RS150{pm_param}-{function}',
                                'RS200'       :f'{circuit}-{cbb}-{device_name}-RS200{pm_param}-{function}',
                                'RS250'       :f'{circuit}-{cbb}-{device_name}-RS250{pm_param}-{function}',
                                'ORITH_80'   :f'{circuit}-{cbb}-{device_name}-{pn.or_ith_80}{pm_param}-{function}',
                                'OR10_80'    :f'{circuit}-{cbb}-{device_name}-OR10_80{pm_param}-{function}',
                                'OR150_200'  :f'{circuit}-{cbb}-{device_name}-OR150_200{pm_param}-{function}',
                                'SOA_I_MODEHOPS':f'{circuit}-{cbb}-{device_name}-SOA_I_MODEHOPS{pm_param}-{function}'
                            },
                        }
                    }
                }
                amf.update(analysis)


        #%% write MDF
        code=mdf.info(pc=pc, author=author, 
                  email=email, mdf_version='1.0.0',
                  program_version='0.0.1')
        final_mdf={}
        final_mdf.update(code)
        
        code=mdf.physical_parameters(pl=PL)
        final_mdf.update(code)
        
        final_mdf.update({'measurement_settings':measurement_settings})
            
            
     with open(f'{filename_format}_MDF.yaml', 'w') as file:
        yaml.dump(data=final_mdf, stream=file, default_flow_style=False)
                
        
    # %% write AMF
     with open(f'{filename_format}_AMF.yaml', 'w') as file:
        yaml.dump(data=amf, stream=file, default_flow_style=False, sort_keys=False)
        file.write('---\n')

    
    #%% MMF
     mmf_matrix = []
     mmf_list = ["Dies/Measurements"] + list(measurement_settings.keys())

     ccf = pd.read_csv(CCF_filepath)
     cells = ccf.CellID
     cell_types = ccf.CellType
    
     for cell, cell_type in zip(cells, cell_types):
        laser_id = cell
        # laser_alias = fp_id_alias[laser_id]
        # find the cell type matching
        # cell_type = [i for i in max_current.keys() if i in cell][0]
        mmf_entry = [cell] + [int(str(cell_type) in meas) for meas in measurement_settings.keys()]
        mmf_matrix.append(mmf_entry)

     mmfdf=pd.DataFrame(mmf_matrix, columns=mmf_list)
     #mmfdf=mmfdf.sort_values(by='Dies/Measurements', ascending=ascending)
       
     mmfdf.to_csv(f'{filename_format}_MMF.csv', index=False)
