# Celebrating Microsoft's 50th Anniversary!
<img src="images/MicrosoftLogo.png" alt="Microsooft Logo" width="400" height="200"> 
Microsoft was founded on April 4, 1975. I wanted to create a project to honor its 50th anniversary during April 2025 by bringing together one Microsoft's first products and its most recent. <br> <br> <br>

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
<em>py -m pip install --upgrade pip [ENTER]</em> <br> <br>

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
* Download the BASIC disassembly-source.rom - the binary file (rom) the emulator will load (rename the file to remove the space) <br>
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
* Input 4080 [ENTER] - using usrfn option<br>

**Terminal Width Prompt:**<br>
* Input 80 [ENTER]<br>

**Optional Component Prompts:**<br>
* Want SIN: Input N [ENTER]<br>
* Want RND: Input N [ENTER] / Y [ENTER] to run randomnumbers.bas<br>
* Want SQR: Input N [ENTER]<br>
<br>

<img src="images/emulator.png" alt="Screenshot of Altair emulator window"> <br>
The test command has already been entered: <br>
<em>PRINT 2 + 2 [ENTER]</em> <br>

The data and address switches are single pole single throw (SPST), which means the switch is either on or off. Clicking the top of the gray circle will turn the switch on, while clicking on the bottom of the gray circle will turn the switch off. The default state of these switches is off.<br><br>
The Stop/Run, Single Step, Examine/Examine Next, and Deposit/Deposit Next are single pole double throw (SPDT) momentary toggle switches. With the exception of Single Step, these switches have dual actions when the switch is activated up or down.  The default state of these switches is in the center position.
<br>

## Debugging <br>
### Command Window <br>
This mode allows a user to debug emulator execution of the rom binary file via the Command Prompt window. Referencing BASIC disassembly-source.lst file, we will set a breakpoint at address 02C2 (InputLineWith subroutine) on the command line: <br>

<em>py altairemulator.py rom=BASICdisassembly-source.rom --bp1 02C2 [ENTER]</em> <br>

| Address    | Data | Label | Command|
| ----------- | ----------- |----------- |----------- |
|02C2|3E3F|InputLineWith|MVI A,'?'|
|02C4|DF | |RST 03 |
|02C5|3E20 | | MVI A,' '|
|02C7|DF | |RST 03|
|02C8|CD3C03  | |CALL InputLine|

Breakpoints – emulator will pause running when the Program Counter (PC) is equal to the value of a command line breakpoint address – 4-byte hexadecimal address. The emulator will switch to single step mode when a breakpoint is encountered.<br>

Breakpoint at pc:02C2 - press [ENTER] <br>

**Debug Commands:** <br>
[ENTER] – single step through emulator execution <br>

stack – starting at current Stack Pointer (SP) address, display 20 bytes from the stack<br>

mem – memory dump by from a starting address and displaying the contents of 20 bytes<br>

flags – displays the Sign, Zero, Auxiliary Carry, Parity, & Carry flags<br>

cont – exit single step mode and resume program execution <br>

Debug information displayed during Single Step mode: <br>

024C : EB XCHG = address : opcode opcode name <br>

SP: 0FFA<br>
A Reg: 00 | B Reg: 0C | C Reg: 31<br>
D Reg: 0C | E Reg: 33 | Flags: 46<br>
H Reg: 0C | L Reg: 22 <br><br>

### Altair Front Panel <br>
#### Single Step Mode:
1. Not active while the emulator is running<br>
2. Momentarily press up on Stop-Run switch to pause the program<br>
3. Momentarily press up on Single Step switch to execute an instruction, single stepping through program execution<br>
4. Program Counter (PC) will be displayed on the address LEDs (not updated during RUN mode) <br>
5. Opcode will be displayed on data LEDs (not updated during RUN mode)<br>
6. Single Step will not update LEDs after Examine switch is toggled up momentarily<br>
7. Momentarily press down on Stop/Run switch to resume program execution<br>

