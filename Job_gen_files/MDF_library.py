# -*- coding: utf-8 -*-
"""
Created on Thu Dec  6 13:07:28 2018

@author: ErikdenHaan

Measurement definitions library
06-12-2018 initial version
19-12-2018 fix descriptions

"""

from time import gmtime, strftime


def info(pc, author, email, mdf_version, program_version):
    structure={
            'date_and_version':{
                    'date':strftime("%d-%m-%Y", gmtime()),
                    'time':strftime("%H.%M.%S", gmtime()),
                    'mdf_version':mdf_version,
                    'program_version':program_version,
                    'from_pc':'SMP-NB127',
                    'author':'EHN',
                    'email':'erik.den.haan@smartphotonics.nl'
                    }
            }
    return structure

def info_v2(pc, author, email, job_version):
    structure={
            'date_and_version':{
                    'date':strftime("%d-%m-%Y", gmtime()),
                    'time':strftime("%H.%M.%S", gmtime()),
                    'jobversion':job_version,
                    'from_pc':pc,
                    'author':author,
                    'email':email
                    }
            }
    return structure

def job_acquisition_settings(edf_filename=None, mdf_filename=None, ccf_filename=None,
                             mmf_filename=None, amf_filename=None,
                             probecard_filepath=None, die_wise=True,
                             sample_type="wafer",save_shell_output=True):
    structure={
            'acquisition settings':{
                    'all_measurements_in_one_die': die_wise,
                    'sample_type': sample_type,
                    'save_shell_output': save_shell_output,
                    'edf': edf_filename,
                    'mdf': mdf_filename,
                    'ccf': ccf_filename,
                    'mmf': mmf_filename,
                    'amf': amf_filename,
                    'probecard': probecard_filepath
                    }
            }
    return structure

def job_postacquisition_settings(file_compression= True, quick_analysis=False, job_type="PRD"):
    structure={
            'post-acquisition settings':{
                    'compressing files': file_compression,
                    'quick analysis': quick_analysis,
                    'job type': job_type
                    }
            }
    return structure


def batch_information(name, wafers):
    structure={
            'batch_information':{
                    'name':name,
                    'wafers':wafers,
                    'batch': name
                    }
            }
    return structure

def batch_information_v2(name, wafers, customer):
    structure={
            'batch_information':{
                    'name':name,
                    'wafers':wafers,
                    'customer':customer,
                    }
            }
    return structure

def batch_information_v3(product, wafer, customer, lot, batch):
    structure={
            'batch_information':{
                    'name':batch, #TODO: name is also batch. remove later.
                    'product':product,
                    'wafers':wafer,
                    'customer':customer,
                    'lot':lot,
                    'batch':batch #backwards compatibility
                    }
            }
    return structure



def measurement_procedure(f,s):
    structure={
            'measurement_procedure':{
                    'all_measurements_in_one_die':f,
                    'sample_type':s
                    }
            }
    return structure


def physical_parameters(pl):
    structure={
            'physical_parameters':{
                    'PL_wavelength':pl
                    }
            }
    return structure
    

def darkcurrentmodule(pdno, sourcepad, measurepad, groundpad, start_value,
                      end_value,steps, pd_current_range='20uA', t_set=20):
    structure={
            'DARK_{}'.format(pdno):{
                    'description':'Collect the Photodetector dark current',
                    'meas_module':'DarkCurrentPD',
                    'T_set':t_set,
                    'building_blocks':{
                            'Photodetector':{
                                    'source_pad':sourcepad,
                                    'measure_pad':measurepad,
                                    'ground_pad':groundpad,
                                    'set_value':'None', #not needed when doing sweep
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'current_range':pd_current_range
                                    }
                    }
                }
            }
    return structure

def vi_module(pdno, sourcepad, measurepad, groundpad, start_value,
                      end_value,steps, pd_current_range='20uA', t_set=20):
    structure={
            'FWD_VI_{}'.format(pdno):{
                    'description':'Forward voltage',
                    'meas_module':'DarkCurrentPD',
                    'T_set':t_set,
                    'building_blocks':{
                            'Photodetector':{
                                    'source_pad':sourcepad,
                                    'measure_pad':measurepad,
                                    'ground_pad':groundpad,
                                    'set_value':'None', #not needed when doing sweep
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'current_range':pd_current_range
                                    }
                    }
                }
            }
    return structure

def PD_fwd(pdno, sourcepad, measurepad, groundpad, start_value,
           end_value,steps, pd_current_range='100mA', t_set=20):
    structure={
            'FWD_{}'.format(pdno):{
                    'description':'Forward current PD',
                    'meas_module':'DarkCurrentPD_fwd',
                    'T_set':t_set,
                    'building_blocks':{
                            'Photodetector_fwd':{
                                    'source_pad':sourcepad,
                                    'measure_pad':measurepad,
                                    'ground_pad':groundpad,
                                    'set_value':'None', #not needed when doing sweep
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'current_range':pd_current_range
                                    }
                    }
                }
            }
    return structure

def IVmodule(measno, source_pad, measure_pad, ground_pad, 
             max_voltage_compliance, start_value, end_value, steps, 
             pulse_width, nplc=0.1, t_set=20):
    '''
    measno, source_pad, measure_pad, ground_pad, 
    max_voltage_compliance, start_value, end_value, steps
    '''
    structure={
            'IV_{}'.format(measno):{
                    'description':'Perform IV sweep',
                    'meas_module':'IVSOA',
                    'T_set':t_set,
                    'building_blocks':{
                            'SOA':{
                                    'source_pad':source_pad,
                                    'measure_pad':measure_pad,
                                    'ground_pad':ground_pad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'max_voltage_compl':max_voltage_compliance,
                                    'pulse_width':pulse_width,
                                    'nplc':nplc #0.1=16.67 ms, 0.01=166.7us
                                    }
                    }
                }
            }
    return structure

def IVmodule_WP2(measno, source_pad, measure_pad, ground_pad, 
             max_voltage_compliance, start_value, end_value, steps, 
             pulse_width, step_size, max_pos_current, max_neg_current, nplc=0.1,
             vrange=None, irange=None, t_set=20):
    '''
    measno, source_pad, measure_pad, ground_pad, 
    max_voltage_compliance, start_value, end_value, steps
    '''
    if not vrange:
        vrange = max_voltage_compliance

    if not irange:
        irange = max([max_pos_current, abs(max_neg_current)])
        
    structure={
            'IV_{}'.format(measno):{
                    'description':'Perform IV sweep',
                    'meas_module':'IV',
                    'T_set':t_set,
                    'building_blocks':{
                            'SOA':{
                                    'source_pad':source_pad,
                                    'measure_pad':measure_pad,
                                    'ground_pad':ground_pad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'max_voltage_compl':max_voltage_compliance,
                                    'max_pos_current':max_pos_current,
                                    'max_neg_current':max_neg_current,
                                    'pulse_width':pulse_width,
                                    'nplc':nplc, #0.1=16.67 ms, 0.01=166.7us
                                    'step_size':step_size,
                                    'irange': irange,
                                    'vrange': vrange
                                    }
                    }
                }
            }
    return structure


