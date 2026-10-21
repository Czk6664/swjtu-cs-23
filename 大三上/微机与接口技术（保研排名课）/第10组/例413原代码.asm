
; You may customize this and other start-up templates; 
; The location of this template is c:\emu8086\inc\0_com_template.txt

org 000h

CODE SEGMENT
    ASSUME CS:CODE,DS:CODE
START:
    MOV AX,CODE
    MOV DS,AX
    MOV BX,20
    MOV CH,4
    
NEXT:
    MOV CL,4
    ROL BX,CL
    MOV DL,BL
    AND DL,0FH
    OR  DL,30H
    CMP DL,39H
    JBE DISPHEX 
    ADD DL,7       
    
DISPHEX:
    MOV AH,2
    INT 21H
    DEC CH
    JNZ NEXT
    MOV DL,'H'
    MOV AH,2
    INT 21H   
    MOV AH,4CH
    INT 21H
CODE ENDS
    END START

ret




