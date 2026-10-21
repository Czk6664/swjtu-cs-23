/*
找出一个二维数组中的鞍点，即该位置上的元素在该行最大，在该列上最小。也可能没有鞍点。
**输入数据格式：
"\n输入行数："
"%d"
"\n输入列数："
"%d"
"第%d行？\n"
"%d"
**输出格式要求：
"%5d"
"\n第%d行，第%d列的%d是鞍点\n"
"\n矩阵中无鞍点!\n"
程序的运行示例1如下：
输入行数：3
输入列数：3
第0行？
1 2 3
第1行？
4 5 6
第2行？
7 8 9
    1    2    3
    4    5    6
    7    8    9

第0行，第2列的3是鞍点
程序的运行示例2如下：
输入行数：2
输入列数：2
第0行？
1 2
第1行？
4 1
    1    2
    4    1

矩阵中无鞍点!
*/

#include <stdio.h>

#define     N   10
#define     M   10

int main()
{
    int i, j, k, m, n, flag1, flag2, a[N][M], max, maxi, maxj;

    printf("\n输入行数：");
    scanf("%d", &n);
    printf("\n输入列数：");
    scanf("%d", &m);

    for (i = 0; i < n; i++)
    {
        printf("第%d行？\n", i);
        for (j = 0; j < m; j++)
        {
            scanf("%d", &a[i][j]);
        }
    }
    for (i = 0; i < n; i++)
    {
        for (j = 0; j < m; j++)
        {
            printf("%5d", a[i][j]);
        }
        printf("\n");
    }
    flag2 = 0;
    for (i = 0; i < n; i++)
    {
        max = a[i][0];
        for (j = 0; j < m; j++)
        {
            if (a[i][j] > max)
            {
                max = a[i][j];
                maxj = j;
            }
        }
        for (k = 0, flag1 = 1; k < n && flag1; k++)
        {
            if (max > a[k][maxj])
            {
                flag1 = 0;
            }
        }
        if (flag1)
        {
            printf("\n第%d行，第%d列的%d是鞍点\n", i, maxj, max);
            flag2 = 1;
        }
    }
    if (!flag2)
    {
        printf("\n矩阵中无鞍点!\n");
    }

    return 0;
}