def VImodule_WP2(measno, source_pad, measure_pad, ground_pad, 
             max_voltage_compliance, min_voltage_compliance,
             start_value, end_value, steps, 
             pulse_width, step_size, max_pos_current, max_neg_current, 
             nplc=0.1, vrange=20, irange=0.01, t_set=20):
    '''
    measno, source_pad, measure_pad, ground_pad, 
    max_voltage_compliance, start_value, end_value, steps
    '''
    structure={
            'VI_{}'.format(measno):{
                    'description':'Perform VI sweep',
                    'meas_module':'VI',
                    'T_set':t_set,
                    'building_blocks':{
                            'SOA':{
                                    'source_pad':source_pad,
                                    'measure_pad':measure_pad,
                                    'ground_pad':ground_pad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'max_voltage_compl':max_voltage_compliance,
                                    'min_voltage_compl':min_voltage_compliance,
                                    'max_pos_current':max_pos_current,
                                    'max_neg_current':max_neg_current,
                                    'pulse_width':pulse_width,
                                    'nplc':nplc, #0.1=16.67 ms, 0.01=166.7us
                                    'step_size':step_size,
                                    'vrange':vrange,
                                    'irange':irange,
                                    }
                    }
                }
            }
    return structure



#LIV module with additional GND pad measurements
def LIVmodule_gnd(measno, pd_bias, pd_sourcepad, pd_measurepad, pd_groundpad, 
              soa_sourcepad, soa_measurepad, soa_groundpad, soa_tbd_pad, start_value, 
              end_value, steps, soa_compliance, pd_current_range='100mA', t_set=20):
    structure={
            'LIV_{}'.format(measno):{
                    'description':'Perform LIV sweep, measure PD current',
                    'meas_module':'LIV',
                    'T_set':t_set,
                    'building_blocks':{
                            'Photodetector':{
                                    'set_value':pd_bias,
                                    'source_pad':pd_sourcepad,
                                    'measure_pad':pd_measurepad,
                                    'ground_pad':pd_groundpad, 
                                    'current_range':pd_current_range
                                    },
                            'SOA':{
                                    'source_pad':soa_sourcepad,
                                    'measure_pad':soa_measurepad,
                                    'ground_pad':soa_groundpad,
                                    'TBD_pad':soa_tbd_pad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'max_voltage_compl':soa_compliance,
                                    'min_voltage_compl':0}
                    }
                }
            }
    return structure


def LIVmodule(measno, pd_bias, pd_sourcepad, pd_measurepad, pd_groundpad, 
              soa_sourcepad, soa_measurepad, soa_groundpad, start_value, 
              end_value, steps, soa_compliance, pd_current_range='100mA', t_set=20):
    structure={
            'LIV_{}'.format(measno):{
                    'description':'Perform LIV sweep, measure PD current',
                    'meas_module':'LIV',
                    'T_set':t_set,
                    'building_blocks':{
                            'Photodetector':{
                                    'set_value':pd_bias,
                                    'source_pad':pd_sourcepad,
                                    'measure_pad':pd_measurepad,
                                    'ground_pad':pd_groundpad, 
                                    'current_range':pd_current_range
                                    },
                            'SOA':{
                                    'source_pad':soa_sourcepad,
                                    'measure_pad':soa_measurepad,
                                    'ground_pad':soa_groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'max_voltage_compl':soa_compliance,
                                    'min_voltage_compl':0}
                    }
                }
            }
    return structure


def LIVmodule_LNSOA(measno, pd_bias, pd_sourcepad, pd_measurepad, pd_groundpad, 
              soa_sourcepad, soa_measurepad, soa_groundpad, start_value, 
              end_value, steps, pd_current_range,
              abspd_source, abspd_current_range, abspd_bias,
              absorbers_sig,absorbers_bias,absorbers_current_range, t_set=20):
    structure={
            'LIV_{}'.format(measno):{
                    'description':'Perform LIV sweep, measure PD current',
                    'meas_module':'LIV_LNSOA',
                    'T_set':t_set,
                    'building_blocks':{
                            'Photodetector':{ #these will be the 3 pds measuring 'slab light'
                                    'set_value':pd_bias,
                                    'source_pad':pd_sourcepad,
                                    'measure_pad':pd_measurepad,
                                    'ground_pad':pd_groundpad, 
                                    'current_range':pd_current_range
                                    },
                            'SOA':{
                                    'source_pad':soa_sourcepad,
                                    'measure_pad':soa_measurepad,
                                    'ground_pad':soa_groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'min_voltage_compl':0
                                    },
                            'EOPM1':{ #bb used for abspd checking the SOA
                                    'set_value':abspd_bias,
                                    'source_pad':abspd_source,
                                    'measure_pad':abspd_source,
                                    'ground_pad':pd_groundpad, 
                                    'current_range':abspd_current_range #meas range wordt vanuit de building_blocks standaard ingesteld
                                    },
                            'EOPM2':{ #the actual absorbers
                                    'set_value':absorbers_bias,
                                    'source_pad':absorbers_sig,
                                    'measure_pad':absorbers_sig,
                                    'ground_pad':soa_groundpad, 
                                    'current_range':absorbers_current_range
                                    },
                    }
                }
            }
    return structure



def LIVmoduleBarTest(temperature,  start_value, end_value, step_size,soa_sourcepad='PAD1', soa_measurepad='PAD1',
                     soa_groundpad='COM', pulse_width=0.01, nplc=0.01,
                     pd_sourcepad='PAD2', pd_measurepad='PAD2', 
                     pd_groundpad='COM', pd_bias=0,iteration=''):
    structure={
            'LIV_{}mA_{}degC{}'.format(int(end_value*1000),temperature,iteration):{
                    'description':'Perform LIV measurement',
                    'meas_module':'LIV',
                    'T_set':temperature,
                    'building_blocks':{
                            'SOA':{
                                    'source_pad':soa_sourcepad,
                                    'measure_pad':soa_measurepad, #will be the PD pad, measure current. how do I set meas range?
                                    'ground_pad':soa_groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'step_size':step_size,
                                    'pulse_width':pulse_width,
                                    'nplc':nplc,
                                    },
                            'Photodetector':{
                                    'source_pad':pd_sourcepad,
                                    'measure_pad':pd_measurepad,
                                    'ground_pad':pd_groundpad, 
                                    'set_value':pd_bias,
                                    },
                    }
                }
            }
    return structure

