#include<stdio.h>
#include<stdlib.h>
#include<signal.h>
#include<unistd.h>
void waiting();
void stop();
int wait_mark;
int main()
{
    int p1;
    while ((p1 = fork()) == -1);
    if (p1>0) //if p1 is parent process
    {
		lockf(1,1,0);
        printf("parent process is %d \n", getpid());
		lockf(1,0,0);
		
        wait_mark=1;
        signal(SIGQUIT, stop);
        waiting();
        kill(p1,16); //send signal 16 to end the process p1
        wait(0); //waiting for the ending of p1
		
		lockf(1,1,0);
        printf("parent process is killed!\n");
		lockf(1,0,0);
		
        exit(0); //quit from the parent process

    }
    else //if p1 is child process
    {
        lockf(1,1,0);
        printf("child process %d is created by the parent %d \n", getpid(), getppid());
		lockf(1,0,0);
		
        signal(SIGQUIT,SIG_IGN);
        wait_mark=1;
        signal(16, stop);
        waiting();
		
        lockf(1,1,0);
        printf("child process %d is killed by parent %d \n", getpid(), getppid());
        lockf(1,0,0);
        exit(0); // p1 quit
    }
    return 0;
}
void waiting( )
{
    while (wait_mark != 0);
}
void stop()
{
    wait_mark=0;
}
