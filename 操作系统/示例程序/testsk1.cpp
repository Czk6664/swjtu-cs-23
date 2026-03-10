#include <stdio.h>
#include <string.h>
#include <ctype.h>

// 函数指针类型定义 - 用于指向不同的打印处理函数
typedef void (*PrinterFunc)(int, char**);

// 函数声明
void print_original(int, char**); // 按原始形式打印参数
void print_upper(int, char**);    // 将参数转换为大写后打印
void print_lower(int, char**);    // 将参数转换为小写后打印
int process_options(int, char**, PrinterFunc*); // 处理命令行选项并返回实际参数数量

int main(int argc, char *argv[]) {
    // 默认使用原始打印函数
    PrinterFunc printer = print_original;
    
    // 检查是否提供了至少一个参数(不包括程序名本身)
    if (argc < 2) {
        fprintf(stderr, "用法: %s <文本> [-up|-low]\n", argv[0]);
        return 1; // 参数不足，返回错误码1
    }
    
    // 处理命令行选项并获取实际需要处理的参数数量
    int processed_argc = process_options(argc, argv, &printer);
    
    // 确保至少有一个文本参数
    if (processed_argc < 1) {
        fprintf(stderr, "错误: 没有提供文本参数\n");
        return 1;
    }
    
    // 根据选项调用相应的打印函数
    printer(processed_argc, argv);
    return 0; // 成功执行，返回0
}

/**
 * 处理命令行选项，确定使用哪个打印函数并调整参数数量
 * @param argc 原始参数数量
 * @param argv 原始参数数组
 * @param printer 指向打印函数的指针(输出参数)
 * @return 实际需要处理的文本参数数量
 */
int process_options(int argc, char *argv[], PrinterFunc *printer) {
    char *last_arg = argv[argc - 1];
    
    // 检查最后一个参数是否为选项
    if (strcmp(last_arg, "-up") == 0) {
        *printer = print_upper; // 设置为大写打印函数
        return argc - 1;        // 返回不包含选项的参数数量
    } else if (strcmp(last_arg, "-low") == 0) {
        *printer = print_lower; // 设置为小写打印函数
        return argc - 1;        // 返回不包含选项的参数数量
    }
    
    // 没有选项，使用原始打印函数和全部参数
    return argc;
}

/**
 * 按原始形式打印命令行参数
 * @param argc 参数数量
 * @param argv 参数数组
 */
void print_original(int argc, char *argv[]) {
    for (int i = 1; i < argc; i++) {
        fputs(argv[i], stdout); // 输出完整参数
        putchar(' ');           // 添加分隔空格
    }
    putchar('\n'); // 换行
}

/**
 * 将命令行参数转换为大写后打印
 * @param argc 参数数量
 * @param argv 参数数组
 */
void print_upper(int argc, char *argv[]) {
    for (int i = 1; i < argc; i++) {
        for (int j = 0; argv[i][j]; j++) {
            // 转换为大写并输出，处理多字节字符
            putchar(toupper((unsigned char)argv[i][j]));
        }
        putchar(' '); // 添加分隔空格
    }
    putchar('\n'); // 换行
}

/**
 * 将命令行参数转换为小写后打印
 * @param argc 参数数量
 * @param argv 参数数组
 */
void print_lower(int argc, char *argv[]) {
    for (int i = 1; i < argc; i++) {
        for (int j = 0; argv[i][j]; j++) {
            // 转换为小写并输出，处理多字节字符
            putchar(tolower((unsigned char)argv[i][j]));
        }
        putchar(' '); // 添加分隔空格
    }
    putchar('\n'); // 换行
}