#### Examine Memory:
1. Not active while the emulator is running <br>
2. Momentarily press up on Stop-Run switch to pause the program<br>
3. Set the starting address of the program area to be examined by setting the address via Address-data switches A15 – A0<br>
4. Momentarily click up on Examine-Examine Next switch to read the memory contents of the starting address<br>
5. Memory contents is display in data LEDs D7 – D0<br>
6. To access the next address, momentarily click down on Examine-Examine Next switch<br>
7. The incremented address will be displayed in the Address LEDs A15-A0 and the memory contents will be displayed in the Data LEDs<br>
8. Momentarily press down on Stop/Run switch to resume program execution <br>
9. The Program Counter is not updated<br>
10. After Examine is toggled, the address cannot be changed. The address can be changed if the user toggles Stop-Run switch momentarily down then up.<br>
11. The Address and Data LEDs will represent the address and data bits<br>

#### Deposit Memory:
1. See steps 2 – 4 in Examine Memory to set the starting address of memory to update<br>
2. Set the Data switches (D7 – D0) to the value of the first byte to write<br>
3. Momentarily click up on Deposit-Deposit Next switch to write the first byte to the starting address<br>
4. Enter in the next value to be written using the Data switches (D7 – D0)<br>
5. Momentarily click down on Deposit-Deposit Next switch to write the next byte to the next address<br>
6. Repeat steps 4 and 5 to write to the remaining memory locations<br>
7. The Address and Data LEDs will represent the address and data bits<br><br>

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

If an altair 8800 could be modified to be able support enough memory to hold an LLM, how long would it take to load the LLM, assuming an 110 BAUD TTY terminal for entry?<br>

**Copilot:** To load a 1 GB large language model (LLM) into memory on a modified Altair 8800 using an 110 BAUD TTY terminal, it would take approximately 21,691.75 hours (about 2.5 years).<br>

**Starting Copilot prompt:** <br>
I want a Python script to emulate all Altair 8800 commands, LEDs are to be printed text statements, input ports are to be keyboard entries via an input_port function, outputs are to print statements via an output_port function, the program will read in a binary file, BASIC.rom and be able to simulate execution of the program.<br>

**Prompt to create simulated LEDs:** <br>
Using the tkinter base, I would to show an image using the file altair8800frontpanel.png, create a new class LED, which will represent the Altair 8800 LEDs.  The LED still have a state ON or OFF, methods to turn an LED off or on, get the status of the LED, assign a name to the LED.  The LEDs are to be circular with a diameter of 15 pixels.  When on, the LED will change to a bright red color, when off, the LED will be a dark red color. All LEDs will start off as OFF. A need a list of 36 LED objects.  The LED objects are to be placed at an x,y coordinate.<br>

**Prompt to create simulated front panel switches:** <br>
Using the tkinter base,  I would to show a create a new class Switch, which will represent the Altair 8800 front panel switches. There will 2 types of switches: toggle and momentary. The Switches are to be circular with a diameter color of 15 pixels, dark gray. The switch pole will be a rectangular box, 3x20 pixels, light gray. Each Switch object shall have a name and function to read status.<br>

Switch types:
Toggle: can be set to on or off. A user can move the switch up or down by clicking a mouse above or below the switch collar. The switch pole will move up or down when clicked.

Momentary: switch starts in the middle position and can be momentarily moved up or down. A user can momentarily toggle the switch up or down by clicking a mouse above or below the switch collar. After a momentarily toggle up or down, the switch will return to the center position.

I also need a method to be added to the class so I can register an event function to be called for a toggle switch off and on and for momentary switch up or down.  Create default event functions which have a print statement for the action and switch name. I need a method to change the switch type. <br>

<br>

**Copyright and Trademark Notices** <br>
Microsoft Copilot™ is a trademark of Microsoft Corporation. <br>
BASIC is a registered trademark of Dartmouth University. <br>
Intel® 8080 microprocessor. Intel is a trademark of Intel Corporation or its subsidiaries. <br>
MITS® Altair 8800. MITS is a trademark of Micro Instrumentation and Telemetry Systems (MITS), its subsidiaries, or successors. <br>
Micro-Soft Altair BASIC 3.2 (4K) © 1975, Bill Gates, Paul Allen, Monte Davidoff. <br>