def LIVmoduleBarTest2520(temperature,  start_value, end_value, step_size,soa_sourcepad='PAD1', soa_measurepad='PAD1',
                     soa_groundpad='COM', pulse_width=0.01,
                     pd_sourcepad='PAD2', pd_measurepad='PAD2', 
                     pd_groundpad='COM', pd_bias=-5,iteration=''):
    structure={
            'LIV_DC_{}mA_{}degC{}'.format(int(end_value*1000),temperature,iteration):{
                    'description':'Perform LIV measurement',
                    'meas_module':'LIV_DC',
                    'T_set':temperature,
                    'building_blocks':{
                            'SOA':{
                                    'source_pad':soa_sourcepad,
                                    'measure_pad':soa_measurepad, #will be the PD pad, measure current. how do I set meas range?
                                    'ground_pad':soa_groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'step_size':step_size,
                                    'pulse_width':pulse_width,
                                    # 'nplc':nplc,
                                    },
                            'Photodetector':{
                                    'source_pad':pd_sourcepad,
                                    'measure_pad':pd_measurepad,
                                    'ground_pad':pd_groundpad, 
                                    'set_value':pd_bias,
                                    },
                    }
                }
            }
    return structure


def LIVmoduleBarTestPulsed2520(temperature,  start_value, end_value, step_size,
                               soa_sourcepad='PAD1', soa_measurepad='PAD1',
                               soa_groundpad='COM', 
                               pulse_width=5e-6, pulse_delay=1e-4,
                               pd_sourcepad='PAD2', pd_measurepad='PAD2', 
                               pd_groundpad='COM', pd_bias=-5,
                               pulse_mode='PULS',
                               dummy=''):
#pulse on range:  500ns to 5ms
#pulse off range: 20us to 500ms
    sweep_mode = ""
    if pulse_mode == 'PULS':
        sweep_mode = 'PULSE'
    if pulse_mode == 'DC':
        sweep_mode = 'STAIRCASE'

    structure={
            'LIV_{}_{}{}mA_pwidth{}_pdelay{}_{}degC'.format(sweep_mode, dummy,int(end_value*1000),pulse_width,pulse_delay,temperature):{
                    'description':'Perform LIV measurement',
                    'meas_module':'LIV_PULSE',
                    'T_set':temperature,
                    'building_blocks':{
                            'SOA':{
                                    'source_pad':soa_sourcepad,
                                    'measure_pad':soa_measurepad, #will be the PD pad, measure current. how do I set meas range?
                                    'ground_pad':soa_groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'step_size':step_size,
                                    'pulse_width':pulse_width,
                                    'nplc':None,
                                    'pulse_delay':pulse_delay,
                                    'pulse_mode':pulse_mode
                                    },
                            'Photodetector':{
                                    'source_pad':pd_sourcepad,
                                    'measure_pad':pd_measurepad,
                                    'ground_pad':pd_groundpad, 
                                    'set_value':pd_bias,
                                    },
                    }
                }
            }
    return structure

def LIVmoduleBarTestPulsed2520_temp(temperature,  start_value, end_value, step_size,
                               soa_sourcepad='PAD1', soa_measurepad='PAD1',
                               soa_groundpad='COM', 
                               pulse_width=5e-6, pulse_delay=1e-4,
                               pd_sourcepad='PAD2', pd_measurepad='PAD2', 
                               pd_groundpad='COM', pd_bias=-5,
                               pulse_mode='PULS',
                               dummy=''):
#pulse on range:  500ns to 5ms
#pulse off range: 20us to 500ms

    structure={
#            'LIV_PULSE_{}{}mA_pwidth{}_pdelay{}_{}degC'.format(dummy,int(end_value*1000),pulse_width,pulse_delay,temperature):{
            'LIV_PULSE_{}mA_{}degC_pwidth{}_pdelay{}_{}'.format(int(end_value*1000),temperature,pulse_width,pulse_delay,dummy):{
                    'description':'Perform LIV measurement',
                    'meas_module':'LIV_PULSE',
                    'T_set':temperature,
                    'building_blocks':{
                            'SOA':{
                                    'source_pad':soa_sourcepad,
                                    'measure_pad':soa_measurepad, #will be the PD pad, measure current. how do I set meas range?
                                    'ground_pad':soa_groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'step_size':step_size,
                                    'pulse_width':pulse_width,
                                    'nplc':None,
                                    'pulse_delay':pulse_delay,
                                    'pulse_mode':pulse_mode
                                    },
                            'Photodetector':{
                                    'source_pad':pd_sourcepad,
                                    'measure_pad':pd_measurepad,
                                    'ground_pad':pd_groundpad, 
                                    'set_value':pd_bias,
                                    },
                    }
                }
            }
    return structure


def LIVmoduleBarTestPulsed(temperature,  start_value, end_value, step_size,soa_sourcepad='PAD1', soa_measurepad='PAD1',
                     soa_groundpad='COM', pulse_width=0.01, nplc=0.01,
                     pd_sourcepad='PAD2', pd_measurepad='PAD2', 
                     pd_groundpad='COM', pd_bias=0,iteration='',duty_cycle=1):
    structure={
            'LIV_{}mA_pw{}_dc{}_{}degC'.format(int(end_value*1000),
                                                  pulse_width,
                                                  duty_cycle,
                                                  temperature):{
                    'description':'Perform LIV measurement',
                    'meas_module':'LIV',
                    'T_set':temperature,
                    'building_blocks':{
                            'SOA':{
                                    'source_pad':soa_sourcepad,
                                    'measure_pad':soa_measurepad, #will be the PD pad, measure current. how do I set meas range?
                                    'ground_pad':soa_groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'step_size':step_size,
                                    'pulse_width':pulse_width,
                                    'duty_cycle':duty_cycle,
                                    'nplc':nplc,
                                    },
                            'Photodetector':{
                                    'source_pad':pd_sourcepad,
                                    'measure_pad':pd_measurepad,
                                    'ground_pad':pd_groundpad, 
                                    'set_value':pd_bias,
                                    },
                    }
                }
            }
    return structure

