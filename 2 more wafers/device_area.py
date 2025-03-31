x=1
y=2
z=3
pcm_dict = {
              "22":{"X":0, "Y":0, "length":0, "width":0, "max_current":0.5},
              "23":{"X":0, "Y":0, "length":0, "width":0, "max_current":0.5},
              "24":{"X":0, "Y":0, "length":0, "width":0, "max_current":0.5},
              "25":{"X":0, "Y":0, "length":0, "width":0, "max_current":0.5},
              "26":{"X":0, "Y":0, "length":0, "width":0, "max_current":0.5},
              "27":{"X":0, "Y":0, "length":0, "width":0, "max_current":0.5},
              "28":{"X":0, "Y":0, "length":0, "width":0, "max_current":0.5},
              "29":{"X":0, "Y":0, "length":0, "width":0, "max_current":0.5},
              "30":{"X":0, "Y":0, "length":0, "width":0, "max_current":0.5},
              "31":{"X":0, "Y":0, "length":0, "width":0, "max_current":0.5},
              "32":{"X":0, "Y":0, "length":0, "width":0, "max_current":0.5},
              "33":{"X":0, "Y":0, "length":0, "width":0, "max_current":0.5},
              "34":{"X":0, "Y":0, "length":0, "width":0, "max_current":0.5},
              "35":{"X":0, "Y":0, "length":0, "width":0, "max_current":0.5},
              "36":{"X":0, "Y":0, "length":0, "width":0, "max_current":0.5},
              "37":{"X":0, "Y":0, "length":0, "width":0, "max_current":0.5},

             }

dummy_dict ={
    "04-00-A":   {"X":0, "Y":-7175, "length": 1578, "width": 2, "area": 3.16E-05, "osa_currents_20C": [x,y,z], "osa_currents_40C": [x,y,z], "osa_currents_60C": [x,y,z], "osa_currents_80C": [x,y,z] },
    
    }
def max_current(cell_type):
  test_current=pcm_dict[cell_type]['max_current']
  return test_current