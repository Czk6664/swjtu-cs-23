#include <sys/syscall.h>
#include <linux/unistd.h>
#include <stdio.h>
#include <sys/time.h>
#include <time.h>
main()
{
    struct timeval tv;
    long tmp;
    tmp=syscall(337,&tv);
    if(tmp!=-1)
    {
        printf("First, user get tv_sec:%d\n",(int)tv.tv_sec);
    }
    sleep(10);
    tmp=syscall(337,&tv);
    if(tmp!=-1)
    {
        printf("Second, user get tv_sec:%d\n",(int)tv.tv_sec);
    }
}