def SpectrumBarTest(temperature, soa_current, soa_compliance_voltage,
                    osa_mode, osa_resolution, osa_sensitivity, 
                    osa_auto_gain, osa_wavelength_span, osa_center_wavelength,
                    soa_sourcepad='PAD1', soa_measurepad='PAD1',
                    soa_groundpad='COM', 
                    dummy=''
                    ):
    structure={
            'SPECTRUM_{}mA_{}degC{}'.format(int(round(soa_current*1000)),temperature,dummy):{
                    'description':'Perform spectral measurement',
                    'meas_module':'Spectrum',
                    'T_set':temperature,
                    'building_blocks':{
                            'SOA':{
                                    'source_pad':soa_sourcepad,
                                    'measure_pad':soa_measurepad, #will be the PD pad, measure current. how do I set meas range?
                                    'ground_pad':soa_groundpad,
                                    'set_value':soa_current,
                                    'set_voltage_compliance':soa_compliance_voltage,
                                    'osa_mode':osa_mode, #should be separate OSA module?
                                    'osa_resolution':osa_resolution,
                                    'osa_sensitivity':osa_sensitivity,
                                    'osa_auto_gain':osa_auto_gain,
                                    'osa_wavelength_span':osa_wavelength_span,
                                    'osa_center_wavelength':osa_center_wavelength,
                                    },
                    }
                }
            }
    return structure



def PContTLMmodule(measno, sourcepad, measurepad, groundpad, start_value, 
              end_value, steps, t_set=20):
    structure={
            'PCONT{}'.format(measno):{
                    'description':'P contact TLM {}um'.format(measno),
                    'meas_module':'PContTLM',
                    'T_set':t_set,
                    'building_blocks':{
                            'PContactTlm':{
                                    'source_pad':sourcepad,
                                    'measure_pad':measurepad,
                                    'ground_pad':groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    }
                    }
                }
            }
    return structure

def NContTLMmodule(measno, sourcepad, measurepad, groundpad, start_value, 
              end_value, steps, t_set=20):
    structure={
            'NCONT{}'.format(measno):{
                    'description':'N contact TLM {}um'.format(measno),
                    'meas_module':'PContTLM',
                    'T_set':t_set,
                    'building_blocks':{
                            'PContactTlm':{ #reuse this, otherwise need to hack AMS
                                    'source_pad':sourcepad,
                                    'measure_pad':measurepad,
                                    'ground_pad':groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    }
                    }
                }
            }
    return structure

def PCladTLMmodule(measno, sourcepad, measurepad, groundpad, start_value, 
              end_value, steps, t_set=20):
    structure={
            'PCLAD{}'.format(measno):{
                    'description':'P cladding TLM {}um'.format(measno),
                    'meas_module':'PCladTLM',
                    'T_set':t_set,
                    'building_blocks':{
                            'PCladdingTlm':{
                                    'source_pad':sourcepad,
                                    'measure_pad':measurepad,
                                    'ground_pad':groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    }
                    }
                }
            }
    return structure

def PisolationTLMmodule(measno, sourcepad, measurepad, groundpad, start_value, 
              end_value, steps, t_set=20):
    structure={
            'PISOL{}'.format(measno):{
                    'description':'P isolation TLM {}um'.format(measno),
                    'meas_module':'PIsolTLM',
                    'T_set':t_set,
                    'building_blocks':{
                            'PIsolationTlm':{
                                    'source_pad':sourcepad,
                                    'measure_pad':measurepad,
                                    'ground_pad':groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    #'current_range':current_range
                                    }
                    }
                }
            }
    return structure


# def GrownNisoTLMmodule(measno, sourcepad, measurepad, groundpad, start_value, 
#               end_value, steps, t_set=20):
#     structure={
#             'GrownNisoTLM{}'.format(measno):{
#                     'description':'P isolation TLM {}um'.format(measno),
#                     'meas_module':'PIsolTLM',
#                     'T_set':t_set,
#                     'building_blocks':{
#                             'PIsolationTlm':{
#                                     'source_pad':sourcepad,
#                                     'measure_pad':measurepad,
#                                     'ground_pad':groundpad,
#                                     'start_value':start_value,
#                                     'end_value':end_value,
#                                     'steps':steps,
#                                     #'current_range':current_range
#                                     }
#                     }
#                 }
#             }
#     return structure



def GrownNisoTLMmodule(master_sourcepad, master_measurepad, master_groundpad, 
                    crange,max_pos_current, max_neg_current,
                    min_voltage_compl, max_voltage_compl, sourcetype,
                    measuretype, start_value, end_value, step_size,
                    description, measplan_description, t_set=20):
    steps=int(abs((end_value-start_value)/step_size)+1)
    structure={
            'GrownNisoTLM_{}_{}'.format(measplan_description,crange):{
                    'description':description,
                    'meas_module':'GenericMasterSweep',
                    'T_set':t_set,
                    'building_blocks':{
                            'MasterCh':{
                                    'source_pad':master_sourcepad,
                                    'measure_pad':master_measurepad,
                                    'ground_pad':master_groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    # 'step_size':step_size,
                                    'steps':steps,
                                    'current_range':crange,
                                    'max_pos_current':max_pos_current,
                                    'max_neg_current':max_neg_current,
                                    'max_voltage_compl':max_voltage_compl,
                                    'min_voltage_compl':min_voltage_compl,
                                    'source_type':sourcetype,
                                    'measure_type':measuretype,
                                    },
                    }
                }
            }
    return structure






def ProbeCardCheck(measid, sourcepad, measurepad, groundpad, start_value, 
              end_value, steps, t_set=20):
    structure={
            'PCCHECK_I{}'.format(measid):{
                    'description':'IV scan between needle {} and needle {}'.format(measurepad, groundpad),
                    'meas_module':'ProbeCardCheck',
                    'T_set':t_set,
                    'building_blocks':{
                            'ProbeCardTest':{
                                    'source_pad':sourcepad,
                                    'measure_pad':measurepad,
                                    'ground_pad':groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    }
                    }
                }
            }
    return structure


def ProbeCardCheckVoltage(measid, sourcepad, measurepad, groundpad, start_value, 
              end_value, steps, t_set=20):
    structure={
            'PCCHECK_V{}'.format(measid):{
                    'description':'VI scan between needle {} and needle {}'.format(measurepad, groundpad),
                    'meas_module':'ProbeCardCheckVoltage',
                    'T_set':t_set,
                    'building_blocks':{
                            'ProbeCardTestVoltage':{
                                    'source_pad':sourcepad,
                                    'measure_pad':measurepad, #was missing measure pad!
                                    'ground_pad':groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    }
                    }
                }
            }
    return structure


def EOPMrevbias(eopmno, sourcepad, measurepad, groundpad, start_value,
                      end_value,steps, current_range, t_set=20):
    structure={
            'EOPM_REV_{}'.format(eopmno):{
                    'description':'Reverse bias EOPM',
                    'meas_module':'EOPM_reverse',
                    'T_set':t_set,
                    'building_blocks':{
                            'EOPM_reversebias':{
                                    'source_pad':sourcepad,
                                    'measure_pad':measurepad,
                                    'ground_pad':groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'current_range':current_range
                                    }
                    }
                }
            }
    return structure

