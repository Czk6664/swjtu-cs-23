/*
*/
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <semaphore.h>
#include <pthread.h>

#define msleep(x) usleep(x*1000)   //微秒
#define PRODUCT_SPEED             //生产速度
#define CONSUM_SPEED              //消费速度
#define INIT_NUM                  //仓库原有产品数
#define TOTAL_NUM                //仓库容量

sem_t p_sem,
      c_sem,
      sh_sem;

int num = INIT_NUM;

void product(void) {
    sleep(CONSUM_SPEED);
}

int add_to_lib() {
    num++;
    msleep(500);
    return num;
}

void consum() { 
　sleep(PRODUCT_SPEED);

    }

int remove_from_lib() {
    num--;
    msleep(500);
    return num;
}

void *productor(void *arg) { }

void *consumer(void *arg) { }

int main() {
    pthread_t tid_1, tid_2;
    sem_init(&p_sem, 0, TOTAL_NUM - INIT_NUM);
    sem_init(&c_sem, 0, INIT_NUM);
    sem_init(&sh_sem, 0, 1);

    pthread_create(&tid_1, NULL, productor, NULL);
    pthread_create(&tid_2, NULL, consumer, NULL);

    pthread_join(tid_1, NULL);
    pthread_join(tid_2, NULL);

    return 0;
}
