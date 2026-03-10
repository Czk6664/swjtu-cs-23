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
    pid_t pid_child, pid_grandchild;

    // 创建子进程
    while ((pid_child = fork()) == -1);

    if (pid_child > 0) {
        // 父进程逻辑
        lockf(1, 1, 0);
        printf("Parent process (PID: %d) created child (PID: %d)\n", getpid(), pid_child);
        lockf(1, 0, 0);

        wait_mark = 1;
        signal(SIGQUIT, stop);
        waiting();

        kill(pid_child, SIGUSR1);
        waitpid(pid_child, NULL, 0);

        lockf(1, 1, 0);
        printf("Parent process (PID: %d) exiting\n", getpid());
        lockf(1, 0, 0);

        exit(EXIT_SUCCESS);
    } else {
        // 子进程逻辑
        lockf(1, 1, 0);
        printf("Child process (PID: %d) created by parent (PID: %d)\n", getpid(), getppid());
        lockf(1, 0, 0);

        // 创建孙进程
        while ((pid_grandchild = fork()) == -1);

        if (pid_grandchild > 0) {
            // 子进程继续执行
            wait_mark = 1;
            signal(SIGQUIT, SIG_IGN);
            signal(SIGUSR1, stop);
            waiting();

            kill(pid_grandchild, SIGUSR1);
            waitpid(pid_grandchild, NULL, 0);

            lockf(1, 1, 0);
            printf("Child process (PID: %d) exiting\n", getpid());
            lockf(1, 0, 0);

            exit(EXIT_SUCCESS);
        } else {
            // 孙进程逻辑
            lockf(1, 1, 0);
            printf("Grandchild process (PID: %d) created by child (PID: %d)\n", getpid(), getppid());
            lockf(1, 0, 0);

            wait_mark = 1;
            signal(SIGQUIT, SIG_IGN);
            signal(SIGUSR1, stop);
            waiting();

            lockf(1, 1, 0);
            printf("Grandchild process (PID: %d) exiting\n", getpid());
            lockf(1, 0, 0);

            exit(EXIT_SUCCESS);
        }
    }

    return 0;
}

void waiting() {
    while (wait_mark != 0);
}

void stop() {
    wait_mark = 0;
}    