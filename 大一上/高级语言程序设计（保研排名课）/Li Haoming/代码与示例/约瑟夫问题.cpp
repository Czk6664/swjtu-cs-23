#include <stdio.h>

// 定义最大支持的总人数（可按需修改，如改为10000支持更多人）
#define MAX_N 1000

/**
 * 静态数组筛选法求解约瑟夫环（无指针+无动态数组）
 * @param n: 总人数（1~n为初始位置，n≤MAX_N）
 * @param m: 报数阈值（报到m的人被淘汰）
 * @param k: 起始报数位置（1~n，支持k>n自动调整）
 * @return: 最后剩余人的初始位置，错误返回-1
 */
int josephus_filter(int n, int m, int k) {
    // 1. 输入合法性校验（含MAX_N限制）
    if (n < 1 || m < 1 || k < 1) {
        printf("错误：n、m、k必须为正整数！\n");
        return -1;
    }
    if (n > MAX_N) {
        printf("错误：总人数n不能超过%d（可修改MAX_N常量扩展）！\n", MAX_N);
        return -1;
    }
    // 调整起始位置k（k>n时转为有效位置，如n=5、k=7→k=2）
    k = (k - 1) % n + 1;
    if (n == 1) { // 边界条件：仅1人时直接返回
        return 1;
    }

    // 2. 静态数组存储淘汰状态（0=未淘汰，1=已淘汰）
    // 无指针、无动态分配，直接声明静态数组
    int is_eliminated[MAX_N] = {0}; // 静态数组默认初始化为0，也可手动循环置0

    int remain = n;               // 剩余未淘汰人数
    int current_idx = k - 1;      // 起始位置的数组索引（1~n→0~n-1）
    int count = 0;                // 报数计数器（仅对未淘汰的人计数）

    // 3. 筛选淘汰过程：直到剩余1人
    while (remain > 1) {
        // 跳过已淘汰的人，仅对未淘汰的人报数
        if (is_eliminated[current_idx] == 0) {
            count++; // 报数+1
            // 报到m时，标记为淘汰
            if (count == m) {
                is_eliminated[current_idx] = 1; // 筛选淘汰当前人
                remain--;                      // 剩余人数-1
                count = 0;                     // 重置报数器
                printf("淘汰：第%d人\n", current_idx + 1); // 可选：打印淘汰顺序
            }
        }
        // 环形移动到下一个人（索引循环：0→1→...→n-1→0）
        current_idx = (current_idx + 1) % n;
    }

    // 4. 找到最后未淘汰的人（返回初始位置：索引+1）
    int result = -1;
    for (int i = 0; i < n; i++) {
        if (is_eliminated[i] == 0) {
            result = i + 1;
            break;
        }
    }

    return result;
}

// 主函数：测试（无指针+无动态数组）
int main() {
    int n, m, k;
    printf("=== 约瑟夫环（静态数组筛选法）===\n");
    printf("当前最大支持人数：%d\n", MAX_N);
    printf("请输入总人数n：");
    scanf("%d", &n);
    printf("请输入报数阈值m（报到m淘汰）：");
    scanf("%d", &m);
    printf("请输入起始报数位置k：");
    scanf("%d", &k);

    int final_pos = josephus_filter(n, m, k);
    if (final_pos != -1) {
        printf("\n最后剩余的人的初始位置是：%d\n", final_pos);
    }

    return 0;
}