def EOPMfwdbias(eopmno, sourcepad, measurepad, groundpad, start_value,
                      end_value,steps, current_range, t_set=20):
    structure={
            'EOPM_FWD_{}'.format(eopmno):{
                    'description':'Forward current sweep EOPM',
                    'meas_module':'EOPM_forward',
                    'T_set':t_set,
                    'building_blocks':{
                            'EOPM_forwardbias':{
                                    'source_pad':sourcepad,
                                    'measure_pad':measurepad,
                                    'ground_pad':groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'current_range':current_range
                                    }
                    }
                }
            }
    return structure


def OWEOPM_REV(measno, soa_sourcepad, soa_measurepad, soa_groundpad, 
               soa_set_current, soa_compliance, eopm_sourcepad, 
               eopm_measurepad, eopm_groundpad, start_value, end_value, steps,
               eopm_current_range, pd_bias, pd_sourcepad, pd_measurepad, 
               pd_groundpad, pd_current_range, t_set=20
               ):
    structure={
            'OWMZM_REV_{}'.format(measno):{
                    'description':'Perform reverse voltage EOPM sweep, measure PD current',
                    'meas_module':'OWEOPM_reversesweep',
                    'T_set':t_set,
                    'building_blocks':{
                            'SOA':{ #set laser
                                    'source_pad':soa_sourcepad,
                                    'measure_pad':soa_measurepad,
                                    'ground_pad':soa_groundpad,
                                    'set_value':soa_set_current,
                                    'max_voltage_compl':soa_compliance,
                                    },
                            'EOPM_reversebias':{
                                    'source_pad':eopm_sourcepad,
                                    'measure_pad':eopm_measurepad,
                                    'ground_pad':eopm_groundpad, 
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'current_range':eopm_current_range
                                    },
                            'Photodetector':{
                                    'set_value':pd_bias,
                                    'source_pad':pd_sourcepad,
                                    'measure_pad':pd_measurepad,
                                    'ground_pad':pd_groundpad, 
                                    'current_range':pd_current_range #meas range wordt vanuit de building_blocks standaard ingesteld
                                    },
                    }
                }
            }
    return structure

def OWEOPM_REV_map(measno, soa_sourcepad, soa_measurepad, soa_groundpad, 
               soa_set_current, soa_compliance, eopm_sourcepad, 
               eopm_measurepad, eopm_groundpad, start_value, end_value, steps,
               eopm_current_range, pd_bias, pd_sourcepad, pd_measurepad, 
               pd_groundpad, pd_current_range, eopm2_set_voltage, eopm2_pad,
               eopm1_set_voltage, eopm1_pad, t_set=20
               ):
    structure={
            'OWMZM_REV_map_{}_{}'.format(measno,eopm2_set_voltage):{
                    'description':'Perform reverse voltage EOPM sweep, measure PD current',
                    'meas_module':'OWEOPM_reversesweep_map',
                    'T_set':t_set,
                    'building_blocks':{
                            'SOA':{ #set laser
                                    'source_pad':soa_sourcepad,
                                    'measure_pad':soa_measurepad,
                                    'ground_pad':soa_groundpad,
                                    'set_value':soa_set_current,
                                    'max_voltage_compl':soa_compliance,
                                    },
                            'EOPM_reversebias':{
                                    'source_pad':eopm_sourcepad,
                                    'measure_pad':eopm_measurepad,
                                    'ground_pad':eopm_groundpad, 
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'current_range':eopm_current_range
                                    },
                            'Photodetector':{
                                    'set_value':pd_bias,
                                    'source_pad':pd_sourcepad,
                                    'measure_pad':pd_measurepad,
                                    'ground_pad':pd_groundpad, 
                                    'current_range':pd_current_range #meas range wordt vanuit de building_blocks standaard ingesteld
                                    },
                            'EOPM2':{ #this is the extra EOPM
                                    'set_value':eopm2_set_voltage,
                                    'source_pad':eopm2_pad,
                                    'measure_pad':eopm2_pad,
                                    'ground_pad':eopm_groundpad, 
                                    'current_range':eopm_current_range #meas range wordt vanuit de building_blocks standaard ingesteld
                                    },
                            'EOPM1':{ #this is the extra EOPM
                                    'set_value':eopm1_set_voltage,
                                    'source_pad':eopm1_pad,
                                    'measure_pad':eopm1_pad,
                                    'ground_pad':eopm_groundpad, 
                                    'current_range':eopm_current_range #meas range wordt vanuit de building_blocks standaard ingesteld
                                    },
                    }
                }
            }
    return structure




def OWEOPM_FWD(measno, soa_sourcepad, soa_measurepad, soa_groundpad, 
               soa_set_current, soa_compliance, eopm_sourcepad, 
               eopm_measurepad, eopm_groundpad, start_value, end_value, steps,
               eopm_current_range, pd_bias, pd_sourcepad, pd_measurepad, 
               pd_groundpad, pd_current_range, t_set=20
               ):
    structure={
            'OWMZM_FWD_{}'.format(measno):{
                    'description':'Perform forward current EOPM sweep with DBR laser as light source, measure PD current',
                    'meas_module':'OWEOPM_forwardsweep',
                    'T_set':t_set,
                    'building_blocks':{
                            'SOA':{ #set laser
                                    'source_pad':soa_sourcepad,
                                    'measure_pad':soa_measurepad,
                                    'ground_pad':soa_groundpad,
                                    'set_value':soa_set_current,
                                    'max_voltage_compl':soa_compliance,
                                    },
                            'EOPM_forwardbias':{
                                    'source_pad':eopm_sourcepad,
                                    'measure_pad':eopm_measurepad,
                                    'ground_pad':eopm_groundpad, 
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'current_range':eopm_current_range
                                    },
                            'Photodetector':{
                                    'set_value':pd_bias,
                                    'source_pad':pd_sourcepad,
                                    'measure_pad':pd_measurepad,
                                    'ground_pad':pd_groundpad, 
                                    'current_range':pd_current_range #meas range wordt vanuit de building_blocks standaard ingesteld
                                    },
                    }
                }
            }
    return structure


