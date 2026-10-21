 /*
 用二维数组编程计算并输出n(n<20)行杨辉三角形。
**输入提示信息要求："Input  n(n<20):\n"
**输入格式："%d"
**输出要求："%4d"
            每输出一行后就换行
*/

#include<stdio.h>
#define N  21
int main()
{
    int a[N][N] = {0};
    int i, j;
    int n;
    printf("Input  n(n<20):\n");
    scanf("%d", &n);
    a[1][1] = 1;
    for (i = 2; i <= n; i++)
        for (j = 1; j <= i; j++)
            a[i][j] = a[i - 1][j - 1] + a[i - 1][j];

    for (i = 1; i <= n; i++)
    {
        for (j = 1; j <= i; j++)
            printf("%4d", a[i][j]);
        printf("\n");
    }
    return 0;
}

/*
#include<stdio.h>
#define  N  20
main() {
    int a[N][N] = {0}, n, i, j;
    printf("Input  n(n<20):\n");
    scanf("%d", &n);//1

    for (i = 0; i < n; i++) //1
    {
        for (j = 0; j <= i; j++) //1
        {
            if (j == 0 || i == j) //1
            {
                a[i][j] = 1;//1
            }
            else
            {
                a[i][j] = a[i - 1][j - 1] + a[i - 1][j];//1
            }
        }
    }

    for (i = 0; i < n; i++) //1
    {
        for (j = 0; j <= i; j++) //1
        {
            printf("%4d", a[i][j]);//1
        }
        printf("\n");//1
    }
}
*/
