;==============================================================================
; 具有录音功能的电子琴 - 8086汇编程序
; 功能：25键电子琴（2个八度+半音），录音200+音符，播放，暂停，清除
; 学号后四位滚动显示
;==============================================================================

;------------------------------------------------------------------------------
; 端口地址定义 (基于地址译码设计)
; 注意: 8086是16位CPU，A0用于字节选择，所以端口地址用A1对应芯片A0
;------------------------------------------------------------------------------
PORT_8255_A     EQU 0200H       ; 8255 端口A - 数码管段码输出/琴键行输入(分时)
PORT_8255_B     EQU 0202H       ; 8255 端口B - 琴键列扫描输出
PORT_8255_C     EQU 0204H       ; 8255 端口C - 低4位功能键输入，高4位数码管位选
PORT_8255_CTRL  EQU 0206H       ; 8255 控制寄存器

PORT_8253_CH0   EQU 0208H       ; 8253 通道0 - 音频输出
PORT_8253_CH1   EQU 020AH       ; 8253 通道1 - 定时
PORT_8253_CH2   EQU 020CH       ; 8253 通道2
PORT_8253_CTRL  EQU 020EH       ; 8253 控制寄存器

PORT_8259_A0    EQU 0210H       ; 8259 ICW1/OCW2
PORT_8259_A1    EQU 0212H       ; 8259 ICW2-4/OCW1

;------------------------------------------------------------------------------
; 常量定义
;------------------------------------------------------------------------------
MAX_NOTES       EQU 250         ; 最大存储音符数
TIMER_FREQ      EQU 1193182     ; 8253输入时钟频率

;------------------------------------------------------------------------------
; 数据段
;------------------------------------------------------------------------------
DATA SEGMENT
    ; 音符存储区 (每个音符3字节: 音符号1字节 + 时长2字节)
    note_buffer     DB 750 DUP(0)   ; 250 * 3 = 750字节
    note_count      DW 0            ; 当前存储的音符数量
    play_index      DW 0            ; 播放索引
    
    ; 状态标志
    is_recording    DB 0            ; 录音状态
    is_playing      DB 0            ; 播放状态
    is_paused       DB 0            ; 暂停状态
    
    ; 时间计数
    key_press_time  DW 0            ; 按键时长计数
    
    ; 学号后四位 (请修改为你的学号)
    student_id      DB 2,6,2,1      ; 学号后四位: 2621
    scroll_pos      DB 0            ; 滚动位置
    
    ; 7段数码管段码表 (共阴极 0-9)
    seg_table       DB 3FH,06H,5BH,4FH,66H,6DH,7DH,07H,7FH,6FH
    
    ; 音符频率表 (25个音符: C4到C6)
    ; 分频值 = 1193182 / 频率
    freq_table      DW 4560   ; C4  - 262Hz
                    DW 4304   ; C#4 - 277Hz
                    DW 4063   ; D4  - 294Hz
                    DW 3836   ; D#4 - 311Hz
                    DW 3619   ; E4  - 330Hz
                    DW 3416   ; F4  - 349Hz
                    DW 3224   ; F#4 - 370Hz
                    DW 3043   ; G4  - 392Hz
                    DW 2873   ; G#4 - 415Hz
                    DW 2711   ; A4  - 440Hz
                    DW 2559   ; A#4 - 466Hz
                    DW 2415   ; B4  - 494Hz
                    DW 2280   ; C5  - 523Hz
                    DW 2152   ; C#5 - 554Hz
                    DW 2031   ; D5  - 587Hz
                    DW 1918   ; D#5 - 622Hz
                    DW 1809   ; E5  - 659Hz
                    DW 1708   ; F5  - 698Hz
                    DW 1612   ; F#5 - 740Hz
                    DW 1521   ; G5  - 784Hz
                    DW 1436   ; G#5 - 831Hz
                    DW 1355   ; A5  - 880Hz
                    DW 1279   ; A#5 - 932Hz
                    DW 1207   ; B5  - 988Hz
                    DW 1140   ; C6  - 1047Hz
DATA ENDS

;------------------------------------------------------------------------------
; 代码段
;------------------------------------------------------------------------------
CODE SEGMENT
    ASSUME CS:CODE, DS:DATA
    