def LIV_2Ch(measno, soa_sourcepad, soa_measurepad, soa_groundpad, 
               soa_set_current, soa_compliance, eopm_sourcepad, 
               eopm_measurepad, eopm_groundpad, start_value, end_value, steps,
               eopm_current_range, pd_bias, pd_sourcepad, pd_measurepad, 
               pd_groundpad, pd_current_range, t_set=20
               ):
    structure={
            'LIV_2Ch_{}'.format(measno):{
                    'description':'Perform forward current sweep on eopm channel with static current bias on 2nd channel, measure PD current',
                    'meas_module':'OWEOPM_forwardsweep',
                    'T_set':t_set,
                    'building_blocks':{
                            'SOA':{ #set laser
                                    'source_pad':soa_sourcepad,
                                    'measure_pad':soa_measurepad,
                                    'ground_pad':soa_groundpad,
                                    'set_value':soa_set_current,
                                    'max_voltage_compl':soa_compliance,
                                    },
                            'EOPM_forwardbias':{
                                    'source_pad':eopm_sourcepad,
                                    'measure_pad':eopm_measurepad,
                                    'ground_pad':eopm_groundpad, 
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'current_range':eopm_current_range
                                    },
                            'Photodetector':{
                                    'set_value':pd_bias,
                                    'source_pad':pd_sourcepad,
                                    'measure_pad':pd_measurepad,
                                    'ground_pad':pd_groundpad, 
                                    'current_range':pd_current_range #meas range wordt vanuit de building_blocks standaard ingesteld
                                    },
                    }
                }
            }
    return structure


def OWWGL_sweep(measno, soa_sourcepad, soa_measurepad, soa_groundpad, 
               soa_set_current, soa_compliance, eopm_sourcepad, 
               eopm_measurepad, eopm_groundpad, start_value, end_value, steps,
               eopm_current_range, monpd_bias, monpd_sourcepad, monpd_measurepad, 
               monpd_groundpad, monpd_current_range,
               ringpd_bias, ringpd_sourcepad, ringpd_measurepad, ringpd_groundpad,
               ringpd_current_range, t_set=20
               ):
    structure={
            'OWWGL_sweep_{}'.format(measno):{
                    'description':'Perform forward current sweep over some diode, measure two PD currents',
                    'meas_module':'OWWGL_sweep',
                    'T_set':t_set,
                    'building_blocks':{
                            'SOA':{
                                    'source_pad':soa_sourcepad,
                                    'measure_pad':soa_measurepad,
                                    'ground_pad':soa_groundpad,
                                    'set_value':soa_set_current,
                                    'max_voltage_compl':soa_compliance,
                                    },
                            'EOPM_forwardbias':{
                                    'source_pad':eopm_sourcepad,
                                    'measure_pad':eopm_measurepad,
                                    'ground_pad':eopm_groundpad, 
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'current_range':eopm_current_range
                                    },
                            'Photodetector':{
                                    'set_value':monpd_bias,
                                    'source_pad':monpd_sourcepad,
                                    'measure_pad':monpd_measurepad,
                                    'ground_pad':monpd_groundpad, 
                                    'current_range':monpd_current_range
                                    },
                            'EOPM1':{ #use EOPM BB to be able to measure two pds
                                    'set_value':ringpd_bias,
                                    'source_pad':ringpd_sourcepad,
                                    'measure_pad':ringpd_measurepad,
                                    'ground_pad':ringpd_groundpad, 
                                    'current_range':ringpd_current_range
                                    },
                    }
                }
            }
    return structure


def OWWGL_eopm_voltagesweep(measno, soa_sourcepad, soa_measurepad, soa_groundpad, 
               soa_set_current, soa_compliance, eopm_sourcepad, 
               eopm_measurepad, eopm_groundpad, start_value, end_value, steps,
               eopm_current_range, monpd_bias, monpd_sourcepad, monpd_measurepad, 
               monpd_groundpad, monpd_current_range,
               ringpd_bias, ringpd_sourcepad, ringpd_measurepad, ringpd_groundpad,
               ringpd_current_range, t_set=20
               ):
    structure={
            'OWWGL_voltagesweep_{}'.format(measno):{
                    'description':'Perform reverse bias sweep over some diode, measure two PD currents',
                    'meas_module':'OWWGL_sweep_voltage',
                    'T_set':t_set,
                    'building_blocks':{
                            'SOA':{
                                    'source_pad':soa_sourcepad,
                                    'measure_pad':soa_measurepad,
                                    'ground_pad':soa_groundpad,
                                    'set_value':soa_set_current,
                                    'max_voltage_compl':soa_compliance,
                                    },
                            'EOPM_reversebias':{
                                    'source_pad':eopm_sourcepad,
                                    'measure_pad':eopm_measurepad,
                                    'ground_pad':eopm_groundpad, 
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'current_range':eopm_current_range
                                    },
                            'Photodetector':{
                                    'set_value':monpd_bias,
                                    'source_pad':monpd_sourcepad,
                                    'measure_pad':monpd_measurepad,
                                    'ground_pad':monpd_groundpad, 
                                    'current_range':monpd_current_range
                                    },
                            'EOPM1':{ #use EOPM BB to be able to measure two pds
                                    'set_value':ringpd_bias,
                                    'source_pad':ringpd_sourcepad,
                                    'measure_pad':ringpd_measurepad,
                                    'ground_pad':ringpd_groundpad, 
                                    'current_range':ringpd_current_range
                                    },
                    }
                }
            }
    return structure

def MIR_sweep(measno, soa_sourcepad, soa_measurepad, soa_groundpad, 
               soa_set_current, soa_compliance, eopm_sourcepad, 
               eopm_measurepad, eopm_groundpad, start_value, end_value, steps,
               eopm_current_range, monpd_bias, monpd_sourcepad, monpd_measurepad, 
               monpd_groundpad, monpd_current_range,
               ringpd_bias, ringpd_sourcepad, ringpd_measurepad, ringpd_groundpad,
               ringpd_current_range, t_set=20
               ):
    structure={
            'MIR_sweep_{}'.format(measno):{
                    'description':'Perform forward current sweep over some diode, measure two PD currents',
                    'meas_module':'OWWGL_sweep',
                    'T_set':t_set,
                    'building_blocks':{
                            'SOA':{
                                    'source_pad':soa_sourcepad,
                                    'measure_pad':soa_measurepad,
                                    'ground_pad':soa_groundpad,
                                    'set_value':soa_set_current,
                                    'max_voltage_compl':soa_compliance,
                                    },
                            'EOPM_forwardbias':{
                                    'source_pad':eopm_sourcepad,
                                    'measure_pad':eopm_measurepad,
                                    'ground_pad':eopm_groundpad, 
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'current_range':eopm_current_range
                                    },
                            'Photodetector':{
                                    'set_value':monpd_bias,
                                    'source_pad':monpd_sourcepad,
                                    'measure_pad':monpd_measurepad,
                                    'ground_pad':monpd_groundpad, 
                                    'current_range':monpd_current_range
                                    },
                            'EOPM1':{ #use EOPM BB to be able to measure two pds
                                    'set_value':ringpd_bias,
                                    'source_pad':ringpd_sourcepad,
                                    'measure_pad':ringpd_measurepad,
                                    'ground_pad':ringpd_groundpad, 
                                    'current_range':ringpd_current_range
                                    },
                    }
                }
            }
    return structure

