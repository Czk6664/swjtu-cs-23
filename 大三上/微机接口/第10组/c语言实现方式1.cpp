#include <iostream>
#include <iomanip>
#include <string>
void displayHexSimple(uint16_t bx)
{
    std::cout << std::uppercase << std::setw(4) << std::setfill('0')<< std::hex << bx << "H" << std::endl; 
}
int main() {
    uint16_t bx_value;
    std::cin >> bx_value;   // 对应汇编中的 MOV BX,20
    std::cout << "=== 方法1: 使用C++流操作符 ===" << std::endl;
    displayHexSimple(bx_value);
    return 0;
}