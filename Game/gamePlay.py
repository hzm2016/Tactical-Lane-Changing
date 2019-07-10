# -*- coding: utf-8 -*-
"""
Created on Thu Jun 27 12:02:26 2019

@author: Baris ALHAN
"""
import Vehicle.VehicleControlModel
import Vehicle.VehicleDynamics

import numpy as np
import pygame 
from pygame.locals import *

class gamePlay:
    '''
        The class that actions of the game happens. We could think this
        class as the brain of the entire project.
        
        All the velocity calculations are made in the unit of m/s.
        
        # TODO: gym will be connected to here.
    '''
    # TODO: add reset method.
    def __init__(self, mode, dynamics, veh_props, veh_model, AIController):

        #######################################################################
        #####                       INITIALIZATION                        #####
        #######################################################################
        self._mode = mode
        self._dynamics = dynamics
        self._veh_props = veh_props
        self._veh_model = veh_model
        self._AIController = AIController
        #######################################################################
        #######################################################################
        
        # TODO: think about whether it is necessary or not.
        # time tick of the simulation (s)
        self._time = 0
        
        
        self._window_width = int(self._dynamics._max_veh_inlane * 
                               (self._veh_props._width + 2 * self._veh_props._height))
        self._window_height = int((self._veh_props._height +  2 * (self._veh_props._height // 2.5)) * self._dynamics._num_lane )

        
        #######################################################################
        #####                           VEHICLES                          #####
        #######################################################################
        # The id of the ego vehicle.
        self._ego_id = int((self._dynamics._num_veh-1)/2)
        
        # Coordinates of the each vehicle [LaneID : X_pos]
        self._veh_coordinates = self.generate_init_points()
        # Velocities of the each vehicle (m/s)
        self._velocities = self.generate_init_velocities()
        
        # The velocity of the ego vehicle (m/s)
        self._ego_v = self._init_velocities[self._ego_id]
        
        # The list that stores the desired max. velocities for the each vehicle 
        self._desired_v = self.calculate_desired_v(self._dynamics._desired_min_v,
                                                            self._dynamics._desired_max_v)
        
        # The lists that stores the velocity and distance differences with the front vehicle for each vehicle
        self._delta_v, self._delta_dist = self.generate_deltas(self._veh_coordinates, self._velocities)
        #######################################################################
        #######################################################################

    ###########################################################################
        
        
    
    '''
     The method generates the initial positions of vehicles.
     
     Aim: Vehicles are distributed to the highway without collisions.
     
     The algorithm is as follows:
         1. Assign each vehicle to a free lane
             (For each lane evaluate the exact position of each vehicle.)
             2. For each lane in lanes:
                 3. First, randomly calculate a point
                    for the first car in that lane.
                 4. Afterwards, assign a position to the remanining
                    vehicles one by one, ensuring that they do not collide.
     
    The coordinates list is sorted at the end and the ego vehicle is always the
    vehicle in the middle.
        
     Inputs: init_range, delta_dist
         init_range : range of the initialization horizon(meters)
         delta_dist: minimum distance between vehicles (meters)
         
     Outputs: coordinates,init_v
         coordinates : Position of each vehicle
         init_v      : Initial speed for each vehicle
    '''
    def generate_init_points(self, init_range = 200, delta_dist = 25):
        
        # Safety check for the distance of the vehicles.
        if delta_dist<10 :
            delta_dist = 10
            
        #The result list stores the lane of each vehicle.
        lane_list = []
        #The result list stores the coordinates of each vehicle.
        #[LaneID, X_pos)]
        coordinates = np.zeros((self._dynamics._num_veh, 2))
        
               
        #first randomly select lanes for each vehicle
        for car in range(0, self._dynamics._num_veh):
            # Randomly chose lane id for each vehicle
            lane_list.append(np.random.randint(0, self._dynamics._num_lane))  
        
        #The map that stores [LaneID <-> number of cars in that lane]
        fullness_of_lanes = {x: lane_list.count(x) for x in lane_list}        
        
        # Temporary list to store the coordinates of the each vehicle.
        # [(LaneID : X_position)]
        tmp_coordinates = []
        
        # 2nd step of the algorithm.
        for lane, num_vehicles_inlane in fullness_of_lanes.items():
            # Temporary point list in the x direction
            # to store the positions of the vehicles.
            tmp_points = list([])
            # First, chose a point for the first vehicle in the selected lane
            # The second parameter in the randomness ensures that there is no
            # accumulation of cars at the end of the inital range.
            tmp_points.append(np.random.uniform(0 , init_range - ((num_vehicles_inlane - 1) * delta_dist) ))
            
            tmp_coordinates.append([lane, tmp_points[-1]])
            for car_id in range(0, num_vehicles_inlane - 1):
                # put other vehicles in that lane to the remaining space
                tmp_points.append(np.random.uniform(tmp_points[-1] + delta_dist,
                                                    (init_range - (num_vehicles_inlane - 2 - car_id) * delta_dist)))
                tmp_coordinates.append([lane, tmp_points[-1]])
                
        coordinates = np.asarray(tmp_coordinates).reshape(coordinates.shape)
        coordinates = coordinates[coordinates[:, 1].argsort()]
        # TODO : Ask what's going on here!
        coordinates[:, 1] = coordinates[:, 1] - coordinates[self._ego_id, 1] + self._window_width / 20
    
        return coordinates     
     
    
    # The method that returns the initial velocities of the vehicles.    
    def generate_init_velocities(self):
        
        #The result list stores the initial velocities of each vehicle.
        init_v = np.zeros((self._dynamics._num_veh, 1))
        
        # initial velocities for the ego vehicle => 10m/s 15 m/s
        # TODO: parametrize here!
        init_v[self._ego_id] = np.random.uniform(10, 15)

        for rear_id in range(0, self._ego_id):
             # 26.4, 33.3  , randomly define initial speeds for rear vehicles  
            init_v[rear_id] = np.random.uniform(15, 25) 
        for front_id in range(self._ego_id + 1, self._dynamics._num_veh):
             # 16.7, 23.6 , randomly define initial speeds for front vehicles
            init_v[front_id] = np.random.uniform(10, 12) 
        
        return init_v    
        
    # TODO: ask what's going on here.
    # Calucate delta_v and delta_dist.
    def generate_deltas(self, current_states, current_v):
        
        num_veh = self._dynamics._num_veh
        num_lane = self._dynamics._num_lane
        
        delta_v = np.zeros((num_veh, 1))
        delta_dist = np.zeros((num_veh, 1))
        
        for lane_id in range(num_lane):
            
            idx = np.where(current_states[:, 0] == lane_id)
            sorted_idx = np.argsort(current_states[idx, 1])
            idx_new = idx[0][sorted_idx]

            dummy_v = 0        # If there id no vehicle in front d_v equals to 0
            dummy_s = 10 ** 5  # If there id no vehicle in front d_s equals to 100000 m
            for x, val in reversed(list(enumerate(idx_new[0]))):
                if dummy_v == 0:
                    dummy_v = current_v[val]
                delta_v[val] = current_v[val] - dummy_v
                delta_dist[val] = dummy_s - current_states[val, 1] - 0
                dummy_v = current_v[val]
                dummy_s = current_states[val, 1]
        return delta_v, delta_dist
    
    
    # The method calculates the desired max. velocities for the each vehicle.
    # The desired max. velocity of the ego car is 25 m/s
    def calculate_desired_v(self, desired_min_v, desired_max_v):
        
        result = np.random.uniform(desired_min_v, desired_max_v, self._dynamics._num_veh)
        result[self._ego_id] = np.array([25])
        result.shape = (len(result), 1)
        result = result[0 : self._dynamics._num_veh]
        
        return result
        
    
    
    # TODO: understand the method.
    def render(self, mode = 'human'):
        return 0
   
    
    
    # PyGame related function.
    def terminate(self):
        pygame.quit()
        return False 
    
    # PyGame related function.
    def wait_for_player_to_press_key(self):
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.terminate()
                if event.type == pygame.KEYDOWN:
                    # escape quits
                    if event.key == pygame.K_ESCAPE:  
                        self.terminate()
                        return
                    elif event.key == pygame.K_LEFT:
                        return -1
                    elif event.key == pygame.K_RIGHT:
                        return 1
                    else:
                        return 0
        
    
    
    # TODO: explain the general algorithm.
    def step(self, action):
        
        # holds whether the RL episode done or not.
        is_done = False
        # If ego vehicle get too close with any other vehicle 
        # the near_collision becomes true
        near_collision = False;
        # If ego vehicle collides with any other vehicle
        # hard_collision becomes true.
        hard_collision = False;
        # The reward of the RL
        reward = 0.0
        # The list that holds the lane change decisions of the vehicles.
        # Decisions of the ego vehicle are determined by RL if it is enabled,
        # else it is directly taken from the user input.
        # Decisions of the other vehicles are determined by the movement model.
        decisions = np.zeros((self._dynamics._num_veh,1))
        # We can think this list as the priority level of each vehicle 
        # to change the lane. During the execution, the vehicle with top priority
        # will change the lane first.
        gains = np.zeros((self._dynamics._num_veh,1))
        
        #######################################################################
        #####                            AIController                    ######
        #######################################################################
        acceleration = self._AIController.IDM(self._velocities, self._desired_v,
                                              self._delta_v, self._delta_dist)
        
        if self._mode._rule_mode == 1 or self._mode._rule_mode == 2:
           if self._time > 0:
               for veh in range(0,self._dynamics._num_veh):
                   # Finding the surrounding vehicles.
                   ll_id, lf_id, ml_id, mf_id, rl_id, rf_id = self._AIController.get_surrounding_vehs(self._veh_coordinates, veh)
                   
                   decisions[veh], gains[veh] = self._AIController.MOBIL(veh, self._veh_coordinates,
                                        acceleration, self._velocities, self._desired_v, 
                                                ll_id, lf_id, ml_id, mf_id, rl_id, rf_id)
                   
        #######################################################################
        #######################################################################

    