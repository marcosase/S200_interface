# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 09:45:33 2019

This script implements the cabling class. The purpose of the cabling is to
interconnect the probing equipment to the Source Meter Units (SMU).

Different setups contain cabling networks of different complexity. The class
should be made setup-agnostic by receiving the mapping from & to each node from
external configuration files. In the present configuration 3 classes of nodes are
foreseen: "probecard", "cabling", and "smu". For each class configuration file(s)
 (.yml) are expected to be found in a local folder called "maps" and in its 
 subfolders ./maps/probe, ./maps/cabling, and ./maps/smu, respectively. 
If one or more .yml file is missing, the operator has the possibility of creating
it on the spot. The created file(s) are saved and will remain available for 
future measurements.

Class should be compatible with API.instrument

During connect:
	Class makes the whole mapping from DUT all the way to SMU. Then, for operation
	it only needs the 1st and last element of each row. These will be parsed in
	two dictionaries, "DUT_2_SMU" (DUT pads ->SMU channels) and "SMU_2_DUT" 
	(SMU channels -> DUT pads).


Mapping each of the files should be compatible with
phiola\\phiola_meas\\phiola\\meas\\pin_mapping.py

===============================================================================
Concept:

          --------------------------------------------
DUT <===> | Node01 <===> Node02 <===> ... <===> NodeN |  <===> SMU
          --------------------------------------------
                      ^ Cabling Network ^

===============================================================================


Requirements for Node files:

	0. File format: yaml is prefered (for now) as it is easier to read. 
	1. Filenames to start with NodeXX_exaplanation of type of node; XX to be a two-digit number;
	   explanation (optional) to give a user friendly explanation of file functionalities.
    2. Folder called "/maps" and sub-folders called "cabling", "probecard", and "smu".
	3. For each folder at point 2, only one mapping setup must be present (i.e. no mixing
       of different setups), otherwise errors/crashes could arise
    4. Node files are not necessary before starting the script, and can be generated
       while the script running



