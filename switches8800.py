# 2025 - Generated and debugged by Microsoft Copilot, integrated by Dave Dempski

# Class to realize Altair 8800 front panel switches

import tkinter as tk
import threading
import time
import sys
import os

switch_info = { # X, Y, type, Label
    0:  [26, 207, "toggle", "Power"],

    1:  [728, 152, "toggle", "A0"],
    2:  [696, 152, "toggle", "A1"],
    3:  [664, 152, "toggle", "A2"],
    4:  [616, 152, "toggle", "A3"],
    5:  [584, 152, "toggle", "A4"],
    6:  [552, 152, "toggle", "A5"],
    7:  [504, 152, "toggle", "A6"],
    8:  [472, 152, "toggle", "A7"],
    9:  [440, 152, "toggle", "A8"],
    10:  [394, 152, "toggle", "A9"],
    11:  [362, 152, "toggle", "A10"],
    12:  [330, 152, "toggle", "A11"],
    13:  [284, 152, "toggle", "A12"],
    14:  [252, 152, "toggle", "A13"],
    15:  [220, 152, "toggle", "A14"],
    16:  [174, 152, "toggle", "A15"],

    17:  [616, 210, "momentary", "AUX1"],
    18:  [552, 210, "momentary", "AUX2"],
    19:  [490, 210, "momentary", "PROTECT"],
    20:  [426, 210, "momentary", "RESET"],
    21:  [364, 210, "momentary", "DEPOSIT"],
    22:  [300, 210, "momentary", "EXAMINE"],
    23:  [236, 210, "momentary", "SINGLE STEP"],
    24:  [174, 210, "momentary", "STOP"]
}

