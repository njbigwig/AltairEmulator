# 2025 - Generated and debugged by Microsoft Copilot, integrated by Dave Dempski

# Class to realize Altair 8800 front panel LEDs

import tkinter as tk

led_info = { # X, Y, Label
    # Data LEDs
    0:  [731, 28, "D0"],
    1:  [697, 28, "D1"],
    2:  [663, 28, "D2"],
    3:  [618, 28, "D3"],
    4:  [584, 28, "D4"],
    5:  [550, 28, "D5"],
    6:  [504, 28, "D6"],
    7:  [470, 28, "D7"],

    # Address LEDs
    8:  [731, 89, "A0"],
    9:  [697, 89, "A1"],
    10: [663, 89, "A2"],
    11: [618, 89, "A3"],
    12: [584, 89, "A4"],
    13: [550, 89, "A5"],
    14: [504, 89, "A6"],
    15: [470, 89, "A7"],
    16: [439, 89, "A8"],
    17: [393, 89, "A9"],
    18: [359, 89, "A10"],
    19: [328, 89, "A11"],
    20: [281, 89, "A12"],
    21: [247, 89, "A13"],
    22: [218, 89, "A14"],
    23: [171, 89, "A15"],

    24: [108, 88, "HLDA"],
    25: [77, 88, "WAIT"],

    26: [360, 25, "INT"],
    27: [326, 25, "WO"],
    28: [292, 25, "STACK"],
    29: [262, 25, "HLTA"],

    30: [231, 25, "OUT"],
    31: [200, 25, "MI"],
    32: [168, 25, "INP"],
    33: [137, 25, "MEMR"],

    34: [106, 25, "PROT"],
    35: [70, 25, "INTE"]
}

class LED:
    def __init__(self, canvas, x, y, name=""):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.name = name
        self.state = False  # OFF by default
        self.diameter = 15
        self.off_color = "#8B0000"  # Dark red
        self.on_color = "#FF0000"   # Bright red
        self.led = self.canvas.create_oval(
            self.x - self.diameter / 2, self.y - self.diameter / 2,
            self.x + self.diameter / 2, self.y + self.diameter / 2,
            fill=self.off_color, outline=self.off_color
        )


    def turn_on(self):
        self.state = True
        self.canvas.itemconfig(self.led, fill=self.on_color, outline=self.on_color)


    def turn_off(self):
        self.state = False
        self.canvas.itemconfig(self.led, fill=self.off_color, outline=self.off_color)


    def get_status(self):
        return self.state


    def set_name(self, name):
        self.name = name


    def move_to(self, x, y):
        self.x = x
        self.y = y
        self.canvas.coords(
            self.led,
            self.x - self.diameter / 2, self.y - self.diameter / 2,
            self.x + self.diameter / 2, self.y + self.diameter / 2
        )