def MIR_sweep_voltage(measno, soa_sourcepad, soa_measurepad, soa_groundpad, 
               soa_set_current, soa_compliance, eopm_sourcepad, 
               eopm_measurepad, eopm_groundpad, start_value, end_value, steps,
               eopm_current_range, monpd_bias, monpd_sourcepad, monpd_measurepad, 
               monpd_groundpad, monpd_current_range,
               ringpd_bias, ringpd_sourcepad, ringpd_measurepad, ringpd_groundpad,
               ringpd_current_range, t_set=20
               ):
    structure={
            'MIR_sweep_voltage_{}'.format(measno):{
                    'description':'Perform forward current sweep over some diode, measure two PD currents',
                    'meas_module':'OWWGL_sweep_voltage',
                    'T_set':t_set,
                    'building_blocks':{
                            'SOA':{
                                    'source_pad':soa_sourcepad,
                                    'measure_pad':soa_measurepad,
                                    'ground_pad':soa_groundpad,
                                    'set_value':soa_set_current,
                                    'max_voltage_compl':soa_compliance,
                                    },
                            'EOPM_reversebias':{
                                    'source_pad':eopm_sourcepad,
                                    'measure_pad':eopm_measurepad,
                                    'ground_pad':eopm_groundpad, 
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'current_range':eopm_current_range
                                    },
                            'Photodetector':{
                                    'set_value':monpd_bias,
                                    'source_pad':monpd_sourcepad,
                                    'measure_pad':monpd_measurepad,
                                    'ground_pad':monpd_groundpad, 
                                    'current_range':monpd_current_range
                                    },
                            'EOPM1':{ #use EOPM BB to be able to measure two pds
                                    'set_value':ringpd_bias,
                                    'source_pad':ringpd_sourcepad,
                                    'measure_pad':ringpd_measurepad,
                                    'ground_pad':ringpd_groundpad, 
                                    'current_range':ringpd_current_range
                                    },
                    }
                }
            }
    return structure

def OWWGL_sweep_gain_sweep(measno, soa_sourcepad, soa_measurepad, soa_groundpad, 
               soa_compliance, start_value, end_value, steps,
               monpd_bias, monpd_sourcepad, monpd_measurepad, 
               monpd_groundpad, monpd_current_range,
               ringpd_bias, ringpd_sourcepad, ringpd_measurepad, ringpd_groundpad,
               ringpd_current_range, t_set=20
               ):
    structure={
            'OWWGL_sweep_{}'.format(measno):{
                    'description':'Perform forward current sweep over some diode, measure two PD currents',
                    'meas_module':'OWWGL_sweep_gain_sweep',
                    'T_set':t_set,
                    'building_blocks':{
                            'SOA':{
                                    'source_pad':soa_sourcepad,
                                    'measure_pad':soa_measurepad,
                                    'ground_pad':soa_groundpad,
                                    'max_voltage_compl':soa_compliance,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'min_voltage_compl':0,
                                    #'current_range':eopm_current_range
                                    },
                            'Photodetector':{
                                    'set_value':monpd_bias,
                                    'source_pad':monpd_sourcepad,
                                    'measure_pad':monpd_measurepad,
                                    'ground_pad':monpd_groundpad, 
                                    'current_range':monpd_current_range #meas range wordt vanuit de building_blocks standaard ingesteld
                                    },
                            'EOPM1':{ #use fwd version of PD to be able to measure two pds
                                    'set_value':ringpd_bias,
                                    'source_pad':ringpd_sourcepad,
                                    'measure_pad':ringpd_measurepad,
                                    'ground_pad':ringpd_groundpad, 
                                    'current_range':ringpd_current_range #meas range wordt vanuit de building_blocks standaard ingesteld
                                    },
                    }
                }
            }
    return structure

def OWEAM_REV(measno, soa_sourcepad, soa_measurepad, soa_groundpad, 
               soa_set_current, soa_compliance, eam_sourcepad, 
               eam_measurepad, eam_groundpad, start_value, end_value, steps,
               eam_current_range, pd_bias, pd_sourcepad, pd_measurepad, 
               pd_groundpad, pd_current_range, t_set=20
               ):
    structure={
            'OWEAM_REV_{}'.format(measno):{
                    'description':'Perform reverse voltage EAM sweep, measure PD current',
                    'meas_module':'OWEOPM_reversesweep', #receycle from OWEOPM module
                    'T_set':t_set,
                    'building_blocks':{
                            'SOA':{ #set DBR laser
                                    'source_pad':soa_sourcepad,
                                    'measure_pad':soa_measurepad,
                                    'ground_pad':soa_groundpad,
                                    'set_value':soa_set_current,
                                    'max_voltage_compl':soa_compliance,
                                    },
                            'EOPM_reversebias':{
                                    'source_pad':eam_sourcepad,
                                    'measure_pad':eam_measurepad,
                                    'ground_pad':eam_groundpad, 
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'current_range':eam_current_range
                                    },
                            'Photodetector':{
                                    'set_value':pd_bias,
                                    'source_pad':pd_sourcepad,
                                    'measure_pad':pd_measurepad,
                                    'ground_pad':pd_groundpad, 
                                    'current_range':pd_current_range #meas range wordt vanuit de building_blocks standaard ingesteld
                                    },
                    }
                }
            }
    return structure

def EAM_REV(pdno, sourcepad, measurepad, groundpad, start_value,
           end_value,steps, pd_current_range='200uA', t_set=20):
    structure={
            'EAM_REV_{}'.format(pdno):{
                    'description':'Collect the EAM dark current',
                    'meas_module':'DarkCurrentPD',
                    'T_set':t_set,
                    'building_blocks':{
                            'Photodetector':{
                                    'source_pad':sourcepad,
                                    'measure_pad':measurepad,
                                    'ground_pad':groundpad,
                                    'set_value':'None', #not needed when doing sweep
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'current_range':pd_current_range
                                    }
                    }
                }
            }
    return structure

def EAM_FWD(pdno, sourcepad, measurepad, groundpad, start_value,
           end_value,steps, pd_current_range='100mA', max_voltage=5, t_set=20):
    structure={
            'EAM_FWD_{}'.format(pdno):{
                    'description':'Forward current EAM',
                    'meas_module':'DarkCurrentPD_fwd',
                    'T_set':t_set,
                    'building_blocks':{
                            'Photodetector_fwd':{
                                    'source_pad':sourcepad,
                                    'measure_pad':measurepad,
                                    'ground_pad':groundpad,
                                    'set_value':'None', #not needed when doing sweep
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'current_range':pd_current_range,
                                    'max_voltage_compl': max_voltage
                                    }
                    }
                }
            }
    return structure