START:
    ; 初始化段寄存器
    MOV AX, DATA
    MOV DS, AX
    MOV ES, AX
    
    ; 初始化堆栈
    MOV AX, 0FFFFH
    MOV SP, AX
    
    ; 初始化外设
    CALL INIT_8255
    CALL INIT_8253
    CALL INIT_8259
    
    ; 清除存储
    CALL CLEAR_STORAGE
    
    ; 显示学号（启动时滚动显示）
    CALL SCROLL_DISPLAY
    
;------------------------------------------------------------------------------
; 主循环
;------------------------------------------------------------------------------
MAIN_LOOP:
    ; 扫描功能键
    CALL SCAN_FUNC_KEYS
    
    ; 检查播放状态
    CMP is_playing, 1
    JE DO_PLAY
    
    ; 扫描琴键
    CALL SCAN_PIANO_KEYS
    
    ; 刷新数码管显示
    CALL REFRESH_DISPLAY
    
    JMP MAIN_LOOP

DO_PLAY:
    CMP is_paused, 1
    JE MAIN_LOOP
    CALL PLAY_NOTE
    JMP MAIN_LOOP

;------------------------------------------------------------------------------
; 初始化8255
; 模式0: A口输出(段码), B口输出(列扫描), C口低4位输入(功能键), 高4位输出(位选)
; 控制字: 1 00 0 0 0 0 1 = 81H
;         |  | | | | | +-- PC0-3输入
;         |  | | | | +---- PC4-7输出
;         |  | | | +------ B口输出
;         |  | | +-------- 模式0
;         |  | +---------- A口输出
;         |  +------------ 模式0
;         +--------------- 模式设置
;------------------------------------------------------------------------------
INIT_8255 PROC
    MOV DX, PORT_8255_CTRL
    MOV AL, 10000001B       ; A输出, B输出, C低输入高输出
    OUT DX, AL
    RET
INIT_8255 ENDP

;------------------------------------------------------------------------------
; 初始化8253
; 通道0: 方波输出，用于产生音频
;------------------------------------------------------------------------------
INIT_8253 PROC
    MOV DX, PORT_8253_CTRL
    MOV AL, 00110110B       ; 通道0, 先低后高, 方波, 二进制
    OUT DX, AL
    
    ; 初始设置为静音（最大分频值）
    MOV DX, PORT_8253_CH0
    MOV AL, 0FFH
    OUT DX, AL
    MOV AL, 0FFH
    OUT DX, AL
    RET
INIT_8253 ENDP

;------------------------------------------------------------------------------
; 初始化8259
;------------------------------------------------------------------------------
INIT_8259 PROC
    ; ICW1
    MOV DX, PORT_8259_A0
    MOV AL, 00010011B       ; 边沿触发, 单片, 需要ICW4
    OUT DX, AL
    
    ; ICW2 - 中断向量号基址
    MOV DX, PORT_8259_A1
    MOV AL, 08H             ; 中断向量从08H开始
    OUT DX, AL
    
    ; ICW4
    MOV AL, 00000001B       ; 8086模式
    OUT DX, AL
    
    ; OCW1 - 开放所有中断
    MOV AL, 00H
    OUT DX, AL
    
    STI                     ; 开中断
    RET
INIT_8259 ENDP


;------------------------------------------------------------------------------
; 扫描功能键
; C口低4位: bit0=播放键, bit1=暂停键, bit2=清除键
;------------------------------------------------------------------------------
SCAN_FUNC_KEYS PROC
    PUSH AX
    PUSH DX
    
    MOV DX, PORT_8255_C
    IN AL, DX
    
    ; 检查播放键 (bit0)
    TEST AL, 01H
    JZ CHECK_PAUSE
    CALL START_PLAY
    JMP FUNC_DONE
    
CHECK_PAUSE:
    ; 检查暂停键 (bit1)
    TEST AL, 02H
    JZ CHECK_CLEAR
    CALL TOGGLE_PAUSE
    JMP FUNC_DONE
    
CHECK_CLEAR:
    ; 检查清除键 (bit2)
    TEST AL, 04H
    JZ FUNC_DONE
    CALL CLEAR_STORAGE
    
FUNC_DONE:
    ; 消抖延时
    CALL DELAY_SHORT
    POP DX
    POP AX
    RET
SCAN_FUNC_KEYS ENDP

