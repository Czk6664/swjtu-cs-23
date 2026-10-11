CODE SEGMENT
    ASSUME CS:CODE, DS:CODE

; 定义数据
MSG     DB '请输入十进制数(0-65535): $'  ; 输入提示
BUFFER  DB 6,0,6 DUP(0)                  ; 输入缓冲区(最大5位数字+回车)
CRLF    DB 0DH,0AH,'$'                   ; 回车换行

START:
    MOV AX, CODE
    MOV DS, AX

; 显示输入提示
    MOV AH, 09H
    LEA DX, MSG
    INT 21H

; 读取用户输入
    MOV AH, 0AH         ; 读取字符串
    LEA DX, BUFFER
    INT 21H

; 输入后换行
    MOV AH, 09H
    LEA DX, CRLF
    INT 21H

; 将输入的十进制字符串转换为二进制数(存入BX)
    MOV SI, OFFSET BUFFER + 2  ; 指向第一个输入字符
    MOV CL, [BUFFER + 1]       ; 实际输入长度
    MOV CH, 0                  ; CX = 字符数
    MOV BX, 0                  ; 结果初始化

CONVERT:
    MOV AL, [SI]
    SUB AL, '0'                ; 字符转数字
    MOV AH, 0
    XCHG AX, BX                ; BX暂存到AX，新数字在BX
    MOV DX, 10
    MUL DX                     ; AX = 原BX * 10
    ADD BX, AX                 ; BX = 原BX*10 + 新数字
    INC SI
    LOOP CONVERT

; 显示6位16进制数（修正版本）
    MOV SI, BX                 ; 用SI暂存BX的值
    MOV DH, 6                  ; 使用DH作为循环计数器（8位）

DISPLAY:
    ; 根据DH的值确定移位量: (DH-1)*4
    ; DH=6 -> 20, DH=5 -> 16, DH=4 -> 12, DH=3 -> 8, DH=2 -> 4, DH=1 -> 0
    MOV CL, DH
    DEC CL                     ; CL = DH - 1
    SHL CL, 2                  ; CL = (DH-1) * 4，左移2位等于乘4
    
    ; 如果移位量>=16，直接输出0
    CMP CL, 16
    JAE OUTPUT_ZERO
    
    ; 否则右移提取
    MOV AX, SI                 ; 加载原始值
    SHR AX, CL                 ; 右移
    AND AL, 0FH                ; 只保留低4位
    JMP CONVERT_CHAR
    
OUTPUT_ZERO:
    MOV AL, 0                  ; 高位补0

CONVERT_CHAR:
    
    ; 转换为ASCII字符
    CMP AL, 10
    JB IS_DIGIT                ; 如果<10，是数字0-9
    ADD AL, 'A' - 10           ; 如果>=10，转换为A-F
    JMP PRINT
    
IS_DIGIT:
    ADD AL, '0'                ; 转换为字符'0'-'9'

PRINT:
    MOV DL, AL                 ; 准备显示
    MOV AH, 02H
    INT 21H
    
    DEC DH                     ; 计数器减1
    JNZ DISPLAY                ; 继续循环

; 显示16进制后缀'H'
    MOV DL, 'H'
    MOV AH, 02H
    INT 21H

; 程序结束
    MOV AH, 4CH
    INT 21H

CODE ENDS
    END START