def QPD_measurement(master_sourcepad, master_measurepad, master_groundpad, 
                    slave_sourcepad, slave_measurepad, slave_groundpad,
                    revbias, master_crange, slave_crange, master_max_pos_current, 
                    master_max_neg_current, slave_max_pos_current, 
                    slave_max_neg_current, min_voltage_compl, max_voltage_compl, 
                    sourcetype, measuretype, start_value, end_value, step_size,
                    description, measplan_description, t_set=20):
    steps=int(abs((end_value-start_value)/step_size)+1)
    structure={
            'QPD_{}'.format(measplan_description):{
                    'description':description,
                    'meas_module':'GenericMasterSlaveSweep',
                    'T_set':t_set,
                    'building_blocks':{
                            'MasterCh':{
                                    'source_pad':master_sourcepad,
                                    'measure_pad':master_measurepad,
                                    'ground_pad':master_groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    # 'step_size':step_size,
                                    'steps':steps,
                                    'current_range':master_crange,
                                    'max_pos_current':master_max_pos_current,
                                    'max_neg_current':master_max_neg_current,
                                    'max_voltage_compl':max_voltage_compl,
                                    'min_voltage_compl':min_voltage_compl,
                                    'source_type':sourcetype,
                                    'measure_type':measuretype,
                                    },
                            'SlaveCh':{
                                    'source_pad':slave_sourcepad,
                                    'measure_pad':slave_measurepad,
                                    'ground_pad':slave_groundpad,
                                    'set_value':revbias,
                                    'current_range':slave_crange,
                                    'max_pos_current':slave_max_pos_current,
                                    'max_neg_current':slave_max_neg_current,
                                    'max_voltage_compl':max_voltage_compl,
                                    'min_voltage_compl':min_voltage_compl,
                                    'source_type':sourcetype,
                                    'measure_type':measuretype,
                                    },
                    }
                }
            }
    return structure


def SingleQuadrant_measurement(master_sourcepad, master_measurepad, master_groundpad, 
                    crange,max_pos_current, max_neg_current,
                    min_voltage_compl, max_voltage_compl, sourcetype,
                    measuretype, start_value, end_value, step_size,
                    description, measplan_description, t_set=20):
    steps=int(abs((end_value-start_value)/step_size)+1)
    structure={
            'QPD_{}'.format(measplan_description):{
                    'description':description,
                    'meas_module':'GenericMasterSweep',
                    'T_set':t_set,
                    'building_blocks':{
                            'MasterCh':{
                                    'source_pad':master_sourcepad,
                                    'measure_pad':master_measurepad,
                                    'ground_pad':master_groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    # 'step_size':step_size,
                                    'steps':steps,
                                    'current_range':crange,
                                    'max_pos_current':max_pos_current,
                                    'max_neg_current':max_neg_current,
                                    'max_voltage_compl':max_voltage_compl,
                                    'min_voltage_compl':min_voltage_compl,
                                    'source_type':sourcetype,
                                    'measure_type':measuretype,
                                    },
                    }
                }
            }
    return structure


def GenericMasterSweep(master_sourcepad, master_measurepad, master_groundpad, 
                    crange,max_pos_current, max_neg_current,
                    min_voltage_compl, max_voltage_compl, sourcetype,
                    measuretype, start_value, end_value, step_size,
                    description, measplan_description, t_set=20):
    steps=int(abs((end_value-start_value)/step_size)+1)
    structure={
            'GMS_{}'.format(measplan_description):{
                    'description':description,
                    'meas_module':'GenericMasterSweep',
                    'T_set':t_set,
                    'building_blocks':{
                            'MasterCh':{
                                    'source_pad':master_sourcepad,
                                    'measure_pad':master_measurepad,
                                    'ground_pad':master_groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    # 'step_size':step_size,
                                    'steps':steps,
                                    'current_range':crange,
                                    'max_pos_current':max_pos_current,
                                    'max_neg_current':max_neg_current,
                                    'max_voltage_compl':max_voltage_compl,
                                    'min_voltage_compl':min_voltage_compl,
                                    'source_type':sourcetype,
                                    'measure_type':measuretype,
                                    },
                    }
                }
            }
    return structure




def GenericMasterSlaveSweep(master_sourcepad, 
                            master_measurepad, 
                            master_groundpad,
                            master_crange, 
                            master_max_pos_current, 
                            master_max_neg_current, 
                            master_min_voltage_compl, 
                            master_max_voltage_compl, 
                            master_sourcetype, 
                            master_measuretype, 
                            start_value, 
                            end_value, 
                            step_size,
                            slave_sourcepad, 
                            slave_measurepad, 
                            slave_groundpad,
                            slave_bias, 
                            slave_crange, 
                            slave_max_pos_current, 
                            slave_max_neg_current, 
                            slave_min_voltage_compl, 
                            slave_max_voltage_compl, 
                            slave_sourcetype,
                            slave_measuretype,
                            description, 
                            measplan_description,
                            t_set=20):
    steps=int(abs((end_value-start_value)/step_size)+1)
    structure={
            'GMSS_{}'.format(measplan_description):{
                    'description':description,
                    'meas_module':'GenericMasterSlaveSweep',
                    'T_set':t_set,
                    'building_blocks':{
                            'MasterCh':{
                                    'source_pad':master_sourcepad,
                                    'measure_pad':master_measurepad,
                                    'ground_pad':master_groundpad,
                                    'start_value':start_value,
                                    'end_value':end_value,
                                    'steps':steps,
                                    'current_range':master_crange,
                                    'max_pos_current':master_max_pos_current,
                                    'max_neg_current':master_max_neg_current,
                                    'max_voltage_compl':master_max_voltage_compl,
                                    'min_voltage_compl':master_min_voltage_compl,
                                    'source_type':master_sourcetype,
                                    'measure_type':master_measuretype,
                                    },
                            'SlaveCh':{
                                    'source_pad':slave_sourcepad,
                                    'measure_pad':slave_measurepad,
                                    'ground_pad':slave_groundpad,
                                    'set_value':slave_bias,
                                    'current_range':slave_crange,
                                    'max_pos_current':slave_max_pos_current,
                                    'max_neg_current':slave_max_neg_current,
                                    'max_voltage_compl':slave_max_voltage_compl,
                                    'min_voltage_compl':slave_min_voltage_compl,
                                    'source_type':slave_sourcetype,
                                    'measure_type':slave_measuretype,
                                    },
                    }
                }
            }
    return structure