;------------------------------------------------------------------------------
; 开始播放
;------------------------------------------------------------------------------
START_PLAY PROC
    MOV is_playing, 1
    MOV is_paused, 0
    MOV play_index, 0
    RET
START_PLAY ENDP

;------------------------------------------------------------------------------
; 切换暂停状态
;------------------------------------------------------------------------------
TOGGLE_PAUSE PROC
    CMP is_paused, 0
    JE SET_PAUSE
    MOV is_paused, 0
    JMP PAUSE_DONE
SET_PAUSE:
    MOV is_paused, 1
    CALL STOP_SOUND         ; 暂停时停止声音
PAUSE_DONE:
    RET
TOGGLE_PAUSE ENDP

;------------------------------------------------------------------------------
; 清除存储
;------------------------------------------------------------------------------
CLEAR_STORAGE PROC
    PUSH AX
    PUSH CX
    PUSH DI
    
    ; 清零音符缓冲区
    LEA DI, note_buffer
    MOV CX, 750
    MOV AL, 0
CLEAR_LOOP:
    MOV [DI], AL
    INC DI
    LOOP CLEAR_LOOP
    
    ; 重置计数器
    MOV note_count, 0
    MOV play_index, 0
    MOV is_playing, 0
    MOV is_paused, 0
    
    ; 显示学号（停止时滚动显示）
    CALL SCROLL_DISPLAY
    
    POP DI
    POP CX
    POP AX
    RET
CLEAR_STORAGE ENDP

;------------------------------------------------------------------------------
; 扫描琴键 (5x5矩阵键盘 = 25键)
; 需要临时将8255 A口设为输入模式读取行状态
; B口: 列扫描输出 (5位)
;------------------------------------------------------------------------------
SCAN_PIANO_KEYS PROC
    PUSH AX
    PUSH BX
    PUSH CX
    PUSH DX
    
    ; 临时将A口设为输入模式
    MOV DX, PORT_8255_CTRL
    MOV AL, 10010001B       ; A输入, B输出, C低输入高输出
    OUT DX, AL
    
    MOV CL, 0               ; 列计数
    MOV BL, 11111110B       ; 列扫描码，低电平有效
    
SCAN_COL:
    ; 输出列扫描码
    MOV DX, PORT_8255_B
    MOV AL, BL
    OUT DX, AL
    
    ; 短延时等待稳定
    CALL DELAY_SHORT
    
    ; 读取行状态
    MOV DX, PORT_8255_A
    IN AL, DX
    
    ; 检查是否有键按下 (低5位)
    AND AL, 00011111B
    CMP AL, 00011111B
    JE NEXT_COL
    
    ; 计算键号: 键号 = 列*5 + 行
    CALL CALC_KEY_NUM
    
    ; 处理按键
    CALL PROCESS_KEY
    
NEXT_COL:
    ; 移动到下一列
    ROL BL, 1
    INC CL
    CMP CL, 5
    JB SCAN_COL
    
    ; 恢复A口为输出模式
    MOV DX, PORT_8255_CTRL
    MOV AL, 10000001B       ; A输出, B输出, C低输入高输出
    OUT DX, AL
    
    POP DX
    POP CX
    POP BX
    POP AX
    RET
SCAN_PIANO_KEYS ENDP

;------------------------------------------------------------------------------
; 计算键号
; 输入: CL=列号, AL=行状态
; 输出: AH=键号 (0-24)
;------------------------------------------------------------------------------
CALC_KEY_NUM PROC
    PUSH CX
    
    ; 找到按下的行
    MOV CH, 0               ; 行号
FIND_ROW:
    TEST AL, 01H
    JZ FOUND_ROW
    SHR AL, 1
    INC CH
    CMP CH, 5
    JB FIND_ROW
    JMP CALC_DONE
    
FOUND_ROW:
    ; 键号 = 列*5 + 行
    MOV AL, CL
    MOV AH, 5
    MUL AH
    ADD AL, CH
    MOV AH, AL              ; 键号存入AH
    
CALC_DONE:
    POP CX
    RET
CALC_KEY_NUM ENDP

