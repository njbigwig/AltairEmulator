# Celebrating Microsoft's 50th Anniversary!
<img src="images/MicrosoftLogo.png" alt="Microsooft Logo" width="400" height="200"> 
Microsoft was founded on April 4, 1975 and I wanted to create a project to honor its 50th anniversary in April 2025. <br> <br> <br>

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
**TOTAL: $1,500**

The MITS Altair 8800 User Manual can be found <a href="docs/Altair8800UserManual.pdf" target="_blank" rel="noopener noreferrer">here.</a>

I have been learning Python and I wanted to leverage Microsoft Copilot to help complete some of the complex tasks. The altairemulator.py emulates the MITS Altair 8800 and supports the execution of the Altair 4K BASIC binary. A user can interact with the emulator via the simulated front panel switches and LEDs. <br>

There sample BASIC programs included in this respository, including programs from the original Altair BASIC user manual:

| BASIC File     | Notes |
| ----------- | ----------- |
|compare2numbers |Is number A greater, less than or equal to number B|
|ctof  |Copilot - convert Celsius to Fahrenheit|
|helloworld|Classic first program|
|numberguess|Guess if a number has a match in a DATA set|
|primenumber|Bench to find 100 prime numbers - very long run time|
|randomnumbers|Generate 10 random numbers, 1-10, needs RND function at start|
|sort|Sort 8 numbers is ascending order|
|sumof2numbers|Add 2 numbers |
|usrfn|Assembly code implementation of USR() to read the Sense switches|
|zeroguess|Checks if a number is zero or not|

User function details - usr(10)
TBD

**Starting Copilot prompt**: <br>
I want a Python script to emulate all Altair 8800 commands, LEDs are to be printed text statements, input ports are to be keyboard entries via an input_port function, outputs are to print statements via an output_port function, the program will read in a binary file, BASIC.rom and be able to simulate execution of the program.

**Prompt to create simulated LEDs:** <br>
Using the tkinter base, I would to show an image using the file altair8800frontpanel.png, create a new class LED, which will represent the Altair 8800 LEDs.  The LED still have a state ON or OFF, methods to turn an LED off or on, get the status of the LED, assign a name to the LED.  The LEDs are to be circular with a diameter of 15 pixels.  When on, the LED will change to a bright red color, when off, the LED will be a dark red color. All LEDs will start off as OFF. A need a list of 36 LED objects.  The LED objects are to be placed at an x,y coordinate.

**Prompt to create simulated front panel switches:** <br>
Using the tkinter base,  I would to show a create a new class Switch, which will represent the Altair 8800 front panel switches. There will 2 types of switches: toggle and momentary. The Switches are to be circular with a diameter color of 15 pixels, dark gray. The switch pole will be a rectangular box, 3x20 pixels, light gray. Each Switch object shall have a name and function to read status.

Switch types:
Toggle: can be set to on or off. A user can move the switch up or down by clicking a mouse above or below the switch collar. The switch pole will move up or down when clicked.

Momentary: switch starts in the middle position and can be momentarily moved up or down. A user can momentarily toggle the switch up or down by clicking a mouse above or below the switch collar. After a momentarily toggle up or down, the switch will return to the center position.

I also need a method to be added to the class so I can register an event function to be called for a toggle switch off and on and for momentary switch up or down.  Create default event functions which have a print statement for the action and switch name. I need a method to change the switch type. <br>

**Copyright and Trademark Notices** <br>
Microsoft Copilot™ is a trademark of Microsoft Corporation. <br>
BASIC is a registered trademark of Dartmouth University. <br>
Intel® 8080 microprocessor. Intel is a trademark of Intel Corporation or its subsidiaries. <br>
MITS® Altair 8800. MITS is a trademark of Micro Instrumentation and Telemetry Systems (MITS), its subsidiaries, or successors. <br>
Micro-Soft Altair BASIC 3.2 (4K) © 1975, Bill Gates, Paul Allen, Monte Davidoff. <br>

