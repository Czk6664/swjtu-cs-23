#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define random(x) (rand() % x)
#define MULTIPLE 3

typedef struct page_s {
    int n;                      //number
    int v;                      //visit flag
}page;

char *menu[] = {
    "f - FIFO",
    "r - LRU",
    "q - quit",
    NULL
};

int getchoice(char *greet, char *choices[]) {
    int chosen = 0;
    int selected;
    char **option;

    do {
        printf("Choice: %s\n", greet);
        option = choices;
        while(*option) {
            printf("%s\n", *option);
            option++;
        }
        do {
            selected = getchar();
        } while(selected == '\n');
        option = choices;
        while(*option) {
            if(selected == *option[0]) {
                chosen = 1;
                break;
            }
            option++;
        }
        if(!chosen) {
            printf("Incorrect choice, select again\n");
        }
    } while(!chosen);
    return selected;    
}


void buildPageReference(int size, page **reference, page *program) {
    int i;
    int n;
    printf("Page reference : ");
    for(i=0;i<size;i++) {
        n = random(size/MULTIPLE);
        reference[i] = &program[n];
        program[n].n = n;
        program[n].v = 0;
        printf("| %d ", n);
    }
    printf("\n");
}

void print(int n, page *frame, int size) {
    int i;

    printf("no. %d step: ", n);
    for(i=0;i<size;i++) {
        printf("| %d ", frame[i].n);
    }
    printf("\n");
}

int Search(int n, page *list, int size) {
    int i;
    for(i=0;i<size;i++) {
        if(list[i].n == n) return i;
    }
    return -1;
}

int findNext(int n, page **list, int start, int size) {
    int count = size;
    int i;
    for(i=start;i<size;i++) {
        if(list[i]->n == n) break;
        else count++;
    }
    return count;
}

int findLastMax(page *frame, int size) {
    int tmp=0,s,i,j=0;
    for(i=0;i<size;i++) {
        s = frame[i].v;
        if(s > tmp) {
            tmp = s;
            j = i;
        }        
    }
    return j;
}


int findLastMin(page *frame, int size) {
    int tmp=frame[0].v,s,i,j=0;
    //printf("| %d ", tmp);
    for(i=1;i<size;i++) {
        s = frame[i].v;
       // printf("| %d ", s);
        if(s < tmp) {
            tmp = s;
            j = i;
        }
    }
   // printf("\n");
    return j;
}

int fifo(int fsize, page *frame, int rsize, page **pageR) {
    int i, j=0,p=0;
    int f=0;
    for(i=0;i<fsize;i++) frame[i].n = -1;
    for(i=0;i<rsize;i++) {
        if(Search(pageR[i]->n, frame, fsize)!=-1);
        else if(i<fsize || p<fsize) {
            frame[p].n=pageR[i]->n;
            p++;
        }
        else {
            frame[j%fsize].n = pageR[i]->n;
            j++;
            f++;
        }
        print(i, frame, fsize);
    }
    printf("page fault : %d\n", f);
    
}

int lru(int fsize, page *frame, int rsize, page **pageR) {
    int i, j, p=0, q;
    int f=0;
    for(i=0;i<fsize;i++) {
        frame[i].n = -1;
        frame[i].v = 0;
    }
    for(i=0;i<rsize;i++) {
        for(j=0;j<fsize;j++) {
            if(frame[j].n!=-1) frame[j].v++;
        }
        q = Search(pageR[i]->n, frame, fsize);
        if(q!=-1) frame[q].v=0;
        else if(i<fsize || p<fsize) {
            frame[p].n=pageR[i]->n;
            p++;
        }else {
            q = findLastMax(frame, fsize);
            frame[q].n = pageR[i]->n;
            frame[q].v = 0;
            f++;
        }
        print(i, frame, fsize);
   }
   printf("page fault : %d\n", f);
}

int main() {
    int choice = 0;
    int logSize;
    int phySize;
    page *program;
    page **pageR;
    page *frame;
    int prSize;

    srand((int)time(0));
    printf("Enter number of pages in program: ");
    scanf("%d", &logSize);

    printf("Enter number of frames in physical memory: ");
    scanf("%d", &phySize);

    program = (page *)malloc(sizeof(int)*2*logSize);
    frame = (page *)malloc(sizeof(int)*2*phySize);

    prSize = logSize * MULTIPLE;
    pageR = (page **)malloc(sizeof(int*)*prSize);
    buildPageReference(prSize, pageR,program);
    
    do {
        choice = getchoice("Please select an action", menu);
        printf("You have chosen: %c\n", choice);
        switch(choice) {
        case 'f' :
            fifo(phySize, frame, prSize, pageR);
            break;
        case 'r' :
            lru(phySize, frame, prSize, pageR);
            break;
        default: break;
        }
    }while(choice != 'q');
    exit(0);
}
