# -*- coding: utf-8 -*-
"""
Created on Fri Jun 29 09:46:01 2018

@author: KostasVoutyras

v0.0.2 Aug 21st, 2018 - Changed alignment process. Removed go_to_first_cell from start_alignment_process_
v0.0.3 Aug 29th, 2018 - get_coordinates to store initial x0,y0 as self.x0, self.y0
22-6-2022 EHN:
    update location for selecting probe height
"""

class AlignSample:



    def __init__(self):
        """
        """
        self.is_aligned=False
        self.counter=0

    def start_alignment_process_(self,eq, first_cell):
        """
        """
        self.eq=eq
        self.p=self.eq.prober

        self.p.set_chuck_vacuum(on=True)

        self.bring_chuck_to_center()
        self.correct_sample_rotation()
        self.set_probing_height(cell_name=first_cell)
        self.x0,self.y0 = self.get_coordinates()


    def change_probing_equipment(self):
        """
        """
        #if self.p.get_serial_number()=='157':

        print('*** OPERATOR INSTRUCTIONS***')
        print ('1. Open door')
        print ('2. Open top lid')
        print ('3. Insert probecard; push until firm.')
        print ('4. Screw probecard 1-3-2-4, until hand tight.')
        print ('5. Close top lid')
        print ('6. Close door')
        print ('7. Press OK when done')

        # Move chuck to safe position
        self.p.set_light(on=True)
        self.p.move_to_change_probecard_position()

        inp=input('\nPress enter when done:')
        if inp:
            self.counter=1


    def bring_chuck_to_center(self):
        """I need to see how this works with the prober
        """
        self.p.move_to_probing_zone_center()
#         inp=input('\nPress enter when done:')
#         if inp:
#             self.counter=2


    def correct_sample_rotation(self):
        """
        """
        print('Correct the sample rotation')
        self.p.run_alignment_screen_plus_set_focus()

        inp=input('\nPress enter when done:')
        if inp:
            self.counter=3

    def go_to_first_cell(self, cell_name):
        """OBSOLETE
        """
        self.p.set_light(on=True)
        print ('Press 5. Manual control')
        print ('Use the joystick to go to cell:',cell_name)
        self.p.exit_remote_mode()
        print('Probe the cell')
        print('Put the tool in Remote mode')
        print('press F5 Back')
        print('press 1.Remote')
        inp=input('\nPress enter when done:')
        if inp:
            self.counter=4

    def set_probing_height(self,cell_name):
        pass
        print('Press the RIGHT red button to toggle to XY')
        print('Use the joystick to go to cell:',cell_name)
        print('Press the RIGHT red button to toggle to Z')
        print('Move chuck up UNTIL the first Edge Sensor Opens.')
        
        self.p.go_to_xy('001250','102485') #updated after maintenance. 
        self.p.run_probe_height_screen()
        inp=input('\nPress enter when done:')
        if inp:
            self.counter=5
        
    def get_coordinates(self):
        '''Returns a tuple with the chuck coords in microns
        '''
        x0,y0=self.p.get_chuck_xy()
#         inp=input('Getting chuck coords...\nPress enter when done:')
#         if inp:
#             self.counter=6

        return (x0,y0)

    def is_sample_aligned(self):
        """
        """
        if self.counter==6:
            self.is_aligned=True

        return self.is_aligned

    def set_sample_aligned(self,aligned):
        """
        """
        self.is_aligned=aligned


if __name__=='__main__':
    from equipment import Equipment

    eq=Equipment(fullpath='readers/wp_edf.yaml')
    #a=AlignSample()
    #a.start_alignment_process_(eq, first_cell='dummy')