class Switch:
    def __init__(self, canvas, x, y, name, switch_type='toggle', initial_state='off', root=None, altair_instance=None, switch_number=0):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.name = name
        self.switch_type = switch_type
        self.state = initial_state
        self.reverse = False
        self.root = root
        self.altair_instance = altair_instance
        self.switchno = switch_number
        self.resetting = False
        # Draw the switch collar (circle)
        self.collar = canvas.create_oval(x-7.5, y-7.5, x+7.5, y+7.5, fill='dark gray')
        
        # Draw the switch pole (rectangle)
        if self.state == 'on':
            self.pole = canvas.create_rectangle(x-1.5, y-7.5, x+1.5, y+7.5, fill='light gray')
        else:
            self.pole = canvas.create_rectangle(x-1.5, y-7.5, x+1.5, y+7.5, fill='light gray')
            self.canvas.move(self.pole, 0, 10)  # Move down to turn off
        
        # Bind mouse click events
        canvas.tag_bind(self.collar, '<Button-1>', self.toggle_switch)
        canvas.tag_bind(self.pole, '<Button-1>', self.toggle_switch)
        
        # Default event functions
        self.on_toggle_on = lambda: print(f"{self.name}:{self.switchno} toggled on")
        self.on_toggle_off = lambda: print(f"{self.name}:{self.switchno} toggled off")
        self.on_momentary_up = lambda: print(f"{self.name} momentarily toggled up")
        self.on_momentary_down = lambda: print(f"{self.name} momentarily toggled down")
    

    def start_if_not_running(self, altair_instance, callback):
        if not altair_instance.running:                
            print("Power ON")
            threading.Thread(target=callback).start()            
  

    def turn_altair_off(self, altair_instance): 
        altair_instance.running = False
        if self.root:
            self.root.destroy()  # Add this line to close the program
        print("Power OFF")
        os._exit(0)


    def register_power_callback(self, altair_instance, callback):
        if self.name == "Power":
            # Power button is a reversed toggle: Up power off/Down power on
            #self.on_toggle_off = lambda: threading.Thread(target=callback).start()
            self.on_toggle_off = lambda: self.start_if_not_running(altair_instance, callback)
            self.on_toggle_on = lambda: self.turn_altair_off(altair_instance)


    def toggle_switch(self, event):
        if self.switch_type == 'toggle':
            if self.state == 'on':
                self.state = 'off'
                self.canvas.move(self.pole, 0, 10)  # Move down to turn off
                self.on_toggle_off()
            else:
                self.state = 'on'
                self.canvas.move(self.pole, 0, -10)  # Move up to turn on
                self.on_toggle_on()
        elif self.switch_type == 'momentary':
            if self.resetting == False:
                if event.y < self.y:
                    self.state = 'up'
                    self.canvas.move(self.pole, 0, -10)
                    self.on_momentary_up()
                    self.resetting = True
                    self.canvas.after(200, self.reset_switch)
                else:
                    self.state = 'down'
                    self.canvas.move(self.pole, 0, 10)
                    self.on_momentary_down()
                    self.resetting = True
                    self.canvas.after(200, self.reset_switch)
          
    
    def get_status(self):
        if self.reverse == True:
            if self.state == 'off':
                return 'on'
            else:
                return 'off'
        else:
            return self.state
        
    
    def register_event_functions(self, on_toggle_on=None, on_toggle_off=None,
                                 on_momentary_up=None, on_momentary_down=None):
        if on_toggle_on:
            self.on_toggle_on = on_toggle_on
        if on_toggle_off:
            self.on_toggle_off = on_toggle_off
        if on_momentary_up:
            self.on_momentary_up = on_momentary_up
        if on_momentary_down:
            self.on_momentary_down = on_momentary_down

    
    def change_switch_type(self, new_type):
        if new_type not in ['toggle', 'momentary']:
            raise ValueError("Invalid switch type. Must be 'toggle' or 'momentary'.")
        
        # Reset the state based on the new switch type
        if new_type == 'toggle':
            if self.switch_type == 'momentary' and self.state != 'center':
                # Move the pole back to center before changing to toggle
                if self.state == 'up':
                    self.canvas.move(self.pole, 0, 10)
                elif self.state == 'down':
                    self.canvas.move(self.pole, 0, -10)
            self.state = 'off'
        
        elif new_type == 'momentary':
            if self.switch_type == 'toggle':
                # Move the pole back to off position before changing to momentary
                self.canvas.move(self.pole, 0, -10)
                self.state = 'center'
        
        # Update the switch type
        self.switch_type = new_type


    def move_to(self, new_x, new_y):
            dx = new_x - self.x
            dy = new_y - self.y
            # Move the collar and pole by the calculated distance
            self.canvas.move(self.collar, dx, dy)
            self.canvas.move(self.pole, dx, dy)
            
            # Update the switch's coordinates
            self.x = new_x
            self.y = new_y


    def switch_label(self, labeltext):
        self.name = labeltext


    def reverse_toggle_action(self):
        if self.switch_type == 'toggle':
            self.reverse = True
            self.on_toggle_on = lambda: print(f"{self.name} toggled off") 
            self.on_toggle_off = lambda: print(f"{self.name} toggled on")


    def set_initial_state(self, state):
        if state not in ['off', 'on']:
            raise ValueError("Invalid state. Must be 'off' or 'on'.")
        
        if self.reverse == True:
            if state == 'on':
                state = 'off'
            else:
                state = 'on'
                
        # Set the initial state of the toggle switch
        if state == 'on' and self.state != 'on':
            self.canvas.move(self.pole, 0, -10)  # Move down to turn off
            self.state = 'on'
        elif state == 'off' and self.state != 'off':
            self.canvas.move(self.pole, 0, 10)  # Move up to turn on            
            self.state = 'off'


    def simulate_momentary_down(self):
        # Simulate the down engagement
        self.state = 'down'
        self.canvas.move(self.pole, 0, 10)  # Move down to simulate engagement
        self.on_momentary_down()  # Call the momentary down event function
        
        # Schedule the switch to return to its original position after 200 milliseconds
        self.canvas.after(200, self.reset_switch)
        
    
    def reset_switch(self):
        if self.state == 'up':
            self.canvas.move(self.pole, 0, 10) # Move down to reset position
        elif self.state == 'down':
            self.canvas.move(self.pole, 0, -10) # Move up to reset position
        self.state = 'center'
        self.resetting = False
        

