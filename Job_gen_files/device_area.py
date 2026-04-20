pcm_dict = {
    "Bar1A":0.27,
    "Bar1B":0.27, 
    "Bar1C":0.34,
    "Bar1D":0.34,
    "Bar1E":0.34,
    "Bar2A":0.27,
    "Bar2B":0.27,
    "Bar2C":0.34,
    "Bar2D":0.34,
    "Bar2E":0.34,
    "Bar2F":0.34,
    "Bar2G":0.405,
    "Bar2H":0.405,
    "Bar2I":0.405,
}
def max_current(bar_type, cell_id=None):
  current=pcm_dict[bar_type]
  return current
# def spectral_current(cell_type):
#     return pcm_dict[cell_type]['osa_currents_5kA']
 