@author: KostasVoutyras and AntonioBonardi
"""

import os, sys
from collections import Mapping

sys.path.append('../')
from API.Instrument import Instrument

from utils.utils	import load_yaml_file
import utils.folders
import yaml

#from utils.folders import get_local_config_folder

def get_local_config_folder():
    # AB: I am not really sure I want/need this function,  not even in utils.folders
    # TO BE IMPLEMENTED!!!!
    """temp function for testing. When the exact location is known, transfer the
	function under utils.folders and uncomment line 66.
    """
    return '.'



class NodeMapping(Instrument):
    """This class implements the functionalities of connection mapping for each step of
    the connection chain between the DUT (device, i.e. wafer, PCB, etc., under investigation)
    and the SMU (test measuring device)
    """

    def __init__(self):
        """
        """
        super().__init__()

    def connect(self,port=None):
        """Maybe this function is superflous
        """
        super().connect()
        #This was for debugging
        #self.test_generate_node_mapping(interactive = False) #not existing function


    def release(self,**kwargs):
        """ Releases the photodetector.
        """

        self.lg.debug('Released')
        super().release()


    def get_ID(self):
        """
        """
        super().get_ID()
        return self.ID
    
    def search_for_node_files(self, _dir_path):
        """ Find all .yml files in the given "dir_path" folder
        """
        r,p, filenames = os.walk(_dir_path, topdown=True).__next__()
        self._node_files = [fn for fn in filenames if fn.startswith('Node')]


    def make_node_sequence(self):
        """Explicitely sort the files.
        """
        return sorted(self._node_files)

    def load_node_files(self, _dir_path):
        """Loads the node files into a collections.Mapping dictionary
		(this data structure doesn't support	changing its keys or values)
        """
        self._map_dict = {}  #Mapping dictionary
        for nf in self._node_files:
            d = {}
            print("opening file ", os.path.join(_dir_path, nf))
            d = load_yaml_file(os.path.join(_dir_path, nf))
            #node_nr = nf.split('_')[0]
            node_nr = nf.split('.')[0]
            self._map_dict[node_nr] = d
        #print("uploaded dictionary")
        #print(self._map_dict)


    def select_node_mapping(self, _dir_path):
        """"This function will ask the user to provide the yaml file(s) with the description
        of the node mapping or to generate a new one(s). If the user opts for
        a new one(s), the node mapping generating function is called and previously existing
        yaml file(s) will be overwritten (if name is the same). """
        answer=input("Are the node configuration yaml files available?[Y/N] ")
        if(answer=='Y' or answer=='y' or answer=='Yes' or answer=='yes' or answer=='YES'):
            self.search_for_node_files(_dir_path)
            self.make_node_sequence()
        else:
            n_nodes = input("How many pads, channels, or cables are present? ")
            n_nodes = int(n_nodes)
            n_steps = input("How many intermediate steps are necessary to define the current sub-configuration? ")
            n_steps = int(n_steps)
            for n in range(n_steps):
                self.generate_node_card(_dir_path, n, n_nodes)
            self.search_for_node_files(_dir_path)
            self.make_node_sequence()
        self.load_node_files(_dir_path)

    def generate_node_card(self,_dir_path, node_id, n_nodes):
        """Asks the user to enter the mapping configuration of each node.
        The entered values are saved on a yaml file in the provided folder (_dir_path)"""

        _type = _dir_path.split(os.sep)[-1] # retrieving the node type from the given path

        file_name = "Node" + str(node_id).zfill(2) + "_"+ _type + ".yml"
                             
        print("*******************")
        print("Generating Node: ",os.path.join(_dir_path,file_name))
        node_dict = {}
        while True:
            node_description = input("Provide the description of the node: ")
            print("This is the entered node description:")
            print(node_description)
            ok = input("Is the entered description correct?[Y/N] ")
            if(ok =='Y' or ok=='y' or ok=='Yes' or ok=='yes' or ok=='YES'):
                break
            else:
                print("The entered description has been cancelled")
        node_dict['info'] = node_description
        while True:
            node_subdict = {}
            # filling the dictionary
            print("Please, enter the node mapping values")
            for i in range(n_nodes):
                key = input("Enter input ID: ")
                value = input("Enter the output ID: ")
                node_subdict[key] = value
            # verifying the dictionary
            print('\nVerification of the entered values')
            for key in node_subdict:
                print(key, ' corresponds to ', node_subdict[key])
            ok = input("Are the shown values correct?[Y/N] ")
            if(ok =='Y' or ok=='y' or ok=='Yes' or ok=='yes' or ok=='YES'):
                break
            else:
                print("The entered values have been cancelled")
        node_dict['mapping'] = node_subdict
        with open(os.path.join(_dir_path,file_name), 'w') as outfile:
            yaml.dump(node_dict, outfile, default_flow_style=False)
            


class Full_Cabling(NodeMapping):
    """This class implement the node mapping on the full chain, i.e. from the probing pads 
    to the SMU channels.
    """
    def __init__(self, probecard_path = None, local_dir = "cabling"):
        self.config_dir(local_dir)
        skip_node_mapping = self.get_fullchain_config_file(probecard_path)
        self._nodemapping = NodeMapping()
        if not skip_node_mapping:
            self.combine_full_node_chain()
            
    def connect(self,port=None):
        """We need an (empty) connect function, as defined in API.Instrument
        """
        super().connect()

    def config_dir(self,_local_dir):
        """ This function sets the folder where the full-chain mapping is retrieved from or saved to
        (if no other file is provided in the EDF file)
        """
        self._folder_dir = os.path.join(get_local_config_folder(), _local_dir, 'maps')
        
    def combine_full_node_chain(self):
        """This function combines together the mapping of the different nodes, subdivided in 
		3 categories, "probecard","cables", and "smu", in a single dictionary
		"""
        _types = ["probecard","cables","smu"]
        self._global_map_dict = {}
        for _type in _types:
            print("\n*******************************************")
            print("Re-calling the configuration of the", _type)
            _open_dir = os.path.join(self._folder_dir, _type)
            self._nodemapping.select_node_mapping(_open_dir)
            self._global_map_dict.update(self._nodemapping._map_dict)
        self.DUT_2_SMU, self.SMU_2_DUT = self.make_DUT_SMU_tables(self._global_map_dict) 
            
    def make_DUT_SMU_tables(self,global_dict):
        """ Starting from the loaded mapping settings (probecard, cables, and SMU channels), it 
        return the conversion dictionary from DUT pads to SMU channels and the conversion 
        dictionary from SMU channels to DUT pads.
        """
        DUT_SMU_table = {}
        SMU_DUT_table = {}
        file_indices = []
        for step, step_value in global_dict.items():
            file_indices.append(step)
        
        for pad_id, probe_card_connection_id in global_dict[file_indices[0]]['mapping'].items():
            
            key = probe_card_connection_id
            
            for i in file_indices[1:]:
                key = global_dict[i]['mapping'][key]
               
            smu_port = key    
            DUT_SMU_table[pad_id] = smu_port
            SMU_DUT_table[smu_port] = pad_id
            #saving the DUT_SMU table on a yaml file
            self.write_full_cabling_config_file(DUT_SMU_table)
        return DUT_SMU_table, SMU_DUT_table    

    def get_fullchain_config_file(self, _file_path):
        """This function opens a yaml file containing the full cabling chain at the given path (the path can consist either
        in a yaml file or in a folder). If no path is given, or if it is invalid, or if no yaml file is found or cannot be
        opend, the default folder '.\maps' is used instead. In the default folder the first yaml file found with 'full_cabling_chain' 
        in its name is taken. If a yaml file is found (either at the given path or in the default location) 
        a dictionary is created, otherwise an empty dictionary is generated and the user will be afterwards prompted to create
        a new one.
        """
        skip_mapping = False
        if _file_path == None:
            _file_path = os.path.join(os.getcwd(), self._folder_dir)            
#            print(_file_path)
            print("### WARNING ###")
            print(" No probecard config file provided!\n Looking for a config file in .\maps ...")
        else:
            if ".yml" in _file_path or ".yaml" in _file_path: # user specified yaml file
                try:
                    if(len(_file_path.split(os.sep))>1): # yaml file in a specific folder
                        fn_full_cabling = _file_path
                    else:    # yaml file in the default folder
                        fn_full_cabling = os.path.join("C:\PRODUCTION\probes", _file_path)
                    print(fn_full_cabling)    
                    self.load_full_cabling_from_file(fn_full_cabling)
                    skip_mapping = True
                    print("######")
                    print("Cabling configuration file {0} successfully loaded\n".format(_file_path))
                except:
                    _file_path = os.path.join(os.getcwd(), self._folder_dir)            
                    print("### WARNING ###")
                    print(" The provided file is not existing or invalid!\n Looking for a config file in .\maps ...")
            else: #user specified only the folder where the yaml file is
                try:
                    r,p, filenames = os.walk(_file_path, topdown=True).__next__()
                    map_file_name = [fn for fn in filenames if ('.yaml' in fn or '.yml' in fn)][0]
                    fn_full_cabling = os.path.join(_file_path, map_file_name)
                    print(fn_full_cabling)
                    self.load_full_cabling_from_file(fn_full_cabling)
                    skip_mapping = True
                    print("######")
                    print("Cabling configuration file {0} found at {1} and successfully loaded\n".format(map_file_name, _file_path))
                except:
                    print("### WARNING ###")
                    print("No cabling full-chain configuration file found at {0}!".format(_file_path))
                    print("Looking for a config file in .\maps ...")
                    _file_path = os.path.join(os.getcwd(), self._folder_dir)            
                
        if skip_mapping == False:
            r,p, filenames = os.walk(_file_path, topdown=True).__next__()
            try:
                map_file_name = [fn for fn in filenames if 'full_cabling_chain' in fn][0]
                fn_full_cabling = os.path.join(_file_path, map_file_name)
                print(fn_full_cabling)
                self.load_full_cabling_from_file(fn_full_cabling)
                skip_mapping = True
                print("######")
                print("Cabling configuration file {0} found at {1} and successfully loaded\n".format(map_file_name, _file_path))
            except:
                print("### WARNING ###")
                print("No cabling full-chain configuration file found!")
                print("The cabling chain description will be generated from the individual nodes description.\n")
                skip_mapping = False
        return skip_mapping
    
    def load_full_cabling_from_file(self,_input_file_name):
        """This function opens the yaml input file and generates the SMU->DUT and 
        the DUT->SMU tables
        """
        self._global_map_dict = load_yaml_file(_input_file_name)
        self.DUT_2_SMU = {}
        self.SMU_2_DUT = {}
        for k,v in self._global_map_dict["cabling map"].items():
            self.DUT_2_SMU[str(k)] = v
            self.SMU_2_DUT[str(v)] = k

    def write_full_cabling_config_file(self,_input_dict):
        """Given a DUT-SMU map dictionary, this function creates a yaml file with the 
        full cabling chain, that means the SMU channel corresponding to each DUT probing pad"""
        file_name = 'full_cabling_chain.yml'
        _dict = {}
        _dict['cabling map'] = _input_dict
        _dict['info'] = "Automatically generated yaml file containing the full cabling description of the measurement setup" 
        with open(os.path.join(self._folder_dir,file_name), 'w') as outfile:
            yaml.dump(_dict, outfile, default_flow_style=False)
            print("file {} created and saved".format(outfile.name))

    def get_pads_from_channels(self, ch):
        # AB: I suspect this function to be useless
        """ Converts the channels to pad names based on the probecard layout,
        which has been defined in make_DUT_SMU_tables() or has been provided through EDF
        INPUT
        -----
        args:
            ch: channel(s), Note: each channel is defined as ['smux','x']
            OUTPUT
            ------
            if ch is a string (1 channel only) returns  pad name (string)
            else returns list of pads
        """
	   # TODO: write doctest
	   #raise ValueError('TODO: Test get_pads_from_channels.')
        if not isinstance(ch[0],list): #if ch is not already a list of lists, converts it into a list of list 
            ch = [ch]

        pads = []
        for c in ch:
            print('c is', c)
            p =[k for k,v in self.DUT_2_SMU.items() if v==c]
            pads.extend(p)

        return pads
    
    def get_channels_from_pads(self, pads):
        # AB: I suspect this function to be useless
        """ Converts the pad names to SMU channels based on the probecard layout,
        which has been defined in make_DUT_SMU_tables() or has been provided through EDF
        INPUT
        -----
        args:
            ch: pad(s)
        OUTPUT
        ------
        if pad is a string (1 channel only) returns channel name (list of [string,string])
        else returns list of lists
        """
	# TODO: write doctest
	#raise ValueError('TODO: Test get_pads_from_channels.')
        if not isinstance(pads, list):
            pads = [pads] 

        ch = []
        for p in pads:
            print('p is', p)
            c =[v for k,v in self.DUT_2_SMU.items() if k==p]
            ch.extend(c)

        return ch
    
if __name__ == '__main__':

    c = Full_Cabling(probecard_path = 'PM-V2.yaml', local_dir = '.')
    
