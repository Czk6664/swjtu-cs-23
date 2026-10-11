#include<stdio.h>
#include<string.h>
#include<time.h>
#include<stdlib.h>

int internal;
int duration;

void func_A()
{
    int i;
    char c[512];
    FILE *in1,*in2;
    in1=fopen("/proc/cpuinfo","r");//打开acpuinfo文件
    in2=fopen("/proc/version","r");//打开version文件
    //获取需要显示的信息
    for(i=0;i<5;i++)
        fgets(c,512,in1);
    printf("CPU类型及型号: %s",c+13);
    fgets(c,512,in2);
    printf("内核版本:%s",c);//转换时间显示形式
    fclose(in1);
    fclose(in2);
}
void func_B()
{
    FILE *in1,*in3;//*in2;//定义文件指针
    char c[512],d[32];//定义数组存放读取的信息
    int m,n,o,p,t,day,month,hour,sec;//存放读取信息
    struct tm *tp;//时间存储空间
    time_t timep;

    time(&timep);//初始化时间变量
    in3=fopen("/proc/uptime","r");//打开文件
    fscanf(in3,"%d",&p);//读取文件
    timep-=p;
    tp=localtime(&timep);//获取启动时间
    printf("系统最后启动时间为:%d/%d/%d %02d:%02d:%02d\n",tp->tm_year+1900,tp->tm_mon+1,tp->tm_mday,tp->tm_hour,tp->tm_min,tp->tm_sec);//显示系统最后启动时间给用户

    day=hour=month=sec=0;
    t=p;
    day=t/86400;
    t=t%86400;
    hour=t/3600;
    t=t%3600;
    month=t/60;
    t=t%60;
    sec=t;
    printf("系统最后一次启动以来的时间: %02d:%02d:%02d:%02d\n",day,hour,month,sec);

    in1=fopen("/proc/stat","r");
//    in2=fopen("/proc/diskstats","r");//打开文件
    fscanf(in1,"%s%*c%*c%d%*c%d%*c%d%*c%d",c,&m,&n,&o,&p);//获取所需信息量
    printf("用户态时间:%d(0.01秒) 系统态时间:%d(0.01秒) 空闲态时间:%d(0.01秒)\n",m,o,p);//显示用户态时间、系统态时间、空闲态时间
//    while(fgets(c,512,in2)!=NULL)
//    {
//        sscanf(c,"%d %d %s %d %d %d %d %d",&m,&m,d,&o,&m,&m,&m,&p);
//        if(d[0]=='s')
//        {
//            printf("系统接收到的磁盘请求%s:读%d，写%d，总计%d\n",d,o,p,o+p);
//            break;
//        }
//    }
    while(fgets(c,512,in1)!=NULL)
    {
        sscanf(c,"%s %d",d,&m);
        if(strcmp(d,"ctxt")==0)//定位到内核执行的上下文转换的次数
        printf("上下文转换的次数:%d\n",m);
        if(strcmp(d,"processes")==0)//定位到从系统启动开始创建的进程数
        printf("从系统启动开始创建的进程数:%d\n",m);
    }
    fclose(in1);
//    fclose(in2);
    fclose(in3);//关闭文件
}

void main(int argc,char *argv[])
{
    char c1,c2;
    if(argc==1)
    {
        func_A();
        return;
    }
    if(argc>1)
    {
        sscanf(argv[1],"%c%c",&c1,&c2);
        if(c1!='-')
        {
            printf("usage: observer [-s] [-l int dur]\n");
            return;
        }
        if(c2=='s')
        {
            func_B();
            return;
        }
            }
}

