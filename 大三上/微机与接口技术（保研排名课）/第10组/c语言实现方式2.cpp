#include <iostream>
#include <iomanip>
#include <string>
void displayHexStepByStep(uint16_t bx) 
{
    uint16_t temp = bx;
    std::cout << "BX的初始值(十进制): " << std::dec << bx << std::endl;
    std::cout << "十六进制显示结果: ";
    // 模拟汇编的循环：处理4个十六进制数字
    for (int i = 0; i < 4; i++)
    {
    // 模拟 ROL BX,4：将高4位移到低4位
    temp = (temp << 4) | (temp >> 12);
    // 模拟 AND DL,0FH：提取低4位
    uint8_t digit = temp & 0x0F;
    // 模拟数字到ASCII的转换
    char displayChar;
    if (digit <= 9) {
        displayChar = '0' + digit;  // 模拟 OR DL,30H
    }
    else {
        displayChar = 'A' + (digit - 10); // 模拟 ADD DL,7
    }
    std::cout << displayChar;
    }
    std::cout << "H" << std::endl; 
}
int main() {
    uint16_t bx_value;
    std::cin >> bx_value;   // 对应汇编中的 MOV BX,20
    std::cout << "=== 方法3: 逐步模拟汇编代码 ===" << std::endl;
    displayHexStepByStep(bx_value);
    return 0;
}