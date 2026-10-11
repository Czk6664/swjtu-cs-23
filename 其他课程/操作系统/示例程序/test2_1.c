#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>

void waiting();
void stop();
int wait_mark;

int main() {
    int p1, p2;
    // 创建第一个子进程
    while ((p1 = fork()) == -1);

    if (p1 > 0) {
        // 父进程继续创建第二个子进程
        while ((p2 = fork()) == -1);

        if (p2 > 0) {
            // 父进程
            lockf(1, 1, 0);
            printf("parent process is %d \n", getpid());
            lockf(1, 0, 0);

            wait_mark = 1;
            signal(SIGQUIT, stop);
            waiting();

            kill(p1, SIGUSR1);
            kill(p2, SIGUSR1);

            waitpid(p1, NULL, 0);
            waitpid(p2, NULL, 0);

            lockf(1, 1, 0);
            printf("parent process is killed!\n");
            lockf(1, 0, 0);

            exit(0);
        } else {
            // 第二个子进程
            lockf(1, 1, 0);
            printf("second child process %d is created by the parent %d \n", getpid(), getppid());
            lockf(1, 0, 0);

            signal(SIGQUIT, SIG_IGN);
            wait_mark = 1;
            signal(SIGUSR1, stop);
            waiting();

            lockf(1, 1, 0);
            printf("second child process %d is killed by parent %d \n", getpid(), getppid());
            lockf(1, 0, 0);

            exit(0);
        }
    } else {
        // 第一个子进程
        lockf(1, 1, 0);
        printf("first child process %d is created by the parent %d \n", getpid(), getppid());
        lockf(1, 0, 0);

        signal(SIGQUIT, SIG_IGN);
        wait_mark = 1;
        signal(SIGUSR1, stop);
        waiting();

        lockf(1, 1, 0);
        printf("first child process %d is killed by parent %d \n", getpid(), getppid());
        lockf(1, 0, 0);

        exit(0);
    }

    return 0;
}

void waiting() {
    while (wait_mark != 0);
}

void stop() {
    wait_mark = 0;
}    