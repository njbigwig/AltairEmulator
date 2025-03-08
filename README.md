# Celebrating Microsoft's 50th Anniversary!
<img src="images/MicrosoftLogo.png" alt="Microsooft Logo" width="400" height="200"> 
Microsoft was founded on April 4, 1975. I wanted to create a project to honor its 50th anniversary during April 2025 by bringing together one Microsoft's first products and its most current. <br> <br> <br>

Concept by Dave Dempski with alot of heavy lifting by Microsoft Copilot!
<img src="images/CopilotLogo.png" alt="Copilot Logo" width="50" height="50"> <br> <br>

<img src="images/PopularElectronics.png" alt="Popular Electronics Magazine Front Cover" width="764" height="670"> <br>
© 1975 Popular Electronics. All rights reserved. <br>

The MITS Altair 8800 was one the first commmercially successful "personal" computers which offered low-cost opportunities to a wide range of people, from hobbyists to developers. The assembled costs (USD) included: <br>
* Altair 8800 computer: $621
* Altair 4K BASIC: $60
* 4K memory board: $338
* Teletype serial interface board: $146
* Teletype model 33: $1,500 <br>
**TOTAL: $2,665** <br>

The Altair 8800 User Manual can be found <a href="docs/Altair8800UserManual.pdf" target="_blank" rel="noopener noreferrer">here.</a> <br>

The Altair 8800 was an amazing product, but it was very difficult to use.  You had to manually set addresses (16 bits) and assembler instructions (8 bit opcodes) via an array of toggle switches. Assembly code is how a computer natively processes commands so it is very fast and efficient, but it can take dozens of assembler lines just to print out a string of characters.  A break through was needed to truly empower Altair 8800 programmers so they could write code faster and easier. A high-level language (HLL) was needed to bridge the gap between how humans represent things and how computers execute them. **Bill Gates, Paul Allen, and Monte Davidoff** launched Altair 4K BASIC on July 1, 1979. BASIC, Beginners All-purpose Instruction Code, was an HLL which efficiently bridged the gap. One of Micro-Soft's first products was not distributed via software download, CD, or floppy disk. It was on paper tape! It took approximately 8 minutes to load the Altair 4K BASIC program via the paper reader on a Teletype. <br><br>
<img src="images/altair4kbasic.png" alt="Section of Altair 4K BASIC paper tape program"> <br>


I have been learning Python. After reading some articles on the history and impacts Altair 8800, so I became fascinated with the trying to find an emulator to mimic how the Altair 8800 worked. Finding none, I started out with a concept and leveraged Microsoft Copilot to complete some of the complex tasks. The <em>altairemulator.py</em> emulates the MITS Altair 8800 and supports the execution of the Altair 4K BASIC binary. A user can interact with the emulator via the simulated front panel switches and LEDs. This program currently runs Windows PCs only. The emulator can support programs up to 64KB. Contributions and suggestions welcome! <br>

## Installation <br>

