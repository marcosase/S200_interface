# -*- coding: utf-8 -*-

import yaml
import sys
import numpy as np
from tqdm import tqdm
import MDF_library as mdf
import pandas as pd
from AMF_library import analysis_dict_v2 as ad
import parameter_names as pn
sort=False
yaml.Dumper.ignore_aliases = lambda *args : True
import device_area
# %% Settings

mdf_version='1.0.0'

pc='SMP-NB216'
author='ABI'
email='antonio.bonardi@smartphotonics.nl'

job_version='1.0.3'
customer = sys.argv[1]
CCF_filepath = sys.argv[2]
temperatures = sys.argv[3]
run_info = sys.argv[4]
print('############################')
print(customer, CCF_filepath, temperatures, run_info)

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

cell_types = list(dict.fromkeys(ccf.CellType.tolist()))
cell_ids=ccf.CellID.tolist()

current_density=14000
stepsize=5e-4                    #A
PL=1550                          #nm
ascending=False                  #For EF reverse MMF. CCF must be reversed as well!
wavelength_span=200              #nm
# spectrum_current=0.300 
enable_spectral_measurement=False

for temperature in temperatures:
    
    for lot,product,wafer in tqdm(run_info):
        # %% JOB

        filename_format='{}_{}_{}_{}deg'.format(customer, lot, wafer,temperature)
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
     
        with open(f'{filename_format}_JOB.yaml', 'w') as file:
            yaml.dump(data=final_job, stream=file, default_flow_style=False)

        # %% MDF and AMF
    
        measurement_settings = {}
        for bar in tqdm(cell_types):
            circuit=bar
            #find if the bar type is Bar1 or Bar2 to assign the correct cbb type
            bar_type=[int(s) for s in bar if s.isdigit()][0]
            cbb="SOA" if bar_type ==1 else "FP"
            
            # bar_cells=device_area.pcm_dict[bar].keys()
            for cell_type in tqdm(cell_types):
                # cell_number=cell.split('#')[0]
                #don't exceed bar's length
                # if int(cell_number) <= bar_max_cell[bar]:
                    #Determine the maximum current based on the bar type and the laser number on the bar
                    max_current=device_area.max_current(cell_type)
                    device_name=cell_type
                    function=None
                    step=stepsize
                    
                    if(enable_spectral_measurement):
                        #LIV max current is for current density of 14 kA/cm2
                        #spectral current should be scaled down to 5kA/cm2
                        spectral_current_value=max_current*(5/14)
                    
                        code=mdf.SpectrumBarTest(temperature=temperature,
                            soa_current=spectral_current_value,
                            soa_compliance_voltage=soa_compliance_voltage,
                            osa_mode='master',
                            osa_resolution=osa_resolution,
                            osa_sensitivity=osa_sensitivity,
                            osa_auto_gain=osa_auto_gain,
                            osa_wavelength_span=wavelength_span,
                            osa_center_wavelength=PL,
                            dummy='_{}_{}'.format(device_name, spectral_current_value)
                            )
                        measurement_settings.update(code)
                        
                          #AMF here
                        analysis={
                              list(code.keys())[0]:{
                                  ad.get('SPECTRUM_BT'):{
                                      'wavelength_column':wvl_col,
                                      'power_column':power_col,
                                      'multifile':False,
                                      'parameters':{
                                          #key is from DE, value is what goes in parameter name
                                          'PEAK_WVL'    :f'{circuit}-{cbb}-{device_name}-{pn.peak_wvl}#{temperature}deg-{function}',
                                          'PEAK_POWER'  :f'{circuit}-{cbb}-{device_name}-{pn.peak_power}#{temperature}deg-{function}',
                                          'SNR'         :f'{circuit}-{cbb}-{device_name}-{pn.snr}#{temperature}deg-{function}',
                                      },
                    
                                  }
                              }
                          }
                        amf.update(analysis)
        
                        
                        
                    for pulse_width,pulse_delay,pulse_mode in tqdm(pulse_settings):
                        sweep_stop = max_current
                        step=0.0005
                        if pulse_mode == 'DC': # limit DC current to 0.499 A (safer for probehead)
                            if sweep_stop >= 0.5:
                                sweep_stop = 0.499
                                
                        if sweep_stop >= 0.5: # do a lower current sweep for comparison
                            code=mdf.LIVmoduleBarTestPulsed2520(temperature=temperature,
                                                      start_value=0,
                                                      end_value=0.499, 
                                                      step_size=step,
                                                      pulse_width=pulse_width,
                                                      pulse_delay=pulse_delay,
                                                      pulse_mode=pulse_mode,
                                                      dummy='{}_'.format(device_name)
                                                      )
                            measurement_settings.update(code)
                            pm_param=f'_PULSED_499mA#{temperature}deg'
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
                                            'SLOPE_IN_150_200' :f'{circuit}-{cbb}-{device_name}-SLOPE_IN_150_200{pm_param}-{function}',
                                            'SLOPE_IN_ITH50_ITH150' :f'{circuit}-{cbb}-{device_name}-SLOPE_IN_ITH50_ITH150{pm_param}-{function}',
                                            'IPD10'      :f'{circuit}-{cbb}-{device_name}-{pn.ipd10}{pm_param}-{function}',
                                            'IPD_AT_100' :f'{circuit}-{cbb}-{device_name}-IPD_AT_100{pm_param}-{function}',
                                            'IPDMAX'     :f'{circuit}-{cbb}-{device_name}-{pn.ipdmax}{pm_param}-{function}',
                                            'SOA_I_PDMAX':f'{circuit}-{cbb}-{device_name}-{pn.soa_i_pdmax}{pm_param}-{function}',
                                            'VF1'        :f'{circuit}-{cbb}-{device_name}-{pn.vf1}{pm_param}-{function}',
                                            # 'VF5000'     :f'{circuit}-{cbb}-{device_name}-VF5000{pm_param}-{function}',
                                            'VFTH'       :f'{circuit}-{cbb}-{device_name}-{pn.vfth}{pm_param}-{function}',
                                            'RS10'       :f'{circuit}-{cbb}-{device_name}-{pn.rs10}{pm_param}-{function}',
                                            'RSTH'       :f'{circuit}-{cbb}-{device_name}-{pn.rsth}{pm_param}-{function}',
                                            'RS80'       :f'{circuit}-{cbb}-{device_name}-{pn.rs80}{pm_param}-{function}',
                                            'ORITH_80'   :f'{circuit}-{cbb}-{device_name}-{pn.or_ith_80}{pm_param}-{function}',
                                            'OR10_80'    :f'{circuit}-{cbb}-{device_name}-OR10_80{pm_param}-{function}',
                                            'OR150_200'  :f'{circuit}-{cbb}-{device_name}-OR150_200{pm_param}-{function}',
                                            'SOA_I_MODEHOPS':f'{circuit}-{cbb}-{device_name}-SOA_I_MODEHOPS{pm_param}-{function}'
                                        },
                                    }
                                }
                            }
                            amf.update(analysis)
        
        
                        code=mdf.LIVmoduleBarTestPulsed2520(temperature=temperature,
                                                  start_value=0,
                                                  end_value=sweep_stop, 
                                                  step_size=step,
                                                  pulse_width=pulse_width,
                                                  pulse_delay=pulse_delay,
                                                  pulse_mode=pulse_mode,
                                                  dummy='{}_'.format(device_name)
                                                  )
                        measurement_settings.update(code)
                        if pulse_mode=='PULS':
                            pm_param=f'_PULSED#{temperature}deg'
                        else:
                            pm_param=f'#{temperature}deg'
        
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
                                        'SLOPE_IN_150_200' :f'{circuit}-{cbb}-{device_name}-SLOPE_IN_150_200{pm_param}-{function}',
                                        'SLOPE_IN_ITH50_ITH150' :f'{circuit}-{cbb}-{device_name}-SLOPE_IN_ITH50_ITH150{pm_param}-{function}',
                                        'IPD10'      :f'{circuit}-{cbb}-{device_name}-{pn.ipd10}{pm_param}-{function}',
                                        'IPD_AT_100' :f'{circuit}-{cbb}-{device_name}-IPD_AT_100{pm_param}-{function}',
                                        'IPDMAX'     :f'{circuit}-{cbb}-{device_name}-{pn.ipdmax}{pm_param}-{function}',
                                        'SOA_I_PDMAX':f'{circuit}-{cbb}-{device_name}-{pn.soa_i_pdmax}{pm_param}-{function}',
                                        'VF1'        :f'{circuit}-{cbb}-{device_name}-{pn.vf1}{pm_param}-{function}',
                                        # 'VF5000'     :f'{circuit}-{cbb}-{device_name}-VF5000{pm_param}-{function}',
                                        'VFTH'       :f'{circuit}-{cbb}-{device_name}-{pn.vfth}{pm_param}-{function}',
                                        'RSTH'       :f'{circuit}-{cbb}-{device_name}-{pn.rsth}{pm_param}-{function}',
                                        'RS10'       :f'{circuit}-{cbb}-{device_name}-{pn.rs10}{pm_param}-{function}',
                                        'RS80'       :f'{circuit}-{cbb}-{device_name}-{pn.rs80}{pm_param}-{function}',
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
                    
            
        #%% write AMF
        with open(f'{filename_format}_AMF.yaml', 'w') as file:
            yaml.dump(data=amf, stream=file, default_flow_style=False)
            file.write('---\n')
    
        
        #%% MMF
        mmf_matrix = []
        mmf_list = ["Dies/Measurements"] + list(measurement_settings.keys())
    
        ccf = pd.read_csv(CCF_filepath)
        cells = ccf.CellID
        cell_types = ccf.CellType
        
        for cell_type,cell in  tqdm(zip(cell_types,cell_ids)):
            # laser_id = cell
            # laser_alias = fp_id_alias[laser_id]
            # find the cell type matching
            # cell_type = [i for i in max_current.keys() if i in cell][0]
            mmf_entry = [cell] +  [int(cell_type in meas) for meas in measurement_settings.keys()]
            mmf_matrix.append(mmf_entry)
    
        mmfdf=pd.DataFrame(mmf_matrix, columns=mmf_list)
        #mmfdf=mmfdf.sort_values(by='Dies/Measurements', ascending=ascending)
           
        mmfdf.to_csv(f'{filename_format}_MMF.csv', index=False)