;------------------------------------------------------------------------------
; 处理按键
; 输入: AH=键号
;------------------------------------------------------------------------------
PROCESS_KEY PROC
    PUSH AX
    PUSH BX
    PUSH CX
    PUSH DX
    
    ; 播放当前音符
    MOV AL, AH
    CALL PLAY_TONE
    
    ; 记录按键开始时间
    MOV key_press_time, 0
    
WAIT_RELEASE:
    ; 增加时长计数
    INC key_press_time
    CALL DELAY_10MS
    
    ; 检查按键是否释放
    MOV DX, PORT_8255_A
    IN AL, DX
    CMP AL, 11111111B
    JNE WAIT_RELEASE
    
    ; 停止声音
    CALL STOP_SOUND
    
    ; 存储音符和时长
    MOV AL, AH              ; 音符号
    MOV BX, key_press_time  ; 时长
    CALL STORE_NOTE
    
    POP DX
    POP CX
    POP BX
    POP AX
    RET
PROCESS_KEY ENDP

;------------------------------------------------------------------------------
; 播放指定音符
; 输入: AL=音符号 (0-24)
;------------------------------------------------------------------------------
PLAY_TONE PROC
    PUSH AX
    PUSH BX
    PUSH DX
    
    ; 获取频率分频值
    MOV BL, AL
    MOV BH, 0
    SHL BX, 1               ; *2 因为是字表
    LEA AX, freq_table
    ADD BX, AX
    MOV AX, [BX]            ; AX = 分频值
    
    ; 设置8253通道0
    PUSH AX
    MOV DX, PORT_8253_CTRL
    MOV AL, 00110110B       ; 通道0, 方波
    OUT DX, AL
    POP AX
    
    ; 写入分频值
    MOV DX, PORT_8253_CH0
    OUT DX, AL              ; 低字节
    MOV AL, AH
    OUT DX, AL              ; 高字节
    
    POP DX
    POP BX
    POP AX
    RET
PLAY_TONE ENDP

;------------------------------------------------------------------------------
; 停止声音
;------------------------------------------------------------------------------
STOP_SOUND PROC
    PUSH AX
    PUSH DX
    
    ; 设置最大分频值（静音）
    MOV DX, PORT_8253_CTRL
    MOV AL, 00110110B
    OUT DX, AL
    
    MOV DX, PORT_8253_CH0
    MOV AL, 0
    OUT DX, AL
    MOV AL, 0
    OUT DX, AL
    
    POP DX
    POP AX
    RET
STOP_SOUND ENDP


;------------------------------------------------------------------------------
; 存储音符
; 输入: AL=音符号, BX=时长
;------------------------------------------------------------------------------
STORE_NOTE PROC
    PUSH AX
    PUSH BX
    PUSH DI
    
    ; 检查是否已满
    CMP note_count, MAX_NOTES
    JAE STORE_DONE
    
    ; 计算存储地址: 地址 = note_buffer + note_count * 3
    MOV DI, note_count
    MOV AH, 3
    PUSH AX
    MOV AL, DI
    MUL AH
    MOV DI, AX
    POP AX
    LEA AX, note_buffer
    ADD DI, AX
    
    ; 存储音符号
    MOV AL, AL
    MOV [DI], AL
    
    ; 存储时长
    MOV [DI+1], BL
    MOV [DI+2], BH
    
    ; 增加计数
    INC note_count
    
STORE_DONE:
    POP DI
    POP BX
    POP AX
    RET
STORE_NOTE ENDP

;------------------------------------------------------------------------------
; 播放存储的音符
;------------------------------------------------------------------------------
PLAY_NOTE PROC
    PUSH AX
    PUSH BX
    PUSH CX
    PUSH DI
    
    ; 检查是否播放完毕
    MOV AX, play_index
    CMP AX, note_count
    JAE PLAY_FINISHED
    
    ; 计算地址
    MOV DI, AX
    MOV CL, 3
    MOV AX, DI
    MUL CL
    MOV DI, AX
    LEA AX, note_buffer
    ADD DI, AX
    
    ; 读取音符号
    MOV AL, [DI]
    
    ; 读取时长
    MOV BL, [DI+1]
    MOV BH, [DI+2]
    
    ; 播放音符
    CALL PLAY_TONE
    
    ; 延时（按时长）
    MOV CX, BX
