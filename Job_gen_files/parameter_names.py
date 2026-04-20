# -*- coding: utf-8 -*-
"""
Created on Fri Jul  9 13:38:27 2021

Lookup table for parameter names to be used for AMF generation
If names change, fix here.

@author: ErikdenHaan
"""

#lasers
slope10    ='SLOPE10'
slope_at_25 = 'SLOPE_AT_25'
slope_at_30 = 'SLOPE_AT_30'
slope_in_ith_80 = 'SLOPE_IN_ITH_80'
slope_in_ith_20 = 'SLOPE_IN_ITH_20'
slope_in_ith_30 = 'SLOPE_IN_ITH_30'
slope_in_ith_40 = 'SLOPE_IN_ITH_40'

slope_in_ith_ith20 = 'SLOPE_IN_ITH_ITH20'
slope_in_ith_ith30 = 'SLOPE_IN_ITH_ITH30'
slope_in_ith_ith40 = 'SLOPE_IN_ITH_ITH40'


slope_ith_80 = 'SLOPE_IN_ITH_80'
slope_ith_20 = 'SLOPE_IN_ITH_20'
slope_ith_30 = 'SLOPE_IN_ITH_30'
slope_ith_40 = 'SLOPE_IN_ITH_40'
slope_in_20_40 = 'SLOPE_IN_20_40'

mhfree_slope_in_ith_80 = 'MHFREE_SLOPE_IN_ITH_80'
ipd10      ='IPD10'
ipdat      ='IPD_AT_VAL'
ipd_at_80  ='IPD_AT_80' 
ith        ='ITH'
ipdmax     ='IPDMAX'
soa_i_pdmax='SOA_I_PDMAX'
soa_i_modehops='SOA_I_MODEHOPS'
peak_wvl   ='PEAK_WVL'
peak_power ='PEAK_POWER'
snr        ='SNR'
vfth       ='VFTH'
rsth       ='RSTH'


#diodes
vf1        ='VF1'
vf10       ='VF10'
vf20       ='VF20'
vf300      ='VF300'
rs5        ='RS5'
rs10       ='RS10'
rs80       ='RS80'
rs100      ='RS100'
or_ith_80  ='OR_ITH_80'
or9_10     ='OR9_10'


#leakage
dark_offset = 'DARK0'
dark2      ='DARK2'
dark5      ='DARK5'
leak2      ='LEAK2'
leak5      ='LEAK5'
leak8      ='LEAK8'
leak_offset  ='LEAK0'

#EAMs
v_ipdmax   ='V_IPDMAX'
v_ipdmin   ='V_IPDMIN'
ipd_vmin   ='IPD_VMIN'
ipd_vmax   ='IPD_VMAX'
er         ='ER'

#EOPMs
vpi        ='VPI'
v0         ='V0' #voltage at lowest intensity
i0         ='I0'
v1         ='V1' #voltage at highest intensity
i1         ='I1'
i_monpd_avg='I_MONPD_AVG' #average monitor PD current

#plating PCM
plating_r  ='PLATING_RESISTANCE'

#tlms
ohmr = 'OR'