5  REM MITS ALTAIR BASIC REFERENCE MANUAL PAGE 11
10 PRINT "GUESS A NUMBER: ";
20 INPUT G
30 READ D
40 IF D= -999999 THEN 90
50 IF D<>G THEN 30
60 PRINT "YOU ARE CORRECT!"
70 END
90 PRINT "BAD GUESS, TRY AGAIN."
95 RESTORE
100 GOTO 10
110 DATA 1,393,-39,28,391,-8,0,3.14,90
120 DATA 89,5,10,15,-34,-999999
