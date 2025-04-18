# -*- coding: utf-8 -*-
"""
Created on Thu Nov  3 08:51:44 2022

Script for generating a new CCF for sub-cell probing on Wafer Prober 2 (or any future 
setup with such characteristics). A standard CCF (as currently generated) is
required as input. Once we have a standard CDF format, this script
would become useless

@author: AntonioBonardi
"""

import os
import pandas as pd

ccf_folder = "."   # location of pre-existing CCF
ccf_name = "PM-SUB-104300_PNC20_CCF.csv"        # name of pre-existing CCF
pcm_ccf_name = "{}".format(ccf_name.split(".")[0] + "_bars_v3.csv") # name of newly-created CCF (pre-existing CCF name + '_pcm_wp2' suffix)

pcm_dict = {"FPC":                               # dict containing name and relative position of pcm elements per each cell-type
                {
                  "13":   {"X":0, "Y":-14250},
                  "14":   {"X":0, "Y":-14000},
                  "15":   {"X":0, "Y":-13750},
                  "16":   {"X":0, "Y":-13500},
                  "17":   {"X":0, "Y":-13250},
                  "18":   {"X":0, "Y":-13000},
                  "19":   {"X":0, "Y":-12750},
                  "20":   {"X":0, "Y":-12500},
                  "21":   {"X":0, "Y":-12250},
                  "22":   {"X":0, "Y":-12000},
                  "23":   {"X":0, "Y":-11750},
                  "24":   {"X":0, "Y":-11500},
                  "25":   {"X":0, "Y":-11250},
                  "26":   {"X":0, "Y":-11000},
                  "27":   {"X":0, "Y":-10750},
                  "28":   {"X":0, "Y":-10500},
                  "29":   {"X":0, "Y":-10250},
                  "30":   {"X":0, "Y":-10000},
                  "31":   {"X":0, "Y":-9750},
                  "32":   {"X":0, "Y":-9500},
                  "33":   {"X":0, "Y":-9250},
                  "34":   {"X":0, "Y":-9000},
                  "35":   {"X":0, "Y":-8750},
                  "36":   {"X":0, "Y":-8500},
                  "37":   {"X":0, "Y":-8250},
                  "38":   {"X":0, "Y":-8000},
                  "39":   {"X":0, "Y":-7750},
                  "40":   {"X":0, "Y":-7500},
                  "41":   {"X":0, "Y":-7250},
                  "42":   {"X":0, "Y":-7000},
                  "43":   {"X":0, "Y":-6750},
                  "44":   {"X":0, "Y":-6500},
                  "45":   {"X":0, "Y":-6250},
                  "46":   {"X":0, "Y":-6000},
                  "47":   {"X":0, "Y":-5750},
                  "48":   {"X":0, "Y":-5500},
                  "49":   {"X":0, "Y":-5250},
                  "50":   {"X":0, "Y":-5000},
                  "51":   {"X":0, "Y":-4750},
                  "52":   {"X":0, "Y":-4500},
                  "53":   {"X":0, "Y":-4250},
                  "54":   {"X":0, "Y":-4000},
                  "55":   {"X":0, "Y":-3750},
                  "56":   {"X":0, "Y":-3500},
                  "57":   {"X":0, "Y":-3250},
                  "58":   {"X":0, "Y":-3000},
                  "59":   {"X":0, "Y":-2750},
                  "60":   {"X":0, "Y":-2500},
                  "61":   {"X":0, "Y":-2250},
                  "62":   {"X":0, "Y":-2000},
                  "63":   {"X":0, "Y":-1750},
                  "64":   {"X":0, "Y":-1500},
                  "65":   {"X":0, "Y":-1250},
                  "66":   {"X":0, "Y":-1000},
                  "67":   {"X":0, "Y":-750},
                  "68":   {"X":0, "Y":-500},
                  "69":   {"X":0, "Y":-250},
                  "70":   {"X":0, "Y":0},
                },
            "FPE":                               # dict containing name and relative position of pcm elements per each cell-type
                {
                  "13":   {"X":0, "Y":-14250},
                  "14":   {"X":0, "Y":-14000},
                  "15":   {"X":0, "Y":-13750},
                  "16":   {"X":0, "Y":-13500},
                  "17":   {"X":0, "Y":-13250},
                  "18":   {"X":0, "Y":-13000},
                  "19":   {"X":0, "Y":-12750},
                  "20":   {"X":0, "Y":-12500},
                  "21":   {"X":0, "Y":-12250},
                  "22":   {"X":0, "Y":-12000},
                  "23":   {"X":0, "Y":-11750},
                  "24":   {"X":0, "Y":-11500},
                  "25":   {"X":0, "Y":-11250},
                  "26":   {"X":0, "Y":-11000},
                  "27":   {"X":0, "Y":-10750},
                  "28":   {"X":0, "Y":-10500},
                  "29":   {"X":0, "Y":-10250},
                  "30":   {"X":0, "Y":-10000},
                  "31":   {"X":0, "Y":-9750},
                  "32":   {"X":0, "Y":-9500},
                  "33":   {"X":0, "Y":-9250},
                  "34":   {"X":0, "Y":-9000},
                  "35":   {"X":0, "Y":-8750},
                  "36":   {"X":0, "Y":-8500},
                  "37":   {"X":0, "Y":-8250},
                  "38":   {"X":0, "Y":-8000},
                  "39":   {"X":0, "Y":-7750},
                  "40":   {"X":0, "Y":-7500},
                  "41":   {"X":0, "Y":-7250},
                  "42":   {"X":0, "Y":-7000},
                  "43":   {"X":0, "Y":-6750},
                  "44":   {"X":0, "Y":-6500},
                  "45":   {"X":0, "Y":-6250},
                  "46":   {"X":0, "Y":-6000},
                  "47":   {"X":0, "Y":-5750},
                  "48":   {"X":0, "Y":-5500},
                  "49":   {"X":0, "Y":-5250},
                  "50":   {"X":0, "Y":-5000},
                  "51":   {"X":0, "Y":-4750},
                  "52":   {"X":0, "Y":-4500},
                  "53":   {"X":0, "Y":-4250},
                  "54":   {"X":0, "Y":-4000},
                  "55":   {"X":0, "Y":-3750},
                  "56":   {"X":0, "Y":-3500},
                  "57":   {"X":0, "Y":-3250},
                  "58":   {"X":0, "Y":-3000},
                  "59":   {"X":0, "Y":-2750},
                  "60":   {"X":0, "Y":-2500},
                  "61":   {"X":0, "Y":-2250},
                  "62":   {"X":0, "Y":-2000},
                  "63":   {"X":0, "Y":-1750},
                  "64":   {"X":0, "Y":-1500},
                  "65":   {"X":0, "Y":-1250},
                  "66":   {"X":0, "Y":-1000},
                  "67":   {"X":0, "Y":-750},
                  "68":   {"X":0, "Y":-500},
                  "69":   {"X":0, "Y":-250},
                  "70":   {"X":0, "Y":0},
                },
            "FPG":                               # dict containing name and relative position of pcm elements per each cell-type
                {
                  "13":   {"X":0, "Y":-14250},
                  "14":   {"X":0, "Y":-14000},
                  "15":   {"X":0, "Y":-13750},
                  "16":   {"X":0, "Y":-13500},
                  "17":   {"X":0, "Y":-13250},
                  "18":   {"X":0, "Y":-13000},
                  "19":   {"X":0, "Y":-12750},
                  "20":   {"X":0, "Y":-12500},
                  "21":   {"X":0, "Y":-12250},
                  "22":   {"X":0, "Y":-12000},
                  "23":   {"X":0, "Y":-11750},
                  "24":   {"X":0, "Y":-11500},
                  "25":   {"X":0, "Y":-11250},
                  "26":   {"X":0, "Y":-11000},
                  "27":   {"X":0, "Y":-10750},
                  "28":   {"X":0, "Y":-10500},
                  "29":   {"X":0, "Y":-10250},
                  "30":   {"X":0, "Y":-10000},
                  "31":   {"X":0, "Y":-9750},
                  "32":   {"X":0, "Y":-9500},
                  "33":   {"X":0, "Y":-9250},
                  "34":   {"X":0, "Y":-9000},
                  "35":   {"X":0, "Y":-8750},
                  "36":   {"X":0, "Y":-8500},
                  "37":   {"X":0, "Y":-8250},
                  "38":   {"X":0, "Y":-8000},
                  "39":   {"X":0, "Y":-7750},
                  "40":   {"X":0, "Y":-7500},
                  "41":   {"X":0, "Y":-7250},
                  "42":   {"X":0, "Y":-7000},
                  "43":   {"X":0, "Y":-6750},
                  "44":   {"X":0, "Y":-6500},
                  "45":   {"X":0, "Y":-6250},
                  "46":   {"X":0, "Y":-6000},
                  "47":   {"X":0, "Y":-5750},
                  "48":   {"X":0, "Y":-5500},
                  "49":   {"X":0, "Y":-5250},
                  "50":   {"X":0, "Y":-5000},
                  "51":   {"X":0, "Y":-4750},
                  "52":   {"X":0, "Y":-4500},
                  "53":   {"X":0, "Y":-4250},
                  "54":   {"X":0, "Y":-4000},
                  "55":   {"X":0, "Y":-3750},
                  "56":   {"X":0, "Y":-3500},
                  "57":   {"X":0, "Y":-3250},
                  "58":   {"X":0, "Y":-3000},
                  "59":   {"X":0, "Y":-2750},
                  "60":   {"X":0, "Y":-2500},
                  "61":   {"X":0, "Y":-2250},
                  "62":   {"X":0, "Y":-2000},
                  "63":   {"X":0, "Y":-1750},
                  "64":   {"X":0, "Y":-1500},
                  "65":   {"X":0, "Y":-1250},
                  "66":   {"X":0, "Y":-1000},
                  "67":   {"X":0, "Y":-750},
                  "68":   {"X":0, "Y":-500},
                  "69":   {"X":0, "Y":-250},
                  "70":   {"X":0, "Y":0},
                },
            "FPI":                               # dict containing name and relative position of pcm elements per each cell-type
                {
                  "13":   {"X":0, "Y":-14250},
                  "14":   {"X":0, "Y":-14000},
                  "15":   {"X":0, "Y":-13750},
                  "16":   {"X":0, "Y":-13500},
                  "17":   {"X":0, "Y":-13250},
                  "18":   {"X":0, "Y":-13000},
                  "19":   {"X":0, "Y":-12750},
                  "20":   {"X":0, "Y":-12500},
                  "21":   {"X":0, "Y":-12250},
                  "22":   {"X":0, "Y":-12000},
                  "23":   {"X":0, "Y":-11750},
                  "24":   {"X":0, "Y":-11500},
                  "25":   {"X":0, "Y":-11250},
                  "26":   {"X":0, "Y":-11000},
                  "27":   {"X":0, "Y":-10750},
                  "28":   {"X":0, "Y":-10500},
                  "29":   {"X":0, "Y":-10250},
                  "30":   {"X":0, "Y":-10000},
                  "31":   {"X":0, "Y":-9750},
                  "32":   {"X":0, "Y":-9500},
                  "33":   {"X":0, "Y":-9250},
                  "34":   {"X":0, "Y":-9000},
                  "35":   {"X":0, "Y":-8750},
                  "36":   {"X":0, "Y":-8500},
                  "37":   {"X":0, "Y":-8250},
                  "38":   {"X":0, "Y":-8000},
                  "39":   {"X":0, "Y":-7750},
                  "40":   {"X":0, "Y":-7500},
                  "41":   {"X":0, "Y":-7250},
                  "42":   {"X":0, "Y":-7000},
                  "43":   {"X":0, "Y":-6750},
                  "44":   {"X":0, "Y":-6500},
                  "45":   {"X":0, "Y":-6250},
                  "46":   {"X":0, "Y":-6000},
                  "47":   {"X":0, "Y":-5750},
                  "48":   {"X":0, "Y":-5500},
                  "49":   {"X":0, "Y":-5250},
                  "50":   {"X":0, "Y":-5000},
                  "51":   {"X":0, "Y":-4750},
                  "52":   {"X":0, "Y":-4500},
                  "53":   {"X":0, "Y":-4250},
                  "54":   {"X":0, "Y":-4000},
                  "55":   {"X":0, "Y":-3750},
                  "56":   {"X":0, "Y":-3500},
                  "57":   {"X":0, "Y":-3250},
                  "58":   {"X":0, "Y":-3000},
                  "59":   {"X":0, "Y":-2750},
                  "60":   {"X":0, "Y":-2500},
                  "61":   {"X":0, "Y":-2250},
                  "62":   {"X":0, "Y":-2000},
                  "63":   {"X":0, "Y":-1750},
                  "64":   {"X":0, "Y":-1500},
                  "65":   {"X":0, "Y":-1250},
                  "66":   {"X":0, "Y":-1000},
                  "67":   {"X":0, "Y":-750},
                  "68":   {"X":0, "Y":-500},
                  "69":   {"X":0, "Y":-250},
                  "70":   {"X":0, "Y":0},
                },
            "FPK":                               # dict containing name and relative position of pcm elements per each cell-type
                {
                  "13":   {"X":0, "Y":-14250},
                  "14":   {"X":0, "Y":-14000},
                  "15":   {"X":0, "Y":-13750},
                  "16":   {"X":0, "Y":-13500},
                  "17":   {"X":0, "Y":-13250},
                  "18":   {"X":0, "Y":-13000},
                  "19":   {"X":0, "Y":-12750},
                  "20":   {"X":0, "Y":-12500},
                  "21":   {"X":0, "Y":-12250},
                  "22":   {"X":0, "Y":-12000},
                  "23":   {"X":0, "Y":-11750},
                  "24":   {"X":0, "Y":-11500},
                  "25":   {"X":0, "Y":-11250},
                  "26":   {"X":0, "Y":-11000},
                  "27":   {"X":0, "Y":-10750},
                  "28":   {"X":0, "Y":-10500},
                  "29":   {"X":0, "Y":-10250},
                  "30":   {"X":0, "Y":-10000},
                  "31":   {"X":0, "Y":-9750},
                  "32":   {"X":0, "Y":-9500},
                  "33":   {"X":0, "Y":-9250},
                  "34":   {"X":0, "Y":-9000},
                  "35":   {"X":0, "Y":-8750},
                  "36":   {"X":0, "Y":-8500},
                  "37":   {"X":0, "Y":-8250},
                  "38":   {"X":0, "Y":-8000},
                  "39":   {"X":0, "Y":-7750},
                  "40":   {"X":0, "Y":-7500},
                  "41":   {"X":0, "Y":-7250},
                  "42":   {"X":0, "Y":-7000},
                  "43":   {"X":0, "Y":-6750},
                  "44":   {"X":0, "Y":-6500},
                  "45":   {"X":0, "Y":-6250},
                  "46":   {"X":0, "Y":-6000},
                  "47":   {"X":0, "Y":-5750},
                  "48":   {"X":0, "Y":-5500},
                  "49":   {"X":0, "Y":-5250},
                  "50":   {"X":0, "Y":-5000},
                  "51":   {"X":0, "Y":-4750},
                  "52":   {"X":0, "Y":-4500},
                  "53":   {"X":0, "Y":-4250},
                  "54":   {"X":0, "Y":-4000},
                  "55":   {"X":0, "Y":-3750},
                  "56":   {"X":0, "Y":-3500},
                  "57":   {"X":0, "Y":-3250},
                  "58":   {"X":0, "Y":-3000},
                  "59":   {"X":0, "Y":-2750},
                  "60":   {"X":0, "Y":-2500},
                  "61":   {"X":0, "Y":-2250},
                  "62":   {"X":0, "Y":-2000},
                  "63":   {"X":0, "Y":-1750},
                  "64":   {"X":0, "Y":-1500},
                  "65":   {"X":0, "Y":-1250},
                  "66":   {"X":0, "Y":-1000},
                  "67":   {"X":0, "Y":-750},
                  "68":   {"X":0, "Y":-500},
                  "69":   {"X":0, "Y":-250},
                  "70":   {"X":0, "Y":0},
                },

            }
    
ccf_df = pd.read_csv(os.path.join(ccf_folder, ccf_name)) # read CCF file
new_ccf_rows_list = []  # list for storing entries for new CCF
     
for cell_type in pcm_dict.keys():
    celltype_df = ccf_df[ccf_df['CellType'] == cell_type]

    cells = celltype_df['CellID'].tolist()
    cells_posx = celltype_df['X'].tolist()
    cells_posy = celltype_df['Y'].tolist()

    for cell, cell_x, cell_y in zip(cells, cells_posx, cells_posy):
        for pcm in pcm_dict[cell_type].keys():
            posx = pcm_dict[cell_type][pcm]["X"] + cell_x
            posy = pcm_dict[cell_type][pcm]["Y"] + cell_y
            pcm_name = f"{cell}#{pcm}"
            new_ccf_rows_list.append([cell_type, pcm_name, posx, posy])
            
# converting new_ccf list into pandas df
new_ccf_df = pd.DataFrame(new_ccf_rows_list, columns = ["CellType", "CellID", "X", "Y"])

# creating a csv file for the new CCF
new_ccf_df.to_csv(os.path.join(ccf_folder, pcm_ccf_name), index=False)
        