### Install Python (v3.12.9 or greater) <br>
* [Python.org](https://www.python.org/downloads/) <br>
* [Microsoft Store](https://apps.microsoft.com/detail/9NCVDN91XZQP?hl=en-us&gl=US&ocid=pdpshare) <br>

Update your Path Environmental Variable to include the directory where you installed the Python executables, e.g. py.exe <br>

If you have already installed Python, make sure your Python Package Manager (pip) is the latest version: <br>
<em>python.exe -m pip install --upgrade pip [ENTER]</em> <br> <br>

### Install Python Imaging Library (PIL) Package <br>
<em>pip install pillow [ENTER] </em><br> <br>

### Install Dot Matrix Font <br>
* Download font from: [Da Font](https://www.dafont.com/dot-matrix.font) <br>
* Extract the files from dot_matrix.zip <br>
* Right mouse click on DOTMATRI.TTF and select Install <br><br>

### Emulator Files <br>
* Create a directory to store the emulator files, e.g. c:\altair <br>
* From AltairEmulator, download all py, wav, bas, & png files to your directory <br><br>

### Altair 4K Source & Binary Files <br>
Charles Mangin and Reuben Harris have done some great work in compiling the Altair 4K BASIC source code and providing a binary program file. <br>
* Access the [Altair-BASIC GitHub repository](https://github.com/option8/Altair-BASIC)  <br>
* The files below need to be copied to your installation directory, e.g. c:\altair <br>
* Download the BASIC disassembly-source.rom - the binary file the emulator will load (rename the file to remove the space) <br>
* Download BASIC disassembly-source.lst - this is the assembled source file and includes the addresses if you want to explore or debug the code <br><br>

You will need a display, keyboard, and a mouse or touchpad to use the emulator. <br><br>

**Simulating a Teletype interface:** <br>
* You would enter in input via the keyboard and it was sent to a dot matrix printer = very slow & NO color monitor <br>
* There was no BACKSPACE key on teletype keyboard, use the underscore character (_) to delete the previous character <br>
* Altair 4K BASIC only supports uppercase characters, all alphabetical characters inputted are converted to uppercase <br> <br>
<img src="images/teletype.png" alt="Picture of Teletype Model 33" width="356" height="211"> <br>

<br>Sample BASIC programs included in this respository, including programs from the original Altair BASIC user manual:

| BASIC File     | Notes |
| ----------- | ----------- |
|compare2numbers |Is number A greater, less than, or equal to number B|
|ctof  |Copilot generated - convert Celsius to Fahrenheit|
|helloworld|Classic first program|
|numberguess|Guess if a number has a match in a DATA set|
|primenumber|Bench to find 100 prime numbers - very long run time|
|randomnumbers|Generate 10 random numbers, 1-10, needs RND function support at start-up|
|sort|Sort 8 numbers in ascending order|
|sumof2numbers|Add 2 numbers |
|usrfn|Assembly code implementation of USR() to read the Sense switches (port 255)|
|zeroguess|Checks if a number is zero or not| <br>

The Altair BASIC User Manual can be found <a href="docs/AltairBASICReferenceManual.pdf" target="_blank" rel="noopener noreferrer">here.</a> <br>

You can load a BASIC program (BAS text file) by clicking on the Load button at the lower right corner of the emulator screen. <br>

**User Function Details - usr(1):** <br>
4K BASIC defines function usr() to allow for user define custom functions. When usr() is not defined the function handler defaults to illegal function call. If PRINT USR(1) is RUN, the user will receive an FC error. When the emulator is started with the --usrfn option, an assembler function is added at 0x0FFO.  The handler vector at address 0x0043-0x0044 is changed from 0x0498 to 0x0FF0. The user() function will be defined as: <br>
<blockquote>
<em>0x0FF1 0xFF ; Port = 0xFF (255) <br>
    0x0FF2 0x47 ; MOV B,A  <br>
    0x0FF3 0xAF ; XRA A  <br>
    0x0FF4 0x2A ; LHLD  <br>
    0x0FF5 0x06 ; 0x0006 = 0x07F9 -> FWordToFloat  <br>
    0x0FF6 0x00  <br>
    0x0FF7 0xE9  ; PCHL </em> <br>
    </blockquote> 
The usr() function parameter is ignored. <br> <br>

## Getting Started <br>
### Starting the Altair Emulator <br>
Open a Command Prompt window and change to your installation directory.  To start the emulator, type in: <br>
<em>py altairemulator.py rom=BASICdisassembly-source.rom [ENTER]</em> <br><br>
The following options are available as command line arguements: <br>
**--nosound** = do not play the dot matrix printer sound as output is shown in the emulator window <br>
**--usrfn** = define user function (USR()) support, required to run usrfn.bas  <br>
**--bp1 to --bp5** = stop executing if Program Counter equals 1 of the 5 breakpoint hexadecimal addresses (XXXX), see "BASIC disassembly-source.lst"<br>
**--debuglevel 1-4** = print out debug information during program execution, higher level = greater cumulative details:
*	0 = default – no debug information <br>
*	1 = Program Counter + Opcode displayed <br>
*	2 = Show LED & Switch actions <br>
*	3 = Interrupts disabled or enabled <br>
*	4 = Prints opcode information <br>
**--debuglogger** = select debug information saved to dblogger.txt<br><br>
Note: displaying debug information will slow the emulator down. <br>

### **Power Switch** <br>
* To start the emulator, turn ON by clicking the green area <br>
* To exit the emulator, turn OFF by clicking the red area  <br>
<img src="images/powerswitch.png" alt="Close up of power switch with indications where to click" width="53" height="60"> <br><br>
The Altair emulator will launch in a separate window, maximize this window.  All keyboard input must be entered from the Command Window. Debug information, if enabled, will also be displayed in the Command Window.<br>

### 4K BASIC Configuration
**Memory Size Prompt:**<br>
* Input 4096 [ENTER] - standard operation<br>
* Input 4086 [ENTER] - using usrfn option<br>

**Terminal Width Prompt:**<br>
* Input 80 [ENTER]<br>

**Optional Component Prompts:**<br>
* Want SIN: Input N [ENTER]<br>
* Want RND: Input N [ENTER] / Y [ENTER] to run randomnumbers.bas<br>
* Want SQR: Input N [ENTER]<br>
<br>

<img src="images/emulator.png" alt="Screenshot of Altair emulator window"> <br>
The test command has already been entered: <br>
<em>PRINT 2 + 2 [ENTER]</em> <br> <br>

The data and address switches are single pole single throw (SPST), which means the switch is on or off. Clicking the top of the gray circle will turn the switch on, while clicking on the bottom of the gray circle will turn the switch off. The default state of these switches is off.<br><br>
The Stop/Run, Single Step, Examine/Examine Next, and Deposit/Deposit Next are single pole double throw (SPDT) momentary toggle switches. With the exception of Single Step, these switches have dual actions when the switch is activated up or down.  The default state of these switches is in the center position.
<br>

## Debugging <br>
### Command Window <br>
Breakpoints – emulator will pause running when the Program Counter (PC) is equal to the value of a command line breakpoint address – 4-byte hexadecimal address.

Breakpoint at {pc:04X} - press [ENTER]

Debug commands:
--Single Step: [ENTER] to step, mem, cont, stack or flags—

024C : EB XCHG = address : opcode opcode name

SP: 0FFA
A Reg: 00 | B Reg: 0C | C Reg: 31
D Reg: 0C | E Reg: 33 | Flags: 46
H Reg: 0C | L Reg: 22

[ENTER] – single step through emulator execution

stack – starting at current Stack Pointer (SP) address, display 20 bytes from the stack.

mem – memory dump by specify a starting address and displaying the contents of 20 bytes.

flags – displays the Sign, Zero, Auxiliary Carry, Parity, & Carry flags

cont – exit single step mode and resume program execution <br>

### Altair Front Panel <br>
1.	Single Step Mode (Altair Single Step – not emulator debugging):
a.	Not active while the emulator is running
b.	Momentarily press up on Stop position on Stop-Run switch to pause the program
c.	Momentarily press up on Single Step switch to execute an instruction, single stepping through program execution
d.	Program Counter (PC) will be displayed on the address LEDs (not updated during RUN mode) 
e.	Opcode will be displayed on data LEDs (not updated during RUN mode)
f.	Single Step will not update LEDs after Examine switch is toggled up momentarily
g.	Momentarily press down on Stop/Run switch to resume program execution
2.	Reset Program:
a.	Not active while the emulator is running
b.	Click Stop position (up) on Stop-Run switch to pause the program
c.	Click Reset position (up) on Reset-Clr switch to reset the Program Counter (PC) to 0x0000
d.	Momentarily press down on Stop/Run switch to restart program execution or momentarily press up on Single Step switch to execute an instruction
3.	Examine Memory:
a.	Not active while the emulator is running
b.	Click Stop position (up) on Stop-Run switch to pause the program
c.	Set the starting address of the program area to be examined by setting the address via Address-data switches A15 – A0
d.	Momentarily click Examine position (up) on Examine-Examine Next switch to read the memory contents of the indicated starting address
e.	Memory contents is display in data LEDs D7 – D0
f.	To access the next address, momentarily click Examine Next position (down) on Examine-Examine Next switch
g.	The incremented address will be displayed in the Address LEDs A15-A0 and the memory contents will be displayed in the Data LEDs
h.	Momentarily press down on Stop/Run switch to resume program execution
i.	The Program Counter is not updated
j.	After Examine is toggled, the address cannot be changed as the user can use Deposit and Deposit Next to change memory at an address.  D0-D7 switches are read to enter in opcodes or data.  The address can be changed if the user toggles Stop-Run switch momentarily up.
k.	The Address and Data LEDs will represent the address and data bits
4.	Deposit Memory
a.	See steps a – d in Examine Memory to set the starting address of memory to write to
b.	Set the Data switches (D7 – D0) to the value of the first byte to write
c.	Momentarily click Deposit position (up) on Deposit-Deposit Next switch to write the first byte to the starting address
d.	Enter in the next value to be written using the Data switches (D7 – D0)
e.	Momentarily click Deposit Next position (down) on Deposit-Deposit Next switch to write the next byte to the starting address
f.	Repeat steps d – e to write to the remaining memory locations
g.	The Address and Data LEDs will represent the address and data bits<br><br>

## Known Issues/Limitations <br>
1.	Fractional whole number division does not work, 1 / 2 = 1 <br>
2.	String variables are not supported (8K BASIC only) <br>
3.	SIN() function does not work <br>
4.	SQR() function does not work <br>
5.	String length function (LEN()) is not included with Altair BASIC 4K <br>
6.	Address and Data LEDs are lit only during Altrair front panel single step mode to maintain performance <br>
7.	Reset/Clr switch actions are not implemented <br>
8.  Protect/unprotect switch actions are not implemented <br>
9.  Just like the original Altair 8800, the Aux switches do have any functions <br><br>


**Starting Copilot prompt:** <br>
I want a Python script to emulate all Altair 8800 commands, LEDs are to be printed text statements, input ports are to be keyboard entries via an input_port function, outputs are to print statements via an output_port function, the program will read in a binary file, BASIC.rom and be able to simulate execution of the program.

**Prompt to create simulated LEDs:** <br>
Using the tkinter base, I would to show an image using the file altair8800frontpanel.png, create a new class LED, which will represent the Altair 8800 LEDs.  The LED still have a state ON or OFF, methods to turn an LED off or on, get the status of the LED, assign a name to the LED.  The LEDs are to be circular with a diameter of 15 pixels.  When on, the LED will change to a bright red color, when off, the LED will be a dark red color. All LEDs will start off as OFF. A need a list of 36 LED objects.  The LED objects are to be placed at an x,y coordinate.

**Prompt to create simulated front panel switches:** <br>
Using the tkinter base,  I would to show a create a new class Switch, which will represent the Altair 8800 front panel switches. There will 2 types of switches: toggle and momentary. The Switches are to be circular with a diameter color of 15 pixels, dark gray. The switch pole will be a rectangular box, 3x20 pixels, light gray. Each Switch object shall have a name and function to read status.

Switch types:
Toggle: can be set to on or off. A user can move the switch up or down by clicking a mouse above or below the switch collar. The switch pole will move up or down when clicked.

Momentary: switch starts in the middle position and can be momentarily moved up or down. A user can momentarily toggle the switch up or down by clicking a mouse above or below the switch collar. After a momentarily toggle up or down, the switch will return to the center position.

I also need a method to be added to the class so I can register an event function to be called for a toggle switch off and on and for momentary switch up or down.  Create default event functions which have a print statement for the action and switch name. I need a method to change the switch type. <br>

<br>
<br>

**Copyright and Trademark Notices** <br>
Microsoft Copilot™ is a trademark of Microsoft Corporation. <br>
BASIC is a registered trademark of Dartmouth University. <br>
Intel® 8080 microprocessor. Intel is a trademark of Intel Corporation or its subsidiaries. <br>
MITS® Altair 8800. MITS is a trademark of Micro Instrumentation and Telemetry Systems (MITS), its subsidiaries, or successors. <br>
Micro-Soft Altair BASIC 3.2 (4K) © 1975, Bill Gates, Paul Allen, Monte Davidoff. <br>

