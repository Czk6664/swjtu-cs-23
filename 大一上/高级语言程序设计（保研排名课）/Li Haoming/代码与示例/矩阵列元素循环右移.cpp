/*
将一个3X4的二维数组a中的每个元素向右移一列，最右一列换到最前面一列，移动后的数组存到另一个二维数组b中，并按矩阵形式输出a和b

输入提示信息："Input array a:\n"
输入数据格式："%d"
输出提示信息："Array a:\n"
输出数据格式："%5d"
输出提示信息："Array b:\n"
输出数据格式："%5d"

输入输出样例：
输入提示信息：Input array a:
输入：
1 2 3 4 5 6 7 8 9 10 11 12↙
输出：
Array a:
    1    2    3    4
    5    6    7    8
    9   10   11   12
Array b:
    4    1    2    3
    8    5    6    7
   12    9   10   11

*/

#include <stdio.h>
#include <stdlib.h>
int main()
{
    int a[3][4];
    int i,j,m;
    puts("Input array a:");  //1
    for(i=0; i<3; i++) //1
        for(j=0; j<4; j++)  //1
            scanf("%d",&a[i][j]);

    puts("Array a:");  //1

    for(i=0; i<3; i++) //1
        for(j=0; j<4; j++) //1
        {
            printf("%5d",a[i][j]);   //1
            if((j+1)%4==0)   //2
                printf("\n");
        }

    for(i=0; i<3; i++) //1
    {
        m=a[i][3];   //1
        for(j=3; j>0; j--) //1
        {
            a[i][j]=a[i][j-1];   //1
        }
        a[i][0]=m;   //1
    }

    puts("Array b:");

    for(i=0; i<3; i++) //1
        for(j=0; j<4; j++) //1
        {
            printf("%5d",a[i][j]);   //1
            if((j+1)%4==0)   //1
                printf("\n");
        }
    return 0;
}

/*
#include <stdio.h>
#define M 3
#define N 4
void print(int a[][N]); //1
int main()
{
    int a[M][N],b[M][N];
    int i,j;
    printf("Input array a:\n");
    for(i=0;i<M;i++)  //1
    {
        for(j=0;j<N;j++)  //1
        {
            scanf("%d",&a[i][j]); //1
        }
    }
      for(i=0;i<M;i++) //1
    {
        for(j=0;j<N-1;j++)   //2
        {

            b[i][j+1]=a[i][j];  //2
        }
    }
    printf("Array a:\n");
    print(a);
    for(i=0;i<M;i++)
        b[i][0]=a[i][N-1];  //1
    printf("Array b:\n");
   print(b);  //1
 return 0;
}


void print(int a[][N])
{
    int i,j;
    for(i=0;i<M;i++)
    {
        for(j=0;j<N;j++)
        {
           printf("%5d",a[i][j]);  //1

        }
         printf("\n");

    }
}
*/
