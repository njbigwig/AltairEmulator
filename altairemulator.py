# March 2025 Concept by Dave Dempski with much help from Microsoft Copilot!

# Celebrating Microsoft's 50th anniversary by emulating one the first products Micro-Soft launched: Altair 4K BASIC!


from opcodes import opcodes_8080
import winsound
import msvcrt
import time
import tkinter as tk
from tkinter import scrolledtext, filedialog
from PIL import Image, ImageTk
import threading
import os
import argparse
import datetime
import leds8800
import switches8800

# Support for USR(0) - return Sense switch settings
usrfn_code=[
0xDB, # IN
0xFF, # Port = 0xFF (255)
0x47, # MOV B,A
0xAF, # XRA A
0x2A, # LHLD
0x06, # 0x0006 = 0x07F9 -> FWordToFloat
0x00, #
0xE9  # PCHL
]

# LED definitions
HLDA_LED = 24
WAIT_LED = 25
INT_LED = 26
WO_LED = 27
STACK_LED = 28 
HLTA_LED = 29
OUT_LED = 30
MI_LED = 31
INP_LED = 32   
MEMR_LED = 33 
PROT_LED = 34
INTE_LED = 35

# Switch definition
POWER_SWITCH = 0
RESETCLR_SWITCH = 20
DEPOSIT_SWITCH = 21
EXAMINE_SWITCH = 22
SINGLESTEP_SWITCH = 23
STOP_SWITCH = 24

AO_SWITCH = 1
A1_SWITCH = 2
A2_SWITCH = 3
A3_SWITCH = 4
A4_SWITCH = 5
A5_SWITCH = 6
A6_SWITCH = 7
A7_SWITCH = 8
A8_SWITCH = 9
A9_SWITCH = 10
A10_SWITCH = 11
A11_SWITCH = 12
A12_SWITCH = 13
A13_SWITCH = 14
A14_SWITCH = 15
A15_SWITCH = 16

# Front panel equipment definitions
ALTAIR_LEDS = 36
ALTAIR_SWITCHES = 25

USRFN_ADDR = 0x0FF0

# Global variables
emulator_parser = None
emulator_args = None

# Custom type function to validate hexadecimal input
def hex_type(value):
    try:
        # Convert the input to an integer with base 16
        int_value = int(value, 16)
        # Ensure it's a 4-digit hexadecimal number
        if len(value) != 4:
            raise argparse.ArgumentTypeError(f"{value} is not a 4-digit hexadecimal number")
        return value
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value} is not a valid hexadecimal number")

