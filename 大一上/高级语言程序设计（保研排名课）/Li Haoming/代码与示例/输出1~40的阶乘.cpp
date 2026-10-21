#include <stdio.h>
#include <string.h>
#define MAX_DIGITS 100  // 足够存储40!（47位）及以下所有阶乘
// 核心函数：基于前一个阶乘（result数组）计算当前n!，更新result和len
void calculate_factorial(int n, int result[], int *len) {
    int carry = 0;  // 进位值
    // 用前一个阶乘（result存储）乘以当前n，得到n!
    for (int j = 0; j < *len; j++) {
        int product = result[j] * n + carry;
        result[j] = product % 10;  // 更新当前位
        carry = product / 10;      // 更新进位
    }
    // 处理剩余进位（多位数进位）
    while (carry > 0) {
        result[*len] = carry % 10;
        carry /= 10;
        (*len)++;  // 结果位数增加
    }
}

int main() {
    int result[MAX_DIGITS];
    int len;  // 当前阶乘的位数
    // 计算并输出1! 至 40!
    for (int n = 1; n <= 40; n++) {
        memset(result, 0, sizeof(int) * MAX_DIGITS);  // 每次初始化数组
        result[0] = 1;  // 1! 的初始值
        len = 1;        // 1! 的位数为1
        if (n >= 2) {
            // 从2乘到n（基于1!计算2!，基于2!计算3!，...，基于(n-1)!计算n!）
            for (int i = 2; i <= n; i++) {
                calculate_factorial(i, result, &len);
            }
        }
        // 输出当前n!（数组低位在前，反向输出）
        printf("%2d! = ", n);  // %2d 使序号对齐（1-9占2位，10-40正常显示）
        for (int i = len - 1; i >= 0; i--) {
            printf("%d", result[i]);
        }
        printf(" (%d位)\n", len);  // 显示当前阶乘的位数
    }
    return 0;
}
