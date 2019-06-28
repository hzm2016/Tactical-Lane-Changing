# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 11:58:37 2019

@author: Baris ALHAN
"""

class gameDynamics:
    '''
        The class for the settings of the more dynamic variables that may
        desired to be changed in each simulation scenerios independent of the
        game mode.
        
        @Params:
            num_cars:
            num_actions:
            desired_min_speed:
            desired_max_speed:
            max_veh_inlane:    
                
    '''
    def __init__(self, num_cars = 9, num_actions = 3, max_veh_inlane = 20, desired_min_v = 18, desired_max_v = 26)):
        self._num_cars = num_cars
        self._num_actions = num_actions
        self._max_veh_inlane = max_veh_inlane
        self._desired_min_v = desired_min_v
        self._desired_max_v = desired_max_v