PLAY_DELAY:
    CALL DELAY_10MS
    
    ; 检查暂停
    CMP is_paused, 1
    JE PLAY_PAUSE_EXIT
    
    LOOP PLAY_DELAY
    
    ; 停止声音
    CALL STOP_SOUND
    
    ; 下一个音符
    INC play_index
    JMP PLAY_EXIT
    
PLAY_FINISHED:
    ; 播放完毕
    MOV is_playing, 0
    MOV play_index, 0
    CALL STOP_SOUND
    
    ; 显示学号（停止播放时滚动显示）
    CALL SCROLL_DISPLAY
    JMP PLAY_EXIT
    
PLAY_PAUSE_EXIT:
PLAY_EXIT:
    POP DI
    POP CX
    POP BX
    POP AX
    RET
PLAY_NOTE ENDP

;------------------------------------------------------------------------------
; 滚动显示学号后四位
;------------------------------------------------------------------------------
SCROLL_DISPLAY PROC
    PUSH AX
    PUSH BX
    PUSH CX
    PUSH DX
    
    MOV CX, 8               ; 滚动8次
    
SCROLL_LOOP:
    PUSH CX
    MOV CX, 50              ; 每个位置显示50次
    
DISPLAY_LOOP:
    ; 显示4位数码管
    CALL DISPLAY_4DIGITS
    CALL DELAY_SHORT
    LOOP DISPLAY_LOOP
    
    ; 更新滚动位置
    INC scroll_pos
    AND scroll_pos, 03H     ; 保持0-3
    
    POP CX
    LOOP SCROLL_LOOP
    
    POP DX
    POP CX
    POP BX
    POP AX
    RET
SCROLL_DISPLAY ENDP

;------------------------------------------------------------------------------
; 显示4位数码管
; 使用8255: A口输出段码, C口高4位(PC4-PC7)输出位选
;------------------------------------------------------------------------------
DISPLAY_4DIGITS PROC
    PUSH AX
    PUSH BX
    PUSH CX
    PUSH DX
    PUSH SI
    
    MOV CL, 4               ; 4位数码管
    MOV CH, 0               ; 当前位
    MOV BL, 00010000B       ; 位选码从PC4开始
    
DISP_DIGIT:
    ; 计算显示的数字索引（滚动效果）
    MOV AL, CH
    ADD AL, scroll_pos
    AND AL, 03H
    
    ; 获取学号数字
    LEA SI, student_id
    MOV AH, 0
    ADD SI, AX
    MOV AL, [SI]
    
    ; 获取段码
    LEA SI, seg_table
    MOV AH, 0
    ADD SI, AX
    MOV AL, [SI]
    
    ; 输出段码到A口
    MOV DX, PORT_8255_A
    OUT DX, AL
    
    ; 读取C口当前值，保留低4位，设置高4位为位选
    MOV DX, PORT_8255_C
    IN AL, DX
    AND AL, 00001111B       ; 保留低4位(功能键状态)
    OR AL, BL               ; 设置位选
    OUT DX, AL
    
    ; 短延时
    CALL DELAY_SHORT
    
    ; 关闭显示（消隐）- 清除高4位
    MOV DX, PORT_8255_C
    IN AL, DX
    AND AL, 00001111B
    OUT DX, AL
    
    ; 下一位
    SHL BL, 1
    INC CH
    CMP CH, 4
    JB DISP_DIGIT
    
    POP SI
    POP DX
    POP CX
    POP BX
    POP AX
    RET
DISPLAY_4DIGITS ENDP

;------------------------------------------------------------------------------
; 刷新数码管显示（主循环中调用）
;------------------------------------------------------------------------------
REFRESH_DISPLAY PROC
    CALL DISPLAY_4DIGITS
    RET
REFRESH_DISPLAY ENDP

;------------------------------------------------------------------------------
; 短延时（约1ms）
;------------------------------------------------------------------------------
DELAY_SHORT PROC
    PUSH CX
    MOV CX, 1000
DELAY_S1:
    NOP
    LOOP DELAY_S1
    POP CX
    RET
DELAY_SHORT ENDP

;------------------------------------------------------------------------------
; 10ms延时
;------------------------------------------------------------------------------
DELAY_10MS PROC
    PUSH CX
    MOV CX, 10
DELAY_10:
    CALL DELAY_SHORT
    LOOP DELAY_10
    POP CX
    RET
DELAY_10MS ENDP

CODE ENDS
END START