class Altair8800:
    def __init__(self, text_widget, canvas, root):
        self.memory = [0] * 65536  # 64KB memory
        self.registers = {
            'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'H': 0, 'L': 0,
            'PC': 0, 'SP': 0xFFFF, 'FLAGS': 0x02
        }
        self.rom_file = None
        self.inputbuffer = []
        self.inputchar = 0x00    
        self.interrupt_enabled = False
        self.altair_singlestep = False
        self.singlestep = False
        self.breakpoints = []
        self.running = False
        self.debuglevel = 0
        self.debuglogger = False
        self.debugloggerfile = None
        self.text_widget = text_widget
        self.load_button = None
        self.running = False
        self.canvas = canvas
        self.root = root
        self.leds = []
        self.create_leds()
        self.switches = [] 
        self.create_switches()
        self.sense_switches = 0x00 # upper 8 bits from Address switches A15 - A8
        self.data_switches = 0x00
        self.address_switches = 0x0000     
        self.address_lock = False   
        self.ttycount = 0
        self.create_load_button()
        self.play_sound = True
        self.usrfunction = False

    def create_leds(self):
        # Create 36 LED objects
        for i in range(ALTAIR_LEDS):
            x = 20 + (i % 12) * 20  # Example x coordinate
            y = 20 + (i // 12) * 20  # Example y coordinate
            led = leds8800.LED(self.canvas, x, y, f"LED {i+1}")
            self.leds.append(led)

        # Add the LEDs to the front panel at specified (X,Y) coordidates
        for ledno in range(0,len(leds8800.led_info)):
            self.leds[ledno].turn_off()
            self.leds[ledno].move_to(leds8800.led_info[ledno][0], leds8800.led_info[ledno][1])
            self.leds[ledno].set_name(leds8800.led_info[ledno][2])  


    def set_data_leds(self, value):
        bitno = 0x01       
        
        for led in range(0, 8):            
            if bitno & value:
                self.leds[led].turn_on()
            else:
                self.leds[led].turn_off()
            bitno = bitno << 1

        if self.debuglevel >= 2:
            print(f"Data LEDs: 0x{value:02X}")


    def set_address_leds(self, value):
        bitno = 0x0001       
        
        for led in range(8, 24):            
            if bitno & value:
                self.leds[led].turn_on()
            else:
                self.leds[led].turn_off()
            bitno = bitno << 1

        if self.debuglevel >= 2:
            print(f"Address LEDs: 0x{value:04X}")


    def stop_altair(self):
        if self.singlestep == False:
            self.altair_singlestep = True
            print("\n\nAltair 8800 Stopped.\n")


    def run_altair(self):
        if self.altair_singlestep == True:
            self.altair_singlestep = False
            self.address_lock = False
            print("\n\nAltair 8800 Running....\n\n")


    def nextcmd_altair(self):
        if self.altair_singlestep == True:               
            print(f"Altair Single Step: PC=0x{self.registers['PC']:04X}")
            self.inputbuffer.append(0x0D)


    def reset_altair(self):
        if self.altair_singlestep == True:
            print("Reset Altair: PC=0x0000")
            self.registers['A'] = 0x00
            self.registers['B'] = 0x00
            self.registers['C'] = 0x00
            self.registers['D'] = 0x00
            self.registers['E'] = 0x00
            self.registers['H'] = 0x00
            self.registers['L'] = 0x00
            self.registers['PC'] = 0x0000
            self.registers['SP'] = 0xFFFF
            self.registers['FLAGS'] = 0x02
            #self.inputbuffer.append(0x0D)


    def switch_positions(self):
        bit = 0x0001

        self.address_switches = 0x0000

        for switch in range(AO_SWITCH, A15_SWITCH+1):
            if self.switches[switch].get_status() == 'on':
                 self.address_switches |= bit

            bit = bit << 1

        self.sense_switches = self.address_switches >> 8
        self.data_switches = self.address_switches & 0xFF    


    def data_switch_positions(self):
        bit = 0x01

        self.data_switches = 0x00

        for switch in range(AO_SWITCH, A7_SWITCH+1):
            if self.switches[switch].get_status() == 'on':
                 self.data_switches |= bit

            bit = bit << 1           
                 

    def addressdata_on(self, switchno):
          biton = 0x0001
          biton = biton << (switchno-1)
          temp = self.address_switches
          temp |= biton

          if self.address_lock == False:
              self.address_switches = temp

          self.sense_switches = temp >> 8
          self.data_switches = temp & 0xFF
    
          if self.debuglevel >= 2:
            print(f"Address-Data Switches: 0x{self.address_switches:04X} Sense: 0x{self.sense_switches:02X} Data: 0x{self.data_switches:02X}")


    def addressdata_off(self, switchno):
          biton = 0x0001
          biton = biton << (switchno-1)
          temp = self.address_switches
          temp &= ~biton

          if self.address_lock == False:
              self.address_switches = temp

          self.sense_switches = temp >> 8
          self.data_switches = temp & 0xFF

          if self.debuglevel >= 2:
            print(f"Address-Data Switches: 0x{self.address_switches:04X} Sense: 0x{self.sense_switches:02X} Data: 0x{self.data_switches:02X}")

    def deposit_memory(self):
       if self.altair_singlestep == True:
           self.data_switch_positions()
           self.set_address_leds(self.address_switches)
           self.set_data_leds(self.data_switches)

           self.memory[self.address_switches] = self.data_switches & 0xFF

           print(f"Deposit 0x{self.address_switches:04X} < 0x{self.data_switches:02X}")


    def depositnext_memory(self):
       if self.altair_singlestep == True:
           self.data_switch_positions()
           self.address_switches = (self.address_switches+1) % 0xFFFF
           self.set_address_leds(self.address_switches)
           self.set_data_leds(self.data_switches)

           self.memory[self.address_switches] = self.data_switches & 0xFF

           print(f"Deposit Next 0x{self.address_switches:04X} < 0x{self.data_switches:02X}")


    def examine_memory(self):
       if self.altair_singlestep == True:
           self.switch_positions()
           self.set_address_leds(self.address_switches)
           self.set_data_leds(self.memory[self.address_switches])

           self.address_lock = True

           print(f"Examine 0x{self.address_switches:04X} = 0x{self.memory[self.address_switches]:02X}")
       

    def examinenext_memory(self):
       if self.altair_singlestep == True:
           self.address_switches = (self.address_switches+1) % 0xFFFF
           self.set_address_leds(self.address_switches)
           self.set_data_leds(self.memory[self.address_switches])

           print(f"Examine Next 0x{self.address_switches:04X} = 0x{self.memory[self.address_switches]:02X}")


    def create_switches(self):
        # Create a list of 25 Switch objects
        for i in range(ALTAIR_SWITCHES):
            x = (i % 5) * 50 + 50
            y = (i // 5) * 50 + 50
            switch = switches8800.Switch(self.canvas, x, y, f'Switch {i+1}', root=self.root, altair_instance=self, switch_number=i)
            self.switches.append(switch)

        # Add the switches to the front panel at specified (X,Y) coordidates
        for switchno in range(0,len(switches8800.switch_info)):
            self.switches[switchno].move_to(switches8800.switch_info[switchno][0], switches8800.switch_info[switchno][1])
            self.switches[switchno].change_switch_type(switches8800.switch_info[switchno][2])

            if switches8800.switch_info[switchno][2] == "toggle":
                self.switches[switchno].set_initial_state('off')

            self.switches[switchno].switch_label(switches8800.switch_info[switchno][3])

            if switchno >= AO_SWITCH and switchno <= A15_SWITCH:
                self.switches[switchno].register_event_functions(on_toggle_on=lambda sn=switchno: self.addressdata_on(sn), on_toggle_off=lambda sn=switchno: self.addressdata_off(sn))

                
        # Altair Power switch toogle: Up=OFF/Down=On
        self.switches[POWER_SWITCH].reverse_toggle_action()
        self.switches[POWER_SWITCH].set_initial_state('off')

        # Register the power callback - turn on the Altair 8800 emulator
        self.switches[POWER_SWITCH].register_power_callback(self, self.execute)

        # Register Stop & Run switch callbacks 
        self.switches[STOP_SWITCH].register_event_functions(self, on_momentary_up=self.stop_altair, on_momentary_down=self.run_altair)
        self.switches[SINGLESTEP_SWITCH].register_event_functions(self, on_momentary_up=self.nextcmd_altair)
          
        # Register Reset & Clear switch callbacks
        #self.switches[RESETCLR_SWITCH].register_event_functions(self, on_momentary_up=self.reset_altair)

        # Register Examine Memory switch callbacks
        self.switches[EXAMINE_SWITCH].register_event_functions(self, on_momentary_up=self.examine_memory, on_momentary_down=self.examinenext_memory)

        # Register Deposit Memory switch callbacks
        self.switches[ DEPOSIT_SWITCH].register_event_functions(self, on_momentary_up=self.deposit_memory, on_momentary_down=self.depositnext_memory)
       
             
        
    def create_load_button(self):
        self.load_button = tk.Button(self.root, text="Load", command=self.load_text_file)
        #self.load_button.place(relx=0.70, rely=0.28, width=30, height=25)  # Use relative positioning #0.23
        self.load_button.place(relx=1.0, rely=1.0, anchor='se', x=-10, y=-10) 


    def load_text_file(self):
        # Open file selection dialog
        filename = filedialog.askopenfilename(
            initialdir=".",
            title="Select a BASIC Program File",
            filetypes=(("BAS files", "*.bas"), ("All files", "*.*")))
    
        # Check if a file was selected
        if filename:
            with open(filename, 'r') as file:
                for line in file:
                    for char in line:
                        self.inputbuffer.append(ord(char))
                    self.inputbuffer.append(ord('\r')) # Append carriage return character
                    self.inputbuffer.append(ord('\n')) # Append newline character
            print(f"Loaded {filename} into program memory.")                  
        

    def load_rom(self, filename):
        print("Loading binary...")
        
        with open(filename, 'rb') as f:
            rom = f.read()

            if len(rom) > len(self.memory):
                raise MemoryError("CRASH: ROM size exceeds memory size!")
            else:
                print(f"Program Size: {len(rom)}\n")

            for i in range(len(rom)):
                self.memory[i] = rom[i]   

        # change the FunctionCallError to the USR function at 0x0FF0
        if self.usrfunction == True:
            print("Changing FunctionCallError vector to USRFN\n")
            self.memory[0x0043] = 0xF0
            self.memory[0x0044] = 0x0F

            # Load the USR function address into the default EC error handler - pg 68 Altair BASIC manual   
            usrcode_ptr = USRFN_ADDR
            print("Adding USR() code:")
            for code in usrfn_code:
                self.memory[usrcode_ptr] = code    
                print(f"{usrcode_ptr:04X}:{code:02X}")
                usrcode_ptr += 1  

            print("\nUse Memory Size = 4080\n")

    def input_port(self, pc, port):        
            
            if port == 0x00 and pc == 0x0377:
                return 0x00 # simulate terminal is ready
            elif port == 0x00 and (pc == 0x0382 or pc == 0x0473):
                if len(self.inputbuffer) > 0:
                    return 0x00 # buffered characters
                
                if msvcrt.kbhit():
                    while msvcrt.kbhit() and self.running == True:
                        try:
                            cnc = msvcrt.getch().decode('utf-8')
                            c = cnc.upper()
                            self.inputbuffer.append(ord(c))
                        except UnicodeDecodeError:
                            # Skip characters that can't be decoded
                            continue
                    return 0x00  # TTY character received
                
                return 0x01  # No character received                    
            elif port == 0x01:
                if pc == 0x0D28:
                    return 0x0D
                else:
                    return self.inputbuffer.pop(0)                                               
            elif port == 0xFF:
                return self.sense_switches
            else:
                return int(input(f"Port: {port:02X} Input: "), 16)
         
    
    def play_sound_async(self, sound_file):
        winsound.PlaySound(sound_file, winsound.SND_FILENAME)


    def output_port(self, value, port):
        value &= 0x7F
        if port == 0x01:
            print(chr(value), end='')  # Print the ASCII character without a newline

            # process backspace
            if value == 0x08: 
                # Get the current cursor position
                cursor_pos = self.text_widget.index(tk.INSERT)

                # Check if the cursor is not at the beginning
                if cursor_pos != "1.0":
                    # Delete the character before the cursor
                    self.text_widget.delete(f"{cursor_pos} - 1 char", cursor_pos)
            else:
                self.text_widget.insert(tk.END, chr(value))  # Print to Tkinter text widget
                self.text_widget.see(tk.END)  # Scroll to the end

            self.ttycount = (self.ttycount+1) % 21
            if self.ttycount == 1:
                if self.play_sound == True:
                    # Play sound asynchronously
                    threading.Thread(target=self.play_sound_async, args=("ttyprinter2s.wav",)).start()             
            
        else:
            print(f"Port: {port:02X} Output: {value:02X}")


    def print_stack(self):
        print("Stack Dump:")
        for i in range(20):
            addr = self.registers['SP'] + i
            if addr < len(self.memory):
                print(f"Address {addr:04X}: {self.memory[addr]:02X}")
            else:
                print(f"Address {addr:04X}: Out of bounds")

        print("\n\n")


    def print_flags(self):
        print(f"Flags: {self.registers['FLAGS']:02X}")

        if self.registers['FLAGS'] & 0x80:
            print("  Sign: 1")
        else:
            print("  Sign: 0")

        if self.registers['FLAGS'] & 0x40:
            print("  Zero: 1")
        else:
            print("  Zero: 0")

        print("0")
        
        if self.registers['FLAGS'] & 0x10:
            print("    AC: 1")
        else:
            print("    AC: 0")

        print("0")

        if self.registers['FLAGS'] & 0x04:
            print("Parity: 1")
        else:
            print("Parity: 0")

        print("1")

        if self.registers['FLAGS'] & 0x01:
            print(" Carry: 1")
        else:
            print(" Carry: 0")


    def memory_dump(self):
        memstart = int(input(f"Input memory start address: "), 16)

        addr = memstart
        for i in range(20):
            
            if addr < len(self.memory):
                print(f"{addr:04X}: {self.memory[addr]:02X}")
            else:
                print(f"Address {addr:04X}: Out of bounds")

            addr += 1

        print("\n\n")


    def debug_addr_write(self, dbf, addr, value):
        if self.debuglogger == True:
            dbf.write(f"WRITE MEM {addr:04X} = {value:02X}\n")


    def debug_write(self, dbfile):
        dbfile.write(f"SP: {self.registers['SP']:04X}\n")
        dbfile.write(f"A Reg: {self.registers['A']:02X} | B Reg: {self.registers['B']:02X} | C Reg: {self.registers['C']:02X}\n")
        dbfile.write(f"D Reg: {self.registers['D']:02X} | E Reg: {self.registers['E']:02X} | Flags: {self.registers['FLAGS']:02X}\n")
        dbfile.write(f"H Reg: {self.registers['H']:02X} | L Reg: {self.registers['L']:02X}\n\n")


    def debug_memory_map(self):
        # memory map info
        print(f"SP=0x{self.registers['SP']:04X}")  

        addr = self.memory[0x0166]<<8 | self.memory[0x0165]
        print(f"Program Base=0x{addr:04X}") 

        addr = self.memory[0x0168]<<8 | self.memory[0x0167]
        print(f"Variable Base=0x{addr:04X}") 

        addr = self.memory[0x016A]<<8 | self.memory[0x0169]
        print(f"Variable Array Base=0x{addr:04X}") 

        addr = self.memory[0x016C]<<8 | self.memory[0x016B]
        print(f"Variable Top Base=0x{addr:04X}") 

        addr = self.memory[0x016E]<<8 | self.memory[0x016D]
        print(f"Data Program Pointer=0x{addr:04X}") 


    def debug(self):
        print(f"\nSP: {self.registers['SP']:04X}")
        print(f"A Reg: {self.registers['A']:02X} | B Reg: {self.registers['B']:02X} | C Reg: {self.registers['C']:02X}")
        print(f"D Reg: {self.registers['D']:02X} | E Reg: {self.registers['E']:02X} | Flags: {self.registers['FLAGS']:02X}")
        print(f"H Reg: {self.registers['H']:02X} | L Reg: {self.registers['L']:02X}")
        if self.singlestep == True:
            xxx = input("\n--Single Step: [ENTER] to step, mem, cont, stack or flags--\n").lower()
            if xxx == "stack":
                self.print_stack()
                xxx = input("\n[ENTER] to continue\n").lower()
            elif xxx == "flags":
                self.print_flags()
                xxx = input("\n[ENTER] to continue\n").lower()
            elif xxx == "mem":
                self.memory_dump()
                xxx = input("\n[ENTER] to continue\n").lower()
            elif xxx == "map":
                self.debug_memory_map()
                xxx = input("\n[ENTER] to continue\n").lower()
            elif xxx == "cont":
                self.singlestep = False
                self.debuglevel = 0            
        else:
            print("\n")
 

    def execute(self):
        # reduce delays from INPUT LED control
        inledcnt = 0

        self.running = True

        # simulate Altair 8800 powering up and reset
        self.leds[WAIT_LED].turn_on()
        self.leds[WO_LED].turn_on()
        self.leds[MI_LED].turn_on()
        self.leds[MEMR_LED].turn_on()
        self.set_data_leds(0xA7)
        self.set_address_leds(0xFB92)

        time.sleep(3)

        self.leds[WAIT_LED].turn_off()
        self.leds[WO_LED].turn_off()
        self.leds[MI_LED].turn_off() 
        self.leds[MEMR_LED].turn_off()           


        self.set_data_leds(0x00)
        self.set_address_leds(0x0000)

     
        if self.debuglogger == True:
            self.debugloggerfile = open("dblogger.txt", "w") 
              
        while self.running == True:
            pc = self.registers['PC']

            if pc >= len(self.memory):
                print(f"Exceeded program memory: PC={pc:04X}")
                self.running = False

            opcode = self.memory[pc] & 0xFF

            if self.altair_singlestep == True and self.address_lock == False:
                self.set_address_leds(pc)
                self.set_data_leds(opcode)
            
            if pc == self.registers['SP']:
                 self.leds[STACK_LED].turn_on()
            else:
                self.leds[STACK_LED].turn_off()

            # update the Opcode Histogram
            opcodes_8080[opcode][1] +=1

            now = datetime.datetime.now()

            if self.debuglevel >= 1:
                print(f"{now.hour}:{now.minute}:{now.second} {pc:04X} : {opcode:02X} {opcodes_8080[opcode][0]}")

            if self.debuglogger == True:
                self.debugloggerfile.write(f"{now.hour}:{now.minute}:{now.second} {pc:04X} : {opcode:02X} {opcodes_8080[opcode][0]}\n")
                self.debug_write(self.debugloggerfile)

            if pc in self.breakpoints:
                bpgo = input(f"\aBreakpoint at {pc:04X} - press [ENTER]\n")
                self.debuglevel = 2
                self.singlestep = True

            self.registers['PC'] += 1

            if opcode == 0x00:  # NOP
                if self.debuglevel >= 4:
                    print("NOP")
            elif opcode == 0x01: # LXI B, word
                self.registers['C'] = self.memory[self.registers['PC']]
                self.registers['B'] = self.memory[self.registers['PC'] + 1]
                self.registers['PC'] += 2
                
                if self.debuglevel >= 4:
                    print(f"LXI B : B={self.registers['B']:02X}, C={self.registers['C']:02X}")
            elif opcode == 0x02:  # STAX B
                addr = (self.registers['B'] << 8) | self.registers['C']  # Calculate the memory address from B and C registers
                self.memory[addr] = self.registers['A']  # Store the value of the accumulator into memory

                if self.debuglevel >= 4:
                    print(f"STAX B: {addr:04X}, A={self.registers['A']:02X}")

                self.debug_addr_write(self.debugloggerfile, addr, self.registers['A'])
            elif opcode == 0x03:  # INX B
                bc = (self.registers['B'] << 8) | self.registers['C']
                bc = (bc + 1) & 0xFFFF  # Ensure it wraps around at 16 bits
                self.registers['B'] = (bc >> 8) & 0xFF
                self.registers['C'] = bc & 0xFF

                if self.debuglevel >= 4:
                    print(f"INX B : B={self.registers['B']:02X}, C={self.registers['C']:02X}")
            elif opcode == 0x04: # INR B
                aux_carryflag_before = self.registers['B'] & 0x0F  # Save the lower nibble before increment
                self.registers['B'] = (self.registers['B'] + 1) & 0xFF  # Increment B and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag

                if self.registers['B'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['B'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['B']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if aux_carryflag_before + 1 > 0x0F:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag   

                if self.debuglevel >= 4:
                    print(f"INR B: B={self.registers['B']:02X}")                        
            elif opcode == 0x05: # DCR B
                aux_carryflag_before = self.registers['B'] & 0x0F  # Save the lower nibble before decrement
                self.registers['B'] = (self.registers['B'] - 1) & 0xFF  # Decrement B and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag

                if self.registers['B'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['B'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['B']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (aux_carryflag_before - 1) & 0x10 != 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                
                if self.debuglevel >= 4:
                    print(f"DCR B: B={self.registers['B']:02X}")
            elif opcode == 0x06:  # MVI B, byte
                self.registers['B'] = self.memory[self.registers['PC']]                

                if self.debuglevel >= 4:
                    print(f"MVI B, byte: {self.registers['PC']:04X}, B={self.registers['B']:02X}")

                self.registers['PC'] += 1
            elif opcode == 0x07:  # RLC
                carry = (self.registers['A'] & 0x80) >> 7  # Extract the most significant bit (bit 7)
                self.registers['A'] = ((self.registers['A'] << 1) & 0xFF) | carry  # Rotate left and set bit 0 to the carry

                # Clear flags
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                # Set the carry flag based on the rotated bit
                if carry:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"RLC: A={self.registers['A']:02X}")
            elif opcode == 0x08: # not ussed in 8080
                pass
            elif opcode == 0x09: # DAD B
                hl = (self.registers['H'] << 8) | self.registers['L']
                bc = (self.registers['B'] << 8) | self.registers['C']
                result = hl + bc
                self.registers['H'] = (result >> 8) & 0xFF
                self.registers['L'] = result & 0xFF

                # Update carry flag
                self.registers['FLAGS'] &= ~(1 << 0) # Clear carry flag
                if result > 0xFFFF:
                    self.registers['FLAGS'] |= (1 << 0) # Set carry flag

                if self.debuglevel >= 4:
                    print(f"DAD B : HL={hl:04X} + BC={bc:04X} = {result:04X}, CY={self.registers['FLAGS'] & 0x01}")
            elif opcode == 0x0A:  # LDAX B
                addr = (self.registers['B'] << 8) | self.registers['C']
                self.registers['A'] = self.memory[addr]
                
                if self.debuglevel >= 4:
                    print(f"LDAX B : A={self.registers['A']:02X}, [BC]={addr:04X} = {self.memory[addr]:02X}")
            elif opcode == 0x0B:  # DCX B
                bc = (self.registers['B'] << 8) | self.registers['C']
                bc = (bc - 1) & 0xFFFF  # Ensure it wraps around at 16 bits
                self.registers['B'] = (bc >> 8) & 0xFF
                self.registers['C'] = bc & 0xFF
                
                if self.debuglevel >= 4:
                    print(f"DCX B : B={self.registers['B']:02X}, C={self.registers['C']:02X}")
            elif opcode == 0x0C: # INR C
                aux_carryflag_before = self.registers['C'] & 0x0F  # Save the lower nibble before increment
                self.registers['C'] = (self.registers['C'] + 1) & 0xFF  # Increment C and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag

                if self.registers['C'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['C'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['C']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if aux_carryflag_before + 1 > 0x0F:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag   

                if self.debuglevel >= 4:
                    print(f"INR C: C={self.registers['C']:02X}")         
            elif opcode == 0x0D: # DCR C
                aux_carryflag_before = self.registers['C'] & 0x0F  # Save the lower nibble before decrement
                self.registers['C'] = (self.registers['C'] - 1) & 0xFF  # Decrement C and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag

                if self.registers['C'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['C'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['C']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (aux_carryflag_before - 1) & 0x10 != 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag

                if self.debuglevel >= 4:
                    print(f"DCR C: C={self.registers['C']:02X}")
            elif opcode == 0x0E:  # MVI C, byte
                self.registers['C'] = self.memory[self.registers['PC']]

                if self.debuglevel >= 4:
                    print(f"MVI C: C={self.registers['C']:02X} addr={self.registers['PC']:04X}")  

                self.registers['PC'] += 1
            elif opcode == 0x0F:  # RRC
                carry = self.registers['A'] & 0x01  # Extract the least significant bit (bit 0)
                self.registers['A'] = (self.registers['A'] >> 1) | (carry << 7)  # Rotate right and set bit 7 to the carry

                # Clear flags
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                # Set the carry flag based on the rotated bit
                if carry:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"RRC: A={self.registers['A']:02X}")  
            elif opcode == 0x10: # not ussed in 8080
                pass
            elif opcode == 0x11:  # LXI D, word
                self.registers['E'] = self.memory[self.registers['PC']]
                self.registers['D'] = self.memory[self.registers['PC'] + 1]
                self.registers['PC'] += 2

                if self.debuglevel >= 4:
                    print(f"LXI D: D={self.registers['D']:02X} E={self.registers['E']:02X}")  
            elif opcode == 0x12: # MOV M, D = 0x72 WRONG - this is STAX D
                addr = (self.registers['D'] << 8) | self.registers['E']
                self.memory[addr] = self.registers['A'] & 0xFF

                if self.debuglevel >= 4:
                    print(f"STAX D {addr:04X} : {self.registers['A']:02X}")

                self.debug_addr_write(self.debugloggerfile, addr, self.registers['A'])
            elif opcode == 0x13: # INX D
                de = (self.registers['D'] << 8) | self.registers['E']
                de = ((de + 1) & 0xFFFF) # Increment DE and ensure it wraps around at 16 bits
                self.registers['D'] = (de >> 8) & 0xFF
                self.registers['E'] = de & 0xFF

                if self.debuglevel >= 4:
                    print(f"INX D: D={self.registers['D']:02X} E={self.registers['E']:02X}")  
            elif opcode == 0x14: # INR D
                aux_carryflag_before = self.registers['D'] & 0x0F  # Save the lower nibble before increment
                self.registers['D'] = (self.registers['D'] + 1) & 0xFF  # Increment D and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag

                if self.registers['D'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['D'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['D']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if aux_carryflag_before + 1 > 0x0F:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag

                if self.debuglevel >= 4:
                    print(f"INR D: D={self.registers['D']:02X}") 
            elif opcode == 0x15:  # DCR D
                # Save the lower nibble before decrement
                aux_carryflag_before = self.registers['D'] & 0x0F
                
                # Decrement D and ensure it wraps around at 8 bits
                self.registers['D'] = (self.registers['D'] - 1) & 0xFF
                
                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                
                if self.registers['D'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['D'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['D']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (aux_carryflag_before - 1) & 0x10 != 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag

                if self.debuglevel >= 4:
                    print(f"DCR D: D={self.registers['D']:02X}") 
            elif opcode == 0x16:  # MVI D, byte
                self.registers['D'] = self.memory[self.registers['PC']]

                if self.debuglevel >= 4:
                    print(f"MVI D: addr={self.registers['PC']:04X} D={self.registers['D']:02X}")  

                self.registers['PC'] += 1
            elif opcode == 0x17:  # RAL
                carry = (self.registers['A'] & 0x80) >> 7  # Extract the most significant bit (bit 7)
                self.registers['A'] = ((self.registers['A'] << 1) & 0xFF) | (self.registers['FLAGS'] & 0x01)  # Rotate left through carry
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                # Set the carry flag based on the rotated bit
                if carry:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"RAL: A={self.registers['A']:02X}") 
            elif opcode == 0x18: # not ussed in 8080
                pass
            elif opcode == 0x19:  # DAD D
                hl = (self.registers['H'] << 8) | self.registers['L']
                de = (self.registers['D'] << 8) | self.registers['E']
                result = hl + de
                self.registers['H'] = (result >> 8) & 0xFF
                self.registers['L'] = result & 0xFF

                # Update carry flag
                self.registers['FLAGS'] &= ~(1 << 0) # Clear carry flag

                if result > 0xFFFF:
                    self.registers['FLAGS'] |= (1 << 0) # Set carry flag

                if self.debuglevel >= 4:
                    print(f"DAD D : HL={hl:04X} + DE={de:04X} = {result:04X}, CY={self.registers['FLAGS'] & 0x01}")
            elif opcode == 0x1A: # LDAX D
                addr = (self.registers['D'] << 8) | self.registers['E']
                self.registers['A'] = self.memory[addr]

                if self.debuglevel >= 4:
                    print(f"LDAX D {addr:04X} = {self.memory[addr]:02X}")
            elif opcode == 0x1B:  # DCX D
                de = (self.registers['D'] << 8) | self.registers['E']  # Combine D and E to form DE
                de = (de - 1) & 0xFFFF  # Decrement DE and ensure it wraps around at 16 bits
                self.registers['D'] = (de >> 8) & 0xFF  # Update D with the high byte of DE
                self.registers['E'] = de & 0xFF  # Update E with the low byte of DE

                if self.debuglevel >= 4:
                    print(f"DCX D: D={self.registers['D']:02X} E={self.registers['E']:02X}") 
            elif opcode == 0x1C: # INR E
                aux_carryflag_before = self.registers['E'] & 0x0F  # Save the lower nibble before increment
                self.registers['E'] = (self.registers['E'] + 1) & 0xFF  # Increment E and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag

                if self.registers['E'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['E'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['E']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if aux_carryflag_before + 1 > 0x0F:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag

                if self.debuglevel >= 4:
                    print(f"INR E: E={self.registers['E']:02X}") 
            elif opcode == 0x1D:  # DCR E
                aux_carryflag_before = self.registers['E'] & 0x0F
                self.registers['E'] = (self.registers['E'] - 1) & 0xFF

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag

                if self.registers['E'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['E'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['E']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag

                # Auxiliary carry flag calculation
                if (aux_carryflag_before - 1) & 0x10:
                    self.registers['FLAGS'] |= (1 << 4)  # Set aux carry flag

                if self.debuglevel >= 4:
                    print(f"DCR E: E={self.registers['E']:02X}") 
            elif opcode == 0x1E:  # MVI E, byte
                self.registers['E'] = self.memory[self.registers['PC']]
                self.registers['PC'] += 1
                
                if self.debuglevel >= 4:
                    print(f"MVI E, byte : E={self.registers['E']:02X}")
            elif opcode == 0x1F:  # RAR
                carry = self.registers['A'] & 0x01  # Extract the least significant bit (bit 0)
                self.registers['A'] = (self.registers['A'] >> 1) | ((self.registers['FLAGS'] & 0x01) << 7)  # Rotate right through carry
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                # Set the carry flag based on the rotated bit
                if carry:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"RAR: A={self.registers['A']:02X}") 
            elif opcode == 0x2D:  # DCR L
                aux_carryflag_before = self.registers['L'] & 0x0F  # Save the lower nibble before decrement
                self.registers['L'] = (self.registers['L'] - 1) & 0xFF  # Decrement L and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag

                if self.registers['L'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['L'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['L']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (aux_carryflag_before - 1) & 0x10 != 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag

                if self.debuglevel >= 4:
                    print(f"DCR L: L={self.registers['L']:02X}") 
            elif opcode == 0x21:  # LXI H, word
                self.registers['L'] = self.memory[self.registers['PC']]
                self.registers['H'] = self.memory[self.registers['PC'] + 1]
                self.registers['PC'] += 2

                if self.debuglevel >= 4:
                    print(f"LXI H: H={self.registers['H']:02X} L={self.registers['L']:02X}") 
            elif opcode == 0x22:  # SHLD addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                self.memory[addr] = self.registers['L']
                self.memory[addr + 1] = self.registers['H']

                if self.debuglevel >= 4:
                    print(f"SHLD addr: {addr:04X} Value={self.memory[addr + 1]:02X}{self.memory[addr]:02X}")

                self.debug_addr_write(self.debugloggerfile, addr, self.registers['L'])
                self.debug_addr_write(self.debugloggerfile, addr+1, self.registers['H'])

                self.registers['PC'] += 2
            elif opcode == 0x23: # INX H
                hl = (self.registers['H'] << 8) | self.registers['L']
                hl = (hl + 1) & 0xFFFF  # Increment HL and ensure it wraps around at 16 bits
                self.registers['H'] = (hl >> 8) & 0xFF
                self.registers['L'] = hl & 0xFF

                if self.debuglevel >= 4:
                    print(f"H: {self.registers['H']:02X} L: {self.registers['L']:02X} HL addr: {hl:04X}")
            elif opcode == 0x25: # DCR H
                aux_carryflag_before = self.registers['H'] & 0x0F  # Save the lower nibble before decrement
                self.registers['H'] = (self.registers['H'] - 1) & 0xFF  # Decrement H and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag

                if self.registers['H'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['H'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['H']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (aux_carryflag_before - 1) & 0x10 != 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag

                if self.debuglevel >= 4:
                    print(f"DCR H: H={self.registers['H']:02X}") 
            elif opcode == 0x26: # MVI H, byte
                self.registers['H'] = self.memory[self.registers['PC']]
                self.registers['PC'] += 1
                
                if self.debuglevel >= 4:
                    print(f"MVI H: H={self.registers['H']:02X}")
            elif opcode == 0x29:  # DAD H
                hl = (self.registers['H'] << 8) | self.registers['L']
                result = hl + hl
                self.registers['H'] = (result >> 8) & 0xFF
                self.registers['L'] = result & 0xFF
                # Update carry flag
                self.registers['FLAGS'] &= ~(1 << 0) # Clear carry flag

                if result > 0xFFFF:
                    self.registers['FLAGS'] |= (1 << 0) # Set carry flag

                if self.debuglevel >= 4:
                    print(f"DAD H: HL={hl:04X} + HL={hl:04X} = {result:04X} FLAGS={self.registers['FLAGS']}")             
            elif opcode == 0x2A:  # LHLD addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                self.registers['L'] = self.memory[addr]
                self.registers['H'] = self.memory[addr + 1]

                if self.debuglevel >= 4:
                    print(f"LHLD address {addr:04X}")

                self.registers['PC'] += 2
            elif opcode == 0x2B: # DCX H
                hl = (self.registers['H'] << 8) | self.registers['L']
                hl = (hl - 1) & 0xFFFF  # Decrement HL and ensure it wraps around at 16 bits
                self.registers['H'] = (hl >> 8) & 0xFF
                self.registers['L'] = hl & 0xFF

                if self.debuglevel >= 4:
                    print(f"DCX H: H={self.registers['H']:02X} L={self.registers['L']:02X}") 
            elif opcode == 0x2E:  # MVI L, byte
                self.registers['L'] = self.memory[self.registers['PC']]
                self.registers['PC'] += 1
                
                if self.debuglevel >= 4:
                    print(f"MVI L,byte: L={self.registers['L']:02X}")
            elif opcode == 0x2F: # CMA
                self.registers['A'] = ~self.registers['A'] & 0xFF
                
                if self.debuglevel >= 4:
                    print(f"CMA: A={self.registers['A']:02X}")
            elif opcode == 0x32:  # STA addr
                addr = (self.memory[self.registers["PC"]] | (self.memory[self.registers["PC"] + 1] << 8))
                self.memory[addr] = self.registers["A"]
                self.registers["PC"] += 2

                if self.debuglevel >= 4:
                    print(f"STA: {addr:04X} = {self.memory[addr]:04X}")

                self.debug_addr_write(self.debugloggerfile, addr, self.registers["A"]) 
            elif opcode == 0x33:  # INX SP
                self.registers['SP'] = (self.registers['SP'] + 1) & 0xFFFF  # Increment SP and ensure it wraps around at 16 bits
                                
                if self.debuglevel >= 4:
                    print(f"INX SP: SP={self.registers['SP']:04X}")           
            elif opcode == 0x34: # INR M
                addr = (self.registers['H'] << 8) | self.registers['L']  # Combine H and L to form the memory address
                aux_carryflag_before = self.memory[addr] & 0x0F  # Save the lower nibble before increment
                self.memory[addr] = (self.memory[addr] + 1) & 0xFF  # Increment the memory content and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag

                if self.memory[addr] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.memory[addr] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.memory[addr]).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if aux_carryflag_before + 1 > 0x0F:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag

                if self.debuglevel >= 4:
                    print(f"INR M: addr={addr:04X}") 
            elif opcode == 0x35: # DCR M
                addr = (self.registers['H'] << 8) | self.registers['L']
                aux_carryflag_before = self.memory[addr] & 0x0F
                self.memory[addr] = (self.memory[addr] - 1) & 0xFF

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag

                if self.memory[addr] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.memory[addr] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.memory[addr]).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag

                # Auxiliary carry flag calculation
                if (aux_carryflag_before - 1) & 0x10 != 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set aux carry flag    

                if self.debuglevel >= 4:
                    print(f"DCR M: addr={addr:04X}")             
            elif opcode == 0x36: # MVI M, byte
                addr = (self.registers['H'] << 8) | self.registers['L']
                self.memory[addr] = self.memory[self.registers['PC']]

                if self.debuglevel >= 4:
                    print(f"MVI M: {addr:04X} = {self.memory[self.registers['PC']]}")

                self.debug_addr_write(self.debugloggerfile, addr, self.memory[self.registers['PC']])    

                self.registers['PC'] += 1
            elif opcode == 0x37:  # STC
                self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"STC: FLAGS={self.registers['FLAGS']:02X}")
            elif opcode == 0x39: # DAD SP
                hl = (self.registers['H'] << 8) | self.registers['L']
                sp = self.registers['SP']
                result = hl + sp
                self.registers['H'] = (result >> 8) & 0xFF
                self.registers['L'] = result & 0xFF

                # Update carry flag
                self.registers['FLAGS'] &= ~(1 << 0) # Clear carry flag
                if result > 0xFFFF:
                    self.registers['FLAGS'] |= (1 << 0) # Set carry flag

                if self.debuglevel >= 4:
                    print(f"DAD SP: HL={hl:04X} + SP={sp:04X} = {result:04X} FLAGS={self.registers['FLAGS']:02X}")
            elif opcode == 0x3A:  # LDA addr
                    addr = (self.memory[self.registers["PC"]] | (self.memory[self.registers["PC"] + 1] << 8))
                    
                    if self.debuglevel >= 4:
                        print(f"LDA addr: {addr:04X}:{self.memory[addr]:02X}")

                    self.registers["A"] = self.memory[addr]
                    self.registers["PC"] += 2
            elif opcode == 0x3C: # INR A
                    aux_carryflag_before = self.registers['A'] & 0x0F  # Save the lower nibble before increment
                    self.registers['A'] = (self.registers['A'] + 1) & 0xFF  # Increment A and ensure it wraps around at 8 bits

                    # Update flags
                    self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                    self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                    self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                    self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag

                    if self.registers['A'] == 0:
                        self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                    if self.registers['A'] & 0x80:
                        self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                    if bin(self.registers['A']).count('1') % 2 == 0:
                        self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                    if aux_carryflag_before + 1 > 0x0F:
                        self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag   

                    if self.debuglevel >= 4:
                        print(f"INR A: A={self.registers['A']:02X}") 
            elif opcode == 0x3D: # DCR A
                aux_carryflag_before = self.registers['A'] & 0x0F
                self.registers['A'] = (self.registers['A'] - 1) & 0xFF

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag

                # Auxiliary carry flag calculation
                if (aux_carryflag_before - 1) & 0x10 != 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set aux carry flag  

                if self.debuglevel >= 4:
                    print(f"DCR A: A={self.registers['A']:02X}")
            elif opcode == 0x3E: # MVI A, byte
                    self.registers['A'] = self.memory[self.registers['PC']]
                    self.registers['PC'] += 1

                    if self.debuglevel >= 4:
                        print(f"MVI A,byte: A={self.registers['A']:02X}")
            elif opcode == 0x3F: # CMC
                self.registers['FLAGS'] ^= 0x01  # Toggle the carry flag

                if self.debuglevel >= 4:
                    print(f"CMC: FLAGS={self.registers['FLAGS']:02X}")
            elif opcode == 0x41:  # MOV B,C
                self.registers['B'] = self.registers['C']
                
                if self.debuglevel >= 4:
                    print(f"MOV B,C: B={self.registers['B']:02X} C={self.registers['C']:02X}")
            elif opcode == 0x43:  # MOV B,E
                self.registers["B"] = self.registers["E"] & 0xFF

                if self.debuglevel >= 4:
                    print(f"MOV B,E: B={self.registers['B']:02X} E={self.registers['E']:02X}")
            elif opcode == 0x44:  # MOV B,H
                self.registers['B'] = self.registers['H']
                
                if self.debuglevel >= 4:
                    print(f"MOV B,H: B={self.registers['B']:02X} H={self.registers['H']:02X}")
            elif opcode == 0x45:  # MOV B,L
                self.registers['B'] = self.registers['L']
                
                if self.debuglevel >= 4:
                    print(f"MOV B,L: B={self.registers['B']:02X} L={self.registers['L']:02X}")
            elif opcode == 0x46: # MOV B, M
                addr = (self.registers['H'] << 8) | self.registers['L']
                self.registers['B'] = self.memory[addr] & 0xFF

                if self.debuglevel >= 4:
                    print(f"MOV B,M: B={self.registers['B']:02X} M={addr:04X}")
            elif opcode == 0x47:  # MOV B,A
                self.registers["B"] = self.registers["A"] & 0xFF

                if self.debuglevel >= 4:
                    print(f"MOV B,A: B={self.registers['B']:02X} A={self.registers['A']:02X}")
            elif opcode == 0x48:  # MOV C,B
                self.registers["C"] = self.registers["B"] & 0xFF

                if self.debuglevel >= 4:
                    print(f"MOV C,B: C={self.registers['C']:02X} B={self.registers['B']:02X}")
            elif opcode == 0x49:  # MOV C,C
                # No operation needed as C is moved to itself  
                self.registers['C'] = self.registers['C']             
                
                if self.debuglevel >= 4:
                    print(f"MOV C,C: C={self.registers['C']:02X}")
            elif opcode == 0x4A:  # MOV C,D
                self.registers['C'] = self.registers['D']
                
                if self.debuglevel >= 4:
                    print(f"MOV C,D: C={self.registers['C']:02X} D={self.registers['D']:02X}")
            elif opcode == 0x4D:  # MOV C,L
                self.registers['C'] = self.registers['L']
                
                if self.debuglevel >= 4:
                    print(f"MOV C,L: C={self.registers['C']:02X} L={self.registers['L']:02X}")
            elif opcode == 0x4E: # MOV C, M
                addr = (self.registers['H'] << 8) | self.registers['L']
                self.registers['C'] = self.memory[addr] & 0xFF

                if self.debuglevel >= 4:
                    print(f"MOV C,M: C={self.registers['C']:02X} M={addr:04X}")
            elif opcode == 0x4F: # MOV C, A
                self.registers['C'] = self.registers['A'] & 0xFF

                if self.debuglevel >= 4:
                    print(f"MOV C,A: C={self.registers['C']:02X} A={self.registers['A']:02X}")
            elif opcode == 0x50:  # MOV D, B
                self.registers['D'] = self.registers['B']

                if self.debuglevel >= 4:
                    print(f"MOV D,B : D={self.registers['D']:02X} B={self.registers['B']:02X}")
            elif opcode == 0x51:  # MOV D,C
                self.registers['D'] = self.registers['C']
                
                if self.debuglevel >= 4:
                    print(f"MOV D,C: D={self.registers['D']:02X} C={self.registers['C']:02X}")
            elif opcode == 0x56: # MOV D, M
                addr = (self.registers['H'] << 8) | self.registers['L']
                self.registers['D'] = self.memory[addr]
                
                if self.debuglevel >= 4:
                    print(f"MOV D,M: D={self.registers['D']:02X} [HL]={addr:04X}")
            elif opcode == 0x58:  # MOV E, B
                self.registers['E'] = self.registers['B']

                if self.debuglevel >= 4:
                    print(f"MOV E,B: E={self.registers['E']:02X} B={self.registers['B']:02X}")
            elif opcode == 0x5A:  # MOV E,D
                self.registers['E'] = self.registers['D']
                
                if self.debuglevel >= 4:
                    print(f"MOV E,D: E={self.registers['E']:02X} D={self.registers['D']:02X}")
            elif opcode == 0x5E: # MOV E, M
                addr = (self.registers['H'] << 8) | self.registers['L']
                self.registers['E'] = self.memory[addr]
                
                if self.debuglevel >= 4:
                    print(f"MOV E,M: E={self.registers['E']:02X}, [HL]={addr:04X}")
            elif opcode == 0x57: # MOV D, A
                self.registers['D'] = self.registers['A']
                
                if self.debuglevel >= 4:
                    print(f"MOV D,A : D={self.registers['D']:02X} A={self.registers['A']:02X}")
            elif opcode == 0x59:  # MOV E, C
                self.registers['E'] = self.registers['C']

                if self.debuglevel >= 4:
                    print(f"MOV E,C: E={self.registers['E']:02X} C={self.registers['C']:02X}")
            elif opcode == 0x5F: # MOV E, A
                self.registers['E'] = self.registers['A']
                
                if self.debuglevel >= 4:
                    print(f"MOV E,A: E={self.registers['E']:02X} A={self.registers['A']:02X}")
            elif opcode == 0x60: # MOV H, B
                self.registers['H'] = self.registers['B']
                
                if self.debuglevel >= 4:
                    print(f"MOV H,B: H={self.registers['H']:02X} B={self.registers['B']:02X}")
            elif opcode == 0x62:  # MOV H,D
                self.registers["H"] = self.registers["D"] & 0xFF

                if self.debuglevel >= 4:
                    print(f"MOV H,D: H={self.registers['H']:02X} D={self.registers['D']:02X}")
            elif opcode == 0x67:  # MOV H,A
                self.registers["H"] = self.registers["A"] & 0xFF

                if self.debuglevel >= 4:
                    print(f"MOV H,A: H={self.registers['H']:02X} A={self.registers['A']:02X}")
            elif opcode == 0x68:  # MOV L,B
                self.registers["L"] = self.registers["B"] & 0xFF

                if self.debuglevel >= 4:
                    print(f"MOV L,B: L={self.registers['L']:02X} B={self.registers['B']:02X}")
            elif opcode == 0x69: # MOV L, C
                self.registers['L'] = self.registers['C']
                
                if self.debuglevel >= 4:
                    print(f"MOV L,C: L={self.registers['L']:02X} C={self.registers['C']:02X}")
            elif opcode == 0x6B:  # MOV L, E
                self.registers['L'] = self.registers['E']

                if self.debuglevel >= 4:
                    print(f"MOV L,E: L={self.registers['L']:02X} E={self.registers['E']:02X}")
            elif opcode == 0x6F: # MOV L, A
                self.registers['L'] = self.registers['A']
                
                if self.debuglevel >= 4:
                    print(f"MOV L,A: L={self.registers['L']:02X} A={self.registers['A']:02X}")
            elif opcode == 0x70: # MOV M, B
                addr = (self.registers['H'] << 8) | self.registers['L']
                self.memory[addr] = self.registers['B']
                
                if self.debuglevel >= 4:
                    print(f"MOV M,B : [HL]={addr:04X} B={self.registers['B']:02X}")

                self.debug_addr_write(self.debugloggerfile, addr, self.registers['B'])  
            elif opcode == 0x71: # MOV M, C
                addr = (self.registers['H'] << 8) | self.registers['L']
                self.memory[addr] = self.registers['C'] & 0xFF

                if self.debuglevel >= 4:
                     print(f"MOV M,C: M={addr:04X} C={self.registers['C']:02X}")
            elif opcode == 0x72:  # MOV M, D
                addr = (self.registers['H'] << 8) | self.registers['L']
                self.memory[addr] = self.registers['D'] & 0xFF

                if self.debuglevel >= 4:
                    print(f"MOV M,D: M={addr:04X} D={self.registers['D']:02X}")
            elif opcode == 0x73: # MOV M, E
                addr = (self.registers['H'] << 8) | self.registers['L']
                self.memory[addr] = self.registers['E']
                
                if self.debuglevel >= 4:
                    print(f"MOV M,E: [HL]={addr:04X} E={self.registers['E']:02X}")

                self.debug_addr_write(self.debugloggerfile, addr, self.registers['E'])  
            elif opcode == 0x74:  # MOV M,H
                addr = (self.registers['H'] << 8) | self.registers['L']
                self.memory[addr] = self.registers['H']
                
                if self.debuglevel >= 4:
                    print(f"MOV M,H: [HL]={addr:04X} H={self.registers['H']:02X}")

                self.debug_addr_write(self.debugloggerfile, addr, self.registers['H'])  
            elif opcode == 0x77: # MOV M, A
                addr = (self.registers['H'] << 8) | self.registers['L']
                self.memory[addr] = self.registers['A'] & 0xFF

                if self.debuglevel >= 4:
                    print(f"MOV M,A: M={addr:04X} A={self.registers['A']:02X}")

                self.debug_addr_write(self.debugloggerfile, addr, self.registers['A'])    
            elif opcode == 0x78:  # MOV A,B
                self.registers["A"] = self.registers["B"] & 0xFF

                if self.debuglevel >= 4:
                    print(f"MOV A,B: A={self.registers['A']:02X} B={self.registers['B']:02X}")
            elif opcode == 0x79: # MOV A, C
                self.registers['A'] = self.registers['C'] & 0xFF

                if self.debuglevel >= 4:
                    print(f"MOV A,C: A={self.registers['A']:02X} C={self.registers['C']:02X}")
            elif opcode == 0x7A: # MOV A, D
                self.registers['A'] = self.registers['D']
                
                if self.debuglevel >= 4:
                    print(f"MOV A,D: A={self.registers['A']:02X} D={self.registers['D']:02X}")
            elif opcode == 0x7B: # MOV A, E
                self.registers['A'] = self.registers['E']
                
                if self.debuglevel >= 4:
                    print(f"MOV A,E: A={self.registers['A']:02X} E={self.registers['E']:02X}")
            elif opcode == 0x7C:  # MOV A,H
                self.registers["A"] = self.registers["H"] & 0xFF

                if self.debuglevel >= 4:
                    print(f"MOV A,H: A={self.registers['A']:02X} H={self.registers['H']:02X}")
            elif opcode == 0x7D: # MOV A, L
                self.registers['A'] = self.registers['L']
                
                if self.debuglevel >= 4:
                    print(f"MOV A,L: A={self.registers['A']:02X} L={self.registers['L']:02X}")
            elif opcode == 0x7E: # MOV A,M
                addr = (self.registers['H'] << 8) | self.registers['L']
                self.registers['A'] = self.memory[addr] & 0xFF

                if self.debuglevel >= 4:
                    print(f"MOV A,M: A={self.registers['A']:02X} M={self.memory[addr]:02X}")
            elif opcode == 0x7F: # MOV A, A
                # No operation needed as A is moved to itself
                if self.debuglevel >= 4:
                    print(f"MOV A,A: A={self.registers['A']:02X}")
            elif opcode == 0x80:  # ADD B
                aux_carryflag_before = (self.registers['A'] & 0x0F) + (self.registers['B'] & 0x0F)  # Save the lower nibbles before addition
                result = self.registers['A'] + self.registers['B']  # Add A and B

                self.registers['A'] = result & 0xFF  # Store the result in A and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if aux_carryflag_before > 0x0F:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result > 0xFF:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag                

                if self.debuglevel >= 4:
                    print(f"ADD B: A={self.registers['A']:02X} B={self.registers['B']:02X}")
            elif opcode == 0x81:  # ADD C
                aux_carryflag_before = (self.registers['A'] & 0x0F) + (self.registers['C'] & 0x0F)  # Save the lower nibbles before addition
                result = self.registers['A'] + self.registers['C']  # Add A and C

                self.registers['A'] = result & 0xFF  # Store the result in A and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if aux_carryflag_before > 0x0F:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result > 0xFF:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"ADD C: A={self.registers['A']:02X} C={self.registers['C']:02X}")
            elif opcode == 0x83: # ADD E
                aux_carryflag_before = (self.registers['A'] & 0x0F) + (self.registers['E'] & 0x0F)  # Save the lower nibbles before addition
                result = self.registers['A'] + self.registers['E']  # Add A and E

                self.registers['A'] = result & 0xFF  # Store the result in A and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if aux_carryflag_before > 0x0F:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result > 0xFF:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"ADD E: A={self.registers['A']:02X} E={self.registers['E']:02X}")   
            elif opcode == 0x86: # ADD M
                addr = (self.registers['H'] << 8) | self.registers['L']  # Combine H and L to form the memory address
                value = self.memory[addr]  # Fetch the value from memory
                aux_carryflag_before = (self.registers['A'] & 0x0F) + (value & 0x0F)  # Save the lower nibbles before addition
                result = self.registers['A'] + value  # Add A and the memory value

                self.registers['A'] = result & 0xFF  # Store the result in A and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if aux_carryflag_before > 0x0F:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result > 0xFF:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"ADD M: A={self.registers['A']:02X} [HL]={value:02X}")
            elif opcode == 0x87: # ADD A
                aux_carryflag_before = (self.registers['A'] & 0x0F) + (self.registers['A'] & 0x0F)  # Save the lower nibbles before addition
                result = self.registers['A'] + self.registers['A']  # Add A to itself

                self.registers['A'] = result & 0xFF  # Store the result in A and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if aux_carryflag_before > 0x0F:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result > 0xFF:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag                

                if self.debuglevel >= 4:
                    print(f"ADD A: A={self.registers['A']:02X}")    
            elif opcode == 0x89:  # ADC C
                carry = self.registers['FLAGS'] & 0x01  # Get the current carry flag
                aux_carryflag_before = (self.registers['A'] & 0x0F) + (self.registers['C'] & 0x0F) + carry  # Save the lower nibbles before addition
                result = self.registers['A'] + self.registers['C'] + carry  # Add A, C, and the carry flag

                self.registers['A'] = result & 0xFF  # Store the result in A and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if aux_carryflag_before > 0x0F:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result > 0xFF:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"ADC C: A={self.registers['A']:02X} C={self.registers['C']:02X}")
            elif opcode == 0x8A:  # ADC D
                carry = self.registers['FLAGS'] & 0x01  # Get the current carry flag
                aux_carryflag_before = (self.registers['A'] & 0x0F) + (self.registers['D'] & 0x0F) + carry  # Save the lower nibbles before addition
                result = self.registers['A'] + self.registers['D'] + carry  # Add A, D, and the carry flag

                self.registers['A'] = result & 0xFF  # Store the result in A and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if aux_carryflag_before > 0x0F:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result > 0xFF:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag                

                if self.debuglevel >= 4:
                    print(f"ADC D: A={self.registers['A']:02X} D={self.registers['D']:02X}")     
            elif opcode == 0x8F: # ADC A
                carry = self.registers['FLAGS'] & 0x01  # Get the current carry flag
                aux_carryflag_before = (self.registers['A'] & 0x0F) + (self.registers['A'] & 0x0F) + carry  # Save the lower nibbles before addition
                result = self.registers['A'] + self.registers['A'] + carry  # Add A to itself and the carry flag

                self.registers['A'] = result & 0xFF  # Store the result in A and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if aux_carryflag_before > 0x0F:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result > 0xFF:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"ADC A: A={self.registers['A']:02X}")
            elif opcode == 0x90: # SUB B
                aux_carryflag_before = self.registers['A'] & 0x0F  # Save the lower nibble before subtraction
                result = self.registers['A'] - self.registers['B']  # Subtract B from A

                self.registers['A'] = result & 0xFF  # Store the result in A and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (aux_carryflag_before - (self.registers['B'] & 0x0F)) < 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result < 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"SUB B: A={self.registers['A']:02X} B={self.registers['B']:02X}")
            elif opcode == 0x92: # SUB D
                aux_carryflag_before = self.registers['A'] & 0x0F  # Save the lower nibble before subtraction
                result = self.registers['A'] - self.registers['D']  # Subtract D from A

                self.registers['A'] = result & 0xFF  # Store the result in A and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (aux_carryflag_before - (self.registers['D'] & 0x0F)) < 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result < 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"SUB D: A={self.registers['A']:02X} D={self.registers['D']:02X}")
            elif opcode == 0x93: # SUB E
                aux_carryflag_before = self.registers['A'] & 0x0F  # Save the lower nibble before subtraction
                result = self.registers['A'] - self.registers['E']  # Subtract E from A

                self.registers['A'] = result & 0xFF  # Store the result in A and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (aux_carryflag_before - (self.registers['E'] & 0x0F)) < 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result < 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"SUB E: A={self.registers['A']:02X} E={self.registers['E']:02X}")
            elif opcode == 0x95: # SUB L
                aux_carryflag_before = self.registers['A'] & 0x0F  # Save the lower nibble before subtraction
                result = self.registers['A'] - self.registers['L']  # Subtract L from A

                self.registers['A'] = result & 0xFF  # Store the result in A and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (aux_carryflag_before - (self.registers['L'] & 0x0F)) < 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result < 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"SUB L: A={self.registers['A']:02X} L={self.registers['L']:02X}")
            elif opcode == 0x96: # SUB M
                addr = (self.registers['H'] << 8) | self.registers['L']  # Combine H and L to form the memory address
                value = self.memory[addr]  # Fetch the value from memory
                aux_carryflag_before = self.registers['A'] & 0x0F  # Save the lower nibble before subtraction
                result = self.registers['A'] - value  # Subtract the memory value from A

                self.registers['A'] = result & 0xFF  # Store the result in A and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (aux_carryflag_before - (value & 0x0F)) < 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result < 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"SUB M: A={self.registers['A']:02X} M={value:02X}")
            elif opcode == 0x98:  # SBB B
                carry = self.registers['FLAGS'] & 0x01  # Get the current carry flag
                aux_carryflag_before = self.registers['A'] & 0x0F  # Save the lower nibble before subtraction
                result = self.registers['A'] - self.registers['B'] - carry  # Subtract B and the carry flag from A

                self.registers['A'] = result & 0xFF  # Store the result in A and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (aux_carryflag_before - (self.registers['B'] & 0x0F) - carry) < 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result < 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag                

                if self.debuglevel >= 3:
                    print(f"SBB B: A={self.registers['A']:02X} B={self.registers['B']:02X}")
            elif opcode == 0xA0:  # ANA B
                aux_carryflag_before = self.registers['A'] & 0x08  
                self.registers['A'] &= self.registers['B']  # Perform bitwise AND between A and B
               
                # Clear flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                # Set flags based on the result in the A register
                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                # Auxiliary carry flag calculation
                if (aux_carryflag_before & 0x08) != (self.registers['A'] & 0x08):
                    self.registers['FLAGS'] |= (1 << 4)  # Set aux carry flag

                if self.debuglevel >= 4:
                    print(f"ANA B: A={self.registers['A']:02X} B={self.registers['B']:02X}")
            elif opcode == 0xA2:  # ANA D
                self.registers['A'] &= self.registers['D']

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (self.registers['A'] & 0x08) != (self.registers['D'] & 0x08):
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag

                if self.debuglevel >= 4:
                    print(f"ANA D: A={self.registers['A']:02X} D={self.registers['D']:02X}")
            elif opcode == 0xA3:  # ANA E
                self.registers['A'] &= self.registers['E']  # Perform bitwise AND between A and E

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (self.registers['A'] & 0x08) != (self.registers['E'] & 0x08):
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag

                if self.debuglevel >= 4:
                    print(f"ANA E: A={self.registers['A']:02X} E={self.registers['E']:02X}")
            elif opcode == 0xA5:  # ANA L
                self.registers['A'] &= self.registers['L']  # Perform bitwise AND between A and L

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (self.registers['A'] & 0x08) != (self.registers['L'] & 0x08):
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag

                if self.debuglevel >= 4:
                    print(f"ANA L: A={self.registers['A']:02X} L={self.registers['L']:02X}")
            elif opcode == 0xA8: # XRA B
                self.registers['A'] ^= self.registers['B']  # Perform bitwise XOR between A and B

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag

                if self.debuglevel >= 4:
                    print(f"XRA B: A={self.registers['A']:02X} B={self.registers['B']:02X}")
            elif opcode == 0xA9: # XRA C
                self.registers['A'] ^= self.registers['C']  # Perform bitwise XOR between A and C

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag

                if self.debuglevel >= 4:
                    print(f"XRA C: A={self.registers['A']:02X} C={self.registers['C']:02X}")
            elif opcode == 0xAE: # XRA M
                addr = (self.registers['H'] << 8) | self.registers['L']  # Combine H and L to form the memory address
                value = self.memory[addr]  # Fetch the value from memory
                self.registers['A'] ^= value  # Perform bitwise XOR between A and the memory value

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag

                if self.debuglevel >= 4:
                    print(f"XRA M: A={self.registers['A']:02X} M={value:02X}")
            elif opcode == 0xAF: # XRA A
                self.registers['A'] ^= self.registers['A']  # Perform bitwise XOR between A and itself

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag

                if self.debuglevel >= 4:
                    print(f"XRA A: A={self.registers['A']:02X}")
            elif opcode == 0xB0:  # ORA B
                self.registers['A'] |= self.registers['B']  # Perform bitwise OR between A and B

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag

                if self.debuglevel >= 4:
                    print(f"ORA B: A={self.registers['A']:02X} B={self.registers['B']:02X}")
            elif opcode == 0xB1:  # ORA C
                self.registers['A'] |= self.registers['C']  # Perform bitwise OR between A and C

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag

                if self.debuglevel >= 4:
                    print(f"ORA C: A={self.registers['A']:02X} C={self.registers['C']:02X}")
            elif opcode == 0xB2:  # ORA D
                self.registers['A'] |= self.registers['D']  # Perform bitwise OR between A and D

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag

                if self.debuglevel >= 4:
                    print(f"ORA D: A={self.registers['A']:02X} D={self.registers['D']:02X}")
            elif opcode == 0xB3:  # ORA E
                self.registers['A'] |= self.registers['E']  # Perform bitwise OR between A and E

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag

                if self.debuglevel >= 4:
                    print(f"ORA E: A={self.registers['A']:02X} E={self.registers['E']:02X}")
            elif opcode == 0xB4:  # ORA H
                self.registers['A'] |= self.registers['H']  # Perform bitwise OR between A and H

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag

                if self.debuglevel >= 4:
                    print(f"ORA H: A={self.registers['A']:02X} H={self.registers['H']:02X}")
            elif opcode == 0xB6:  # ORA M
                addr = (self.registers['H'] << 8) | self.registers['L']  # Combine H and L to form the memory address
                value = self.memory[addr]  # Fetch the value from memory
                self.registers['A'] |= value  # Perform bitwise OR between A and the memory value

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag

                if self.debuglevel >= 4:
                    print(f"ORA M: A={self.registers['A']:02X} M={value:02X}") 
            elif opcode == 0xB7:  # ORA A
                self.registers['A'] |= self.registers['A']  # Perform bitwise OR between A and itself

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag

                if self.debuglevel >= 4:
                    print(f"ORA A: A={self.registers['A']:02X}") 
            elif opcode == 0xB8:  # CMP B
                aux_carryflag_before = self.registers['A'] & 0x0F  # Save the lower nibble before comparison
                result = self.registers['A'] - self.registers['B']  # Compare A with B (A - B)

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if result == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if result & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(result & 0xFF).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (aux_carryflag_before - (self.registers['B'] & 0x0F)) < 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result < 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"CMP B: A={self.registers['A']:02X} B={self.registers['B']:02X} FLAGS={self.registers['FLAGS']:02X}") 
            elif opcode == 0xB9:  # CMP C
                aux_carryflag_before = self.registers['A'] & 0x0F  # Save the lower nibble before comparison
                result = self.registers['A'] - self.registers['C']  # Compare A with C (A - C)

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if result == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if result & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(result & 0xFF).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (aux_carryflag_before - (self.registers['C'] & 0x0F)) < 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result < 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag   

                if self.debuglevel >= 4:
                    print(f"CMP C: A={self.registers['A']:02X} C={self.registers['C']:02X} FLAGS={self.registers['FLAGS']:02X}")       
            elif opcode == 0xBA:  # CMP D
                aux_carryflag_before = self.registers['A'] & 0x0F  # Save the lower nibble before comparison
                result = self.registers['A'] - self.registers['D']  # Compare A with D (A - D)

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if result == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if result & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(result & 0xFF).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (aux_carryflag_before - (self.registers['D'] & 0x0F)) < 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result < 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"CMP D: A={self.registers['A']:02X} D={self.registers['D']:02X} FLAGS={self.registers['FLAGS']:02X}") 
            elif opcode == 0xBE:  # CMP M
                addr = (self.registers['H'] << 8) | self.registers['L']  # Combine H and L to form the memory address
                value = self.memory[addr]  # Fetch the value from memory
                aux_carryflag_before = self.registers['A'] & 0x0F  # Save the lower nibble before comparison
                result = self.registers['A'] - value  # Compare A with the memory value (A - M)

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if result == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if result & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(result & 0xFF).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (aux_carryflag_before - (value & 0x0F)) < 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result < 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"CMP M: A={self.registers['A']:02X} value={value:02X} FLAGS={self.registers['FLAGS']:02X}") 
            elif opcode == 0xBF: # CMP A
                aux_carryflag_before = self.registers['A'] & 0x0F  # Save the lower nibble before comparison
                result = self.registers['A'] - self.registers['A']  # Compare A with itself (A - A)

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if result == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if result & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(result & 0xFF).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (aux_carryflag_before - (self.registers['A'] & 0x0F)) < 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result < 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"CMP A: A={self.registers['A']:02X} FLAGS={self.registers['FLAGS']:02X}") 
            elif opcode == 0x99: # SBB C
                carry = self.registers['FLAGS'] & 0x01  # Get the current carry flag
                aux_carryflag_before = self.registers['A'] & 0x0F  # Save the lower nibble before subtraction
                result = self.registers['A'] - self.registers['C'] - carry  # Subtract C and the carry flag from A

                self.registers['A'] = result & 0xFF  # Store the result in A and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (aux_carryflag_before - (self.registers['C'] & 0x0F) - carry) < 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result < 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"SBB C: A={self.registers['A']:02X} C={self.registers['C']:02X}") 
            elif opcode == 0x9A: # SBB D
                carry = self.registers['FLAGS'] & 0x01  # Get the current carry flag
                aux_carryflag_before = self.registers['A'] & 0x0F  # Save the lower nibble before subtraction
                result = self.registers['A'] - self.registers['D'] - carry  # Subtract D and the carry flag from A

                self.registers['A'] = result & 0xFF  # Store the result in A and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (aux_carryflag_before - (self.registers['D'] & 0x0F) - carry) < 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result < 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"SBB D: A={self.registers['A']:02X} D={self.registers['D']:02X}") 
            elif opcode == 0x9B: # SBB E
                carry = self.registers['FLAGS'] & 0x01  # Get the current carry flag
                aux_carryflag_before = self.registers['A'] & 0x0F  # Save the lower nibble before subtraction
                result = self.registers['A'] - self.registers['E'] - carry  # Subtract E and the carry flag from A

                self.registers['A'] = result & 0xFF  # Store the result in A and ensure it wraps around at 8 bits

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if (aux_carryflag_before - (self.registers['E'] & 0x0F) - carry) < 0:
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag
                if result < 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag

                if self.debuglevel >= 4:
                    print(f"SBB E: A={self.registers['A']:02X} E={self.registers['E']:02X}") 
            elif opcode == 0x9C: # SBB H
                carry = self.registers['FLAGS'] & 0x01
                aux_carryflag_before = self.registers['A'] & 0x10 
                result = self.registers['A'] - self.registers['H'] - carry
                aux_carryflag_after = result & 0x08 

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if result < 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag
                    result += 256

                if result == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if result & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(result).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if aux_carryflag_before and aux_carryflag_after:
                    self.registers['FLAGS'] |= (1 << 4)  # Set aux carry flag 

                self.registers['A'] = result

                if self.debuglevel >= 4:
                    print(f"SBB H: A={self.registers['A']:02X} H={self.registers['H']:02X}") 
            elif opcode == 0x9E: # SBB M
                carry = self.registers['FLAGS'] & 0x01
                addr = (self.registers['H'] << 8) | self.registers['L']
                aux_carryflag_before = self.registers['A'] & 0x10 
                result = self.registers['A'] - self.memory[addr] - carry
                aux_carryflag_after = result & 0x08 

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if result < 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag
                    result += 256

                if result == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if result & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(result).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if aux_carryflag_before and aux_carryflag_after:
                    self.registers['FLAGS'] |= (1 << 4)  # Set aux carry flag 

                self.registers['A'] = result

                if self.debuglevel >= 4:
                    print(f"SBB M: A={self.registers['A']:02X} M={self.memory[addr]:02X}") 
            elif opcode == 0x9F: # SBB A
                carry = self.registers['FLAGS'] & 0x01
                aux_carryflag_before = self.registers['A'] & 0x10
                result = self.registers['A'] - self.registers['A'] - carry
                aux_carryflag_after = result & 0x08 

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if result < 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag
                    result += 256

                if result == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if result & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(result).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if aux_carryflag_before and aux_carryflag_after:
                    self.registers['FLAGS'] |= (1 << 4)  # Set aux carry flag 

                self.registers['A'] = result

                if self.debuglevel >= 4:
                    print(f"SBB A: A={self.registers['A']:02X}") 
            elif opcode == 0xE4:  # CPO addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                if not (self.registers['FLAGS'] & (1 << 2)):  # Check if the parity flag is not set
                    self.registers['PC'] += 2
                    self.memory[self.registers['SP'] - 1] = (self.registers['PC'] >> 8) & 0xFF  # Push high byte of PC
                    self.memory[self.registers['SP'] - 2] = self.registers['PC'] & 0xFF  # Push low byte of PC
                    self.registers['SP'] -= 2
                    self.registers['PC'] = addr

                    if self.debuglevel >= 4:
                        print(f"CPO addr: {addr:04X}")                     
                else:
                    self.registers['PC'] += 2
            elif opcode == 0xC0:  # RNZ
                if not (self.registers['FLAGS'] & (1 << 6)):  # Check if the zero flag is not set
                    self.registers['PC'] = self.memory[self.registers['SP']] | (self.memory[self.registers['SP'] + 1] << 8)
                    self.registers['SP'] += 2

                    if self.debuglevel >= 4:
                        print(f"RNZ: {self.registers['PC']:04X}")    

            elif opcode == 0xC1:  # POP B
                self.registers['C'] = self.memory[self.registers['SP']]
                self.registers['B'] = self.memory[self.registers['SP'] + 1]
                self.registers['SP'] += 2

                if self.debuglevel >= 4:
                    print(f"POP B: B={self.registers['B']:02X}, C={self.registers['C']:02X}")
            elif opcode == 0xC2: # JNZ addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                if not (self.registers['FLAGS'] & (1 << 6)):  # Check if the zero flag is not set
                    self.registers['PC'] = addr

                    if self.debuglevel >= 4:
                        print(f"JNZ: addr={addr:04X}")    
                else:
                    self.registers['PC'] += 2
            elif opcode == 0xC3:  # JMP addr
                addr = (self.memory[self.registers["PC"]] | (self.memory[self.registers["PC"] + 1] << 8))
                self.registers["PC"] = addr
                if self.debuglevel >= 4:
                    print(f"JMP to: {addr:04X}")
            elif opcode == 0xC4:  # CNZ addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                if not (self.registers['FLAGS'] & (1 << 6)):  # Check if the zero flag is not set
                    self.registers['PC'] += 2
                    self.memory[self.registers['SP'] - 1] = (self.registers['PC'] >> 8) & 0xFF  # Push high byte of PC
                    self.memory[self.registers['SP'] - 2] = self.registers['PC'] & 0xFF  # Push low byte of PC
                    self.registers['SP'] -= 2
                    self.registers['PC'] = addr

                    if self.debuglevel >= 4:
                        print(f"CNZ addr: addr={addr:04X}")    
                else:
                    self.registers['PC'] += 2
            elif opcode == 0xC5: # PUSH B
                self.memory[self.registers['SP'] - 1] = self.registers['B']
                self.memory[self.registers['SP'] - 2] = self.registers['C']
                self.registers['SP'] -= 2
                
                if self.debuglevel >= 4:
                    print(f"PUSH B: B={self.registers['B']:02X}, C={self.registers['C']:02X}")
            elif opcode == 0xC6: # ADI byte
                immediate_value = self.memory[self.registers['PC']] & 0xFF
                self.registers['PC'] += 1

                aux_carryflag_before = self.registers['A'] & 0x08 
                carryflag_before = self.registers['A'] & 0x80
                if self.registers['A'] + immediate_value > 0xFF:   
                    self.registers['A'] = immediate_value - 1          
                else:
                    self.registers['A'] += immediate_value
                aux_carryflag_after = self.registers['A'] & 0x10
                carryflag_after = self.registers['A'] & 0x80

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if aux_carryflag_before and aux_carryflag_after:
                    self.registers['FLAGS'] |= (1 << 4)  # Set aux carry flag   
                if carryflag_before and carryflag_after == 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set aux carry flag    

                if self.debuglevel >= 4:
                    print(f"ADI byte: A={self.registers['A']:02X} immediate={immediate_value:02X}")            
            elif opcode == 0xC7: # RST 0
                self.memory[self.registers['SP'] - 1] = (self.registers['PC'] >> 8) & 0xFF # Push high byte of PC
                self.memory[self.registers['SP'] - 2] = self.registers['PC'] & 0xFF # Push low byte of PC
                self.registers['SP'] -= 2
                self.registers['PC'] = 0x00

                if self.debuglevel >= 4:
                    print(f"RST 0 call: {self.registers['PC']:04X}")
            elif opcode == 0xC8: # RZ
                if self.registers['FLAGS'] & (1 << 6):  # Check if the zero flag is set
                    self.registers['PC'] = self.memory[self.registers['SP']] | (self.memory[self.registers['SP'] + 1] << 8)
                    self.registers['SP'] += 2

                    if self.debuglevel >= 4:
                        print(f"RZ: {self.registers['PC']:04X}")
            elif opcode == 0xC9: # RET
                self.registers['PC'] = self.memory[self.registers['SP']] | (self.memory[self.registers['SP'] + 1] << 8)

                # error in binary, jump to 0x04F7 does not align to the opcode LXI B
                if self.registers['PC'] == 0x04F7:
                       self.registers['PC'] = 0x04F5
                
                if self.debuglevel >= 4:
                        print(f"RET: {self.registers['PC']:04X}")
                
                self.registers['SP'] += 2
            elif opcode == 0xCA: # JZ addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                if self.registers['FLAGS'] & (1 << 6):  # Check if the zero flag is set
                    # error in binary, jump to 0x04F7 does not align to the opcode LXI B
                    if addr == 0x04F7:
                        addr = 0x04F5

                    self.registers['PC'] = addr

                    if self.debuglevel >= 4:
                        print(f"JZ to: {addr:04X}")
                else:
                    self.registers['PC'] += 2
            elif opcode == 0xCC: # CZ addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                if self.registers['FLAGS'] & (1 << 6):  # Check if the zero flag is set
                    self.registers['PC'] += 2
                    self.memory[self.registers['SP'] - 1] = (self.registers['PC'] >> 8) & 0xFF  # Push high byte of PC
                    self.memory[self.registers['SP'] - 2] = self.registers['PC'] & 0xFF         # Push low byte of PC
                    self.registers['SP'] -= 2
                    self.registers['PC'] = addr

                    if self.debuglevel >= 4:
                        print(f"CZ to: {addr:04X}")
                else:
                    self.registers['PC'] += 2
            elif opcode == 0xCD: # CALL addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                self.registers['PC'] += 2
                self.memory[self.registers['SP'] - 1] = (self.registers['PC'] >> 8) & 0xFF  # Push high byte of PC
                self.memory[self.registers['SP'] - 2] = self.registers['PC'] & 0xFF         # Push low byte of PC

                if self.debuglevel >= 4:
                    print(f"Call: {addr:04X}")

                self.registers['SP'] -= 2
                self.registers['PC'] = addr
            elif opcode == 0xCE: # ACI byte
                immediate_value = self.memory[self.registers['PC']]
                self.registers['PC'] += 1
                carry = self.registers['FLAGS'] & 0x01
                aux_carryflag_before = self.registers['A'] & 0x08 
                result = self.registers['A'] + immediate_value + carry
                aux_carryflag_after = result & 0x10 

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if result > 255:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag
                    result -= 256

                if result == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if result & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(result).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if aux_carryflag_before and aux_carryflag_after:
                    self.registers['FLAGS'] |= (1 << 4)  # Set aux carry flag

                self.registers['A'] = result

                if self.debuglevel >= 4:
                    print(f"ACI byte: A={self.registers['A']:02X} byte={immediate_value:02X}")
            elif opcode == 0xCF: # RST 1
                self.memory[self.registers['SP'] - 1] = (self.registers['PC'] >> 8) & 0xFF # Push high byte of PC
                self.memory[self.registers['SP'] - 2] = self.registers['PC'] & 0xFF # Push low byte of PC
                self.registers['SP'] -= 2
                self.registers['PC'] = 0x08

                if self.debuglevel >= 4:
                    print(f"RST 1 call: {self.registers['PC']:04X}")
            elif opcode == 0xD0: # RNC
                if not (self.registers['FLAGS'] & 0x01):  # Check if the carry flag is not set
                    self.registers['PC'] = self.memory[self.registers['SP']] | (self.memory[self.registers['SP'] + 1] << 8)
                    self.registers['SP'] += 2

                    if self.debuglevel >= 4:
                        print(f"RNC to: {self.registers['PC']:04X}")
            elif opcode == 0xD1:  # POP D
                self.registers['E'] = self.memory[self.registers['SP']]
                self.registers['D'] = self.memory[self.registers['SP'] + 1]
                self.registers['SP'] += 2

                if self.debuglevel >= 4:
                    print("POP D")
            elif opcode == 0xD2: # JNC addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                if not (self.registers['FLAGS'] & 0x01):  # Check if the carry flag is not set
                    self.registers['PC'] = addr

                    if self.debuglevel >= 4:
                        print(f"JNC to: {addr:04X}")
                else:
                    self.registers['PC'] += 2
            elif opcode == 0xD4:  # CNC addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                if not (self.registers['FLAGS'] & 0x01):  # Check if the carry flag is not set
                    self.registers['PC'] += 2
                    self.memory[self.registers['SP'] - 1] = (self.registers['PC'] >> 8) & 0xFF  # Push high byte of PC
                    self.memory[self.registers['SP'] - 2] = self.registers['PC'] & 0xFF  # Push low byte of PC
                    self.registers['SP'] -= 2
                    self.registers['PC'] = addr

                    if self.debuglevel >= 4:
                        print(f"CNC to: {addr:04X}")
                else:
                    self.registers['PC'] += 2
            elif opcode == 0xD7: # RST 2
                self.memory[self.registers['SP'] - 1] = (self.registers['PC'] >> 8) & 0xFF  # Push high byte of PC
                self.memory[self.registers['SP'] - 2] = self.registers['PC'] & 0xFF         # Push low byte of PC
                self.registers['SP'] -= 2
                self.registers['PC'] = 0x10

                if self.debuglevel >= 4:
                    print(f"RST 2 call: {self.registers['PC']:04X}")
            elif opcode == 0xD8: # RC
                if self.registers['FLAGS'] & 0x01:  # Check if the carry flag is set
                    self.registers['PC'] = self.memory[self.registers['SP']] | (self.memory[self.registers['SP'] + 1] << 8)
                    self.registers['SP'] += 2

                    if self.debuglevel >= 4:
                        print(f"RC call: {self.registers['PC']:04X}")
            elif opcode == 0xDA: # JC addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                if self.registers['FLAGS'] & 0x01:  # Check if the carry flag is set
                        self.registers['PC'] = addr

                        if self.debuglevel >= 4:
                            print(f"JC to: {addr:04X}")
                else:
                    self.registers['PC'] += 2
            elif opcode == 0xDB:  # IN port
                port = self.memory[self.registers["PC"]] & 0xFF
                self.registers["PC"] += 1
                inledcnt = (inledcnt + 1) % 5
                if inledcnt == 4:
                    self.leds[INP_LED].turn_on()
                self.registers["A"] = self.input_port(pc, port) & 0xFF
                if inledcnt == 4:
                    self.leds[INP_LED].turn_off()

                if self.debuglevel >= 4:
                    print(f"IN: Port={port:02X} Data={self.registers["A"]:02X}")
            elif opcode == 0xD3:  # OUT port
                port = self.memory[self.registers["PC"]] & 0xFF
                self.registers["PC"] += 1
                self.leds[OUT_LED].turn_on()
                self.output_port(self.registers["A"], port)
                self.leds[OUT_LED].turn_off()

                if self.debuglevel >= 4:
                    print(f"OUT: Port={port:02X} Data={self.registers["A"]:02X}")                
            elif opcode == 0xD5: # PUSH D
                self.memory[self.registers['SP'] - 1] = self.registers['D']
                self.memory[self.registers['SP'] - 2] = self.registers['E']
                self.registers['SP'] -= 2

                if self.debuglevel >= 4:
                    print("PUSH D")
            elif opcode == 0xD6:  # SUI byte
                immediate_value = self.memory[self.registers['PC']]
                self.registers['PC'] += 1
                result = self.registers['A'] - immediate_value

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if result < 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag
                    result += 256

                if result == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if result & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(result & 0xFF).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag

                # Auxiliary carry flag calculation
                if (self.registers['A'] & 0x0F) < (immediate_value & 0x0F):
                    self.registers['FLAGS'] |= (1 << 4)  # Set aux carry flag

                self.registers['A'] = result & 0xFF   

                if self.debuglevel >= 4:
                    print(f"SUI data: {self.registers['A']:02X}")
            elif opcode == 0xDC: # CC addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                if self.registers['FLAGS'] & 0x01: # Check if the carry flag is set
                    self.registers['PC'] += 2
                    self.memory[self.registers['SP'] - 1] = (self.registers['PC'] >> 8) & 0xFF # Push high byte of PC
                    self.memory[self.registers['SP'] - 2] = self.registers['PC'] & 0xFF # Push low byte of PC
                    self.registers['SP'] -= 2
                    self.registers['PC'] = addr

                    if self.debuglevel >= 4:
                        print(f"CC to: {addr:04X}")
                else:
                    self.registers['PC'] += 2             
            elif opcode == 0xDE: # SBI byte
                immediate_value = self.memory[self.registers['PC']]
                self.registers['PC'] += 1
                carry = self.registers['FLAGS'] & 0x01
                aux_carryflag_before = self.registers['A'] & 0x10 
                result = self.registers['A'] - immediate_value - carry
                aux_carryflag_after = result & 0x08 

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if result < 0:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag
                    result += 256

                if result == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if result & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(result).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if aux_carryflag_before and aux_carryflag_after:
                    self.registers['FLAGS'] |= (1 << 4)  # Set aux carry flag 

                self.registers['A'] = result

                if self.debuglevel >= 4:
                    print(f"SBI A: A={self.registers['A']:02X}")
            elif opcode == 0xDF: # RST 3
                self.memory[self.registers['SP'] - 1] = (self.registers['PC'] >> 8) & 0xFF  # Push high byte of PC
                self.memory[self.registers['SP'] - 2] = self.registers['PC'] & 0xFF         # Push low byte of PC
                self.registers['SP'] -= 2
                self.registers['PC'] = 0x18

                if self.debuglevel >= 4:
                    print(f"RST 3 call: {self.registers['PC']:04X}")
            elif opcode == 0xE0:  # RPO
                if not (self.registers['FLAGS'] & (1 << 2)):  # Check if the parity flag is not set
                    self.registers['PC'] = self.memory[self.registers['SP']] | (self.memory[self.registers['SP'] + 1] << 8)
                    self.registers['SP'] += 2

                    if self.debuglevel >= 4:
                        print(f"RPO PC: {self.registers['PC']:04X}")
            elif opcode == 0xE1: # POP H
                self.registers['L'] = self.memory[self.registers['SP']]
                self.registers['H'] = self.memory[self.registers['SP'] + 1]
                self.registers['SP'] += 2

                if self.debuglevel >= 4:
                    print("POP H")
            elif opcode == 0xE2:  # JPO addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                if not (self.registers['FLAGS'] & (1 << 2)):  # Check if the parity flag is not set
                    self.registers['PC'] = addr

                    if self.debuglevel >= 4:
                        print(f"JPO jump: {addr:04X}")
                else:
                    self.registers['PC'] += 2
            elif opcode == 0xE3: # XTHL
                temp_l = self.memory[self.registers['SP']]
                temp_h = self.memory[self.registers['SP'] + 1]
                self.memory[self.registers['SP']] = self.registers['L']
                self.memory[self.registers['SP'] + 1] = self.registers['H']
                self.registers['L'] = temp_l
                self.registers['H'] = temp_h

                if self.debuglevel >= 4:
                    print("XTHL")
            elif opcode == 0xE4:  # CPO addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                if not (self.registers['FLAGS'] & (1 << 2)):  # Check if the parity flag is not set
                    self.registers['PC'] += 2
                    self.memory[self.registers['SP'] - 1] = (self.registers['PC'] >> 8) & 0xFF  # Push high byte of PC
                    self.memory[self.registers['SP'] - 2] = self.registers['PC'] & 0xFF  # Push low byte of PC
                    self.registers['SP'] -= 2
                    self.registers['PC'] = addr

                    if self.debuglevel >= 4:
                        print(f"CPO addr: {addr:04X}")
                else:
                    self.registers['PC'] += 2
            elif opcode == 0xE5: # PUSH H
                self.memory[self.registers['SP'] - 1] = self.registers['H']
                self.memory[self.registers['SP'] - 2] = self.registers['L']
                self.registers['SP'] -= 2

                if self.debuglevel >= 4:
                    print(f"PUSH HL: {self.registers['H']:02X}-{self.registers['L']:02X}")
            elif opcode == 0xEA:  # JPE addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                if self.registers['FLAGS'] & (1 << 2):  # Check if the parity flag is set
                    self.registers['PC'] = addr

                    if self.debuglevel >= 4:
                        print(f"JPE jump: {addr:04X}")
                else:
                    self.registers['PC'] += 2
            elif opcode == 0xE7: # RST 4
                self.memory[self.registers['SP'] - 1] = (self.registers['PC'] >> 8) & 0xFF # Push high byte of PC
                self.memory[self.registers['SP'] - 2] = self.registers['PC'] & 0xFF # Push low byte of PC
                self.registers['SP'] -= 2
                self.registers['PC'] = 0x20

                if self.debuglevel >= 4:
                    print(f"RST 4 call: {self.registers['PC']:04X}")
            elif opcode == 0xEB: # XCHG
                tempreg = self.registers['D']
                self.registers['D'] = self.registers['H']
                self.registers['H'] = tempreg

                tempreg = self.registers['E']
                self.registers['E'] = self.registers['L']
                self.registers['L'] = tempreg       

                if self.debuglevel >= 4:
                    print("XCHG")         
            elif opcode == 0xE6: # ANI byte
                immediate_value = self.memory[self.registers['PC']]
                self.registers['PC'] += 1
                self.registers['A'] &= immediate_value                

                # Clear flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                # Set flags based on the result in the A register
                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag

                if self.debuglevel >= 4:
                    print(f"ANI A & {immediate_value:02X} = {self.registers['A']:02X}")
            elif opcode == 0xE8:  # RPE
                if self.registers['FLAGS'] & (1 << 2):  # Check if the parity flag is set
                    self.registers['PC'] = self.memory[self.registers['SP']] | (self.memory[self.registers['SP'] + 1] << 8)
                    self.registers['SP'] += 2

                    if self.debuglevel >= 4:
                        print(f"RPE PC: {self.registers['PC']:04X}")
            elif opcode == 0xE9: # PCHL
                self.registers['PC'] = (self.registers['H'] << 8) | self.registers['L']
                
                if self.debuglevel >= 4:
                    print(f"PCHL : PC={self.registers['PC']:04X}")
            elif opcode == 0xEC:  # CPE addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                if self.registers['FLAGS'] & (1 << 2):  # Check if the parity flag is set
                    self.registers['PC'] += 2
                    self.memory[self.registers['SP'] - 1] = (self.registers['PC'] >> 8) & 0xFF  # Push high byte of PC
                    self.memory[self.registers['SP'] - 2] = self.registers['PC'] & 0xFF  # Push low byte of PC
                    self.registers['SP'] -= 2
                    self.registers['PC'] = addr
                else:
                    self.registers['PC'] += 2
                
                if self.debuglevel >= 4:
                    print(f"CPE addr: {addr:04X}")
            elif opcode == 0xEE: # XRI byte
                immediate_value = self.memory[self.registers['PC']]
                self.registers['PC'] += 1
                self.registers['A'] ^= immediate_value

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag

                if self.debuglevel >= 4:
                    print(f"XRI A: A={self.registers['A']:02X} byte={immediate_value:02X}:")
            elif opcode == 0xEF:  # RST 5
                self.memory[self.registers['SP'] - 1] = (self.registers['PC'] >> 8) & 0xFF  # Push high byte of PC
                self.memory[self.registers['SP'] - 2] = self.registers['PC'] & 0xFF  # Push low byte of PC
                self.registers['SP'] -= 2
                self.registers['PC'] = 0x28

                if self.debuglevel >= 4:
                    print(f"RST 5 call: {self.registers['PC']:04X}")
            elif opcode == 0xF0:  # RP
                if not (self.registers['FLAGS'] & (1 << 7)):  # Check if the sign flag is not set
                    self.registers['PC'] = self.memory[self.registers['SP']] | (self.memory[self.registers['SP'] + 1] << 8)
                    self.registers['SP'] += 2

                    if self.debuglevel >= 4:
                        print(f"RP: {addr:04X}") 
            elif opcode == 0xF1: # POP PSW
                self.registers['FLAGS'] = self.memory[self.registers['SP']]
                self.registers['A'] = self.memory[self.registers['SP'] + 1]
                self.registers['SP'] += 2

                if self.debuglevel >= 4:
                    print("POP PSW") 
            elif opcode == 0xF2:  # JP M, addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                if not (self.registers['FLAGS'] & (1 << 7)):  # Check if the sign flag is set
                    self.registers['PC'] = addr

                    if self.debuglevel >= 4:
                        print(f"JP jump: {addr:04X}")
                else:
                    self.registers['PC'] += 2
            elif opcode == 0xF3:
                self.interrupt_enabled = False

                if self.debuglevel >= 3:
                    print("Interrupts Disabled")  # DI   
            elif opcode == 0xF4:  # CP addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                if not (self.registers['FLAGS'] & (1 << 7)):  # Check if the sign flag is not set
                    self.registers['PC'] += 2
                    self.memory[self.registers['SP'] - 1] = (self.registers['PC'] >> 8) & 0xFF  # Push high byte of PC
                    self.memory[self.registers['SP'] - 2] = self.registers['PC'] & 0xFF  # Push low byte of PC
                    self.registers['SP'] -= 2
                    self.registers['PC'] = addr

                    if self.debuglevel >= 4:
                        print(f"CP call: {addr:04X}")     
                else:
                    self.registers['PC'] += 2 
            elif opcode == 0xF5: # PUSH PSW
                self.memory[self.registers['SP'] - 1] = self.registers['A']
                self.memory[self.registers['SP'] - 2] = self.registers['FLAGS']
                self.registers['SP'] -= 2  

                if self.debuglevel >= 4:
                    print("PUSH PSW")                 
            elif opcode == 0xF6:  # ORI byte
                immediate_value = self.memory[self.registers['PC']]  # Fetch the immediate byte
                self.registers['PC'] += 1  # Increment the program counter
                self.registers['A'] |= immediate_value  # Perform bitwise OR between A and the immediate byte

                # Clear flags
                self.registers['FLAGS'] &= ~(1 << 7)  # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6)  # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4)  # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2)  # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0)  # Clear carry flag

                # Set flags based on the result in the A register
                if self.registers['A'] == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if self.registers['A'] & 0x80:
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(self.registers['A']).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag  

                if self.debuglevel >= 4:
                    print(f"ORI A: A={self.registers['A']:02X} byte={immediate_value}")    
            elif opcode == 0xF7: # RST 6
                self.memory[self.registers['SP'] - 1] = (self.registers['PC'] >> 8) & 0xFF  # Push high byte of PC
                self.memory[self.registers['SP'] - 2] = self.registers['PC'] & 0xFF         # Push low byte of PC
                self.registers['SP'] -= 2
                self.registers['PC'] = 0x30   

                if self.debuglevel >= 4:
                    print(f"RST 6 call: {self.registers['PC']:04X}")
            elif opcode == 0xF8:  # RM
                if self.registers['FLAGS'] & (1 << 7):  # Check if the sign flag is set
                    self.registers['PC'] = self.memory[self.registers['SP']] | (self.memory[self.registers['SP'] + 1] << 8)
                    self.registers['SP'] += 2

                    if self.debuglevel >= 4:
                        print(f"RM SP: {self.registers['SP']:04X}")
            elif opcode == 0xFA:  # JM addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                if self.registers['FLAGS'] & (1 << 7):  # Check if the sign flag is set
                    self.registers['PC'] = addr

                    if self.debuglevel >= 4:
                        print(f"JM addr: {addr:04X}")
                else:
                    self.registers['PC'] += 2
            elif opcode == 0xFB:
                self.interrupt_enabled = True

                if self.debuglevel >= 3:
                    print("Interrupts Enabled")  # EI  
            elif opcode == 0xFC:  # CM addr
                addr = (self.memory[self.registers['PC']] | (self.memory[self.registers['PC'] + 1] << 8))
                if self.registers['FLAGS'] & (1 << 7):  # Check if the sign flag is set
                    self.registers['PC'] += 2
                    self.memory[self.registers['SP'] - 1] = (self.registers['PC'] >> 8) & 0xFF  # Push high byte of PC
                    self.memory[self.registers['SP'] - 2] = self.registers['PC'] & 0xFF  # Push low byte of PC
                    self.registers['SP'] -= 2
                    self.registers['PC'] = addr

                    if self.debuglevel >= 4:
                        print(f"CM addr: {addr:04X}")
                else:
                    self.registers['PC'] += 2 
            elif opcode == 0xF9: # SPHL
                self.registers['SP'] = (self.registers['H'] << 8) | self.registers['L']  

                if self.debuglevel >= 4:
                    print(f"SPHL = {self.registers['SP']:04X}")
            elif opcode == 0xFE:  # CPI byte
                immediate_value = self.memory[self.registers['PC']]
                self.registers['PC'] += 1

                result = (self.registers['A'] - immediate_value) & 0xFF                

                # Update flags
                self.registers['FLAGS'] &= ~(1 << 7) # Clear sign flag
                self.registers['FLAGS'] &= ~(1 << 6) # Clear zero flag
                self.registers['FLAGS'] &= ~(1 << 4) # Clear auxiliary carry flag
                self.registers['FLAGS'] &= ~(1 << 2) # Clear parity flag
                self.registers['FLAGS'] &= ~(1 << 0) # Clear carry flag

                if result == 0:
                    self.registers['FLAGS'] |= (1 << 6)  # Set zero flag
                if result & (1 << (8 - 1)):
                    self.registers['FLAGS'] |= (1 << 7)  # Set sign flag
                if bin(result).count('1') % 2 == 0:
                    self.registers['FLAGS'] |= (1 << 2)  # Set parity flag
                if  self.registers['A'] < immediate_value:
                    self.registers['FLAGS'] |= (1 << 0)  # Set carry flag
                if (self.registers['A'] & 0x0F) < (immediate_value & 0xFF):
                    self.registers['FLAGS'] |= (1 << 4)  # Set auxiliary carry flag

                if self.debuglevel >= 4:
                    print(f"CPI: {result:02X}")
            elif opcode == 0xFF: # RST 7
                self.memory[self.registers['SP'] - 1] = (self.registers['PC'] >> 8) & 0xFF # Push high byte of PC
                self.memory[self.registers['SP'] - 2] = self.registers['PC'] & 0xFF # Push low byte of PC
                self.registers['SP'] -= 2
                self.registers['PC'] = 0x38

                if self.debuglevel >= 4:
                    print(f"RST 7 call: {self.registers['PC']:04X}")
            else:
                self.running = False

                print(f"Undefined opcode: {opcode:02X} at {pc:04X} = ABORTING!!!")

                for opc in range(0,0x100):
                    if opcodes_8080[opc][1] == 1:
                        print(f"{opcodes_8080[opc][0]}")

                if self.debuglogger == True:
                    self.debugloggerfile.write(f"Undefined opcode: {opcode:02X} at {pc:04X} = ABORTING!!!")
                    self.debuglogger = False

                    self.debugloggerfile.close()               
            
            if self.altair_singlestep == True:
                while len(self.inputbuffer) == 0 and self.altair_singlestep == True:
                    time.sleep(0.1)

                if len(self.inputbuffer):
                    self.inputbuffer.pop(0)   

            if self.singlestep == True:
                self.debug()

            if self.debuglogger == True:
                self.debug_write(self.debugloggerfile)


def on_mouse_click(event):
    x, y = event.x, event.y
    #print(f"Mouse clicked at ({x}, {y})")

def start_tkinter():
    root = tk.Tk()
    root.title("MITS Altair 8800")
    root.geometry("800x600")  # Set an initial size for the window
    root.resizable(True, True)  # Allow the window to be resizable  
    icon_photo = tk.PhotoImage(file='ttyicon.png')
    root.wm_iconphoto(False, icon_photo)
    root.configure(bg='#F5F5DC')

    # Load the front panel image
    image = Image.open('altair8800frontpanel.png')

    # Resize the image
    new_width = 800  # Adjust the width as needed
    new_height = int(new_width * image.height / image.width)  # Maintain aspect ratio
    image = image.resize((new_width, new_height), Image.LANCZOS)

    frontpanel_photo = ImageTk.PhotoImage(image)

    # Create a canvas to display the image and LEDs
    canvas = tk.Canvas(root, width=image.width, height=image.height)
    canvas.pack()

    # Display the image on the canvas
    canvas.create_image(0, 0, anchor=tk.NW, image=frontpanel_photo)
    canvas.image = frontpanel_photo  

    # Bind the mouse click event to the on_mouse_click function
    canvas.bind("<Button-1>", on_mouse_click)

    text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=20, font=("Dot Matrix", 14), bg='#F5F5DC', fg='black')
    text_area.pack(padx=10, pady=10)
    
    return (root, text_area, canvas)

def run_altair():
    global emulator_parser
    global emulator_args

    (root, text_area, canvas) = start_tkinter()

    print("Creating Altair 8800 Emulator")
    altair8800 = Altair8800(text_area, canvas, root=root)

    rom_argument = emulator_args.rom.split('=')[1] if '=' in emulator_args.rom else emulator_args.rom
    rom_filename = os.path.basename(rom_argument)
    altair8800.rom_file = rom_filename

    if emulator_args.usrfn:
        altair8800.usrfunction = True

    altair8800.load_rom(rom_filename)

    # disable TTY printer sound
    if emulator_args.nosound == True:
        altair8800.play_sound = False

    # add breakpoints
    if emulator_args.bp1: 
        altair8800.breakpoints.append(int(emulator_args.bp1, 16))

    if emulator_args.bp2:
        altair8800.breakpoints.append(int(emulator_args.bp2, 16))

    if emulator_args.bp3:
        altair8800.breakpoints.append(int(emulator_args.bp3, 16))

    if emulator_args.bp4:
        altair8800.breakpoints.append(int(emulator_args.bp4, 16))

    if emulator_args.bp5:
        altair8800.breakpoints.append(int(emulator_args.bp5, 16))

    if emulator_args.debuglevel:
        altair8800.debuglevel = emulator_args.debuglevel

    if emulator_args.debuglogger:
        altair8800.debuglogger = True            

    # moved to Power  switch call back
    #threading.Thread(target=altair8800.execute).start()
    root.mainloop()

if __name__ == "__main__":
    emulator_parser = argparse.ArgumentParser(description="Altair Emulator for 4K BASIC")
    emulator_parser.add_argument("rom", type=str, help="Load Intel 8080 binary, rom=basic.rom")
    emulator_parser.add_argument("--bp1", type=hex_type, help="Program code breakpoint #1 - 4 digit hexadecimal number")
    emulator_parser.add_argument("--bp2", type=hex_type, help="Program code breakpoint #2 - 4 digit hexadecimal number")
    emulator_parser.add_argument("--bp3", type=hex_type, help="Program code breakpoint #3 - 4 digit hexadecimal number")
    emulator_parser.add_argument("--bp4", type=hex_type, help="Program code breakpoint #4 - 4 digit hexadecimal number")
    emulator_parser.add_argument("--bp5", type=hex_type, help="Program code breakpoint #5 - 4 digit hexadecimal number")
    emulator_parser.add_argument("--debuglevel", type=int, choices=[1, 2, 3, 4], help="Set the debug information level (1-4)")
    emulator_parser.add_argument("--debuglogger", action="store_true", help="Enables saving debug info to dblogger.txt")
    emulator_parser.add_argument("--usrfn", action="store_true", help="Enables USR() functionality")
    emulator_parser.add_argument("--nosound", action="store_true", help="Do not play TTY printer sound")

    emulator_args = emulator_parser.parse_args()

    run_altair()
