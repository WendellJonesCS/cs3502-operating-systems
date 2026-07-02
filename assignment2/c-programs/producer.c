#include <stdio.h>
#include <stdlib.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <semaphore.h>
#include <fcntl.h>
#include <errno.h>
#include "buffer.h"

#define SEM_MUTEX "/sem_mutex"
#define SEM_EMPTY "/sem_empty"
#define SEM_FULL  "/sem_full"

int main(int argc, char *argv[]) {

    if (argc != 3) {
        fprintf(stderr, "Usage: %s <id> <num_items>\n", argv[0]);
        exit(1);
    }
    int producer_id = atoi(argv[1]);
    int num_items   = atoi(argv[2]);

   
    int created = 1;
    int shm_id = shmget(SHM_KEY, sizeof(shared_buffer_t), IPC_CREAT | IPC_EXCL | 0666);

    if (shm_id == -1) {
        if (errno == EEXIST) {
            // if segment already exists get the ID without IPC_EXCL
            created = 0;
            shm_id = shmget(SHM_KEY, sizeof(shared_buffer_t), 0666);
            if (shm_id == -1) {
                perror("shmget (attach existing)");
                exit(1);
            }
        } else {
            perror("shmget (create)");
            exit(1);
        }
    }

    // attach segment to this process's address in memory.
    shared_buffer_t *shm = (shared_buffer_t *)shmat(shm_id, NULL, 0);
    if (shm == (void *)-1) {
        perror("shmat");
        exit(1);
    }

    if (created) {
        shm->head  = 0;
        shm->tail  = 0;
        shm->count = 0;
    }


    sem_t *sem_empty = sem_open(SEM_EMPTY, O_CREAT, 0644, BUFFER_SIZE);
    sem_t *sem_full  = sem_open(SEM_FULL,  O_CREAT, 0644, 0);
    sem_t *sem_mutex = sem_open(SEM_MUTEX, O_CREAT, 0644, 1);

    if (sem_empty == SEM_FAILED || sem_full == SEM_FAILED || sem_mutex == SEM_FAILED) {
        perror("sem_open");
        shmdt(shm);
        exit(1);
    }

    // displays which producer made each item in the output.
    for (int i = 0; i < num_items; i++) {
        int value = producer_id * 1000 + i;

        // wait for a open slot
        sem_wait(sem_empty);

        // lock  buffer so only one process can write at a time
        sem_wait(sem_mutex);

        //w rite the item into the next available index
        shm->buffer[shm->head].value       = value;
        shm->buffer[shm->head].producer_id = producer_id;

        // move head circularly
        shm->head = (shm->head + 1) % BUFFER_SIZE;
        shm->count++;

        printf("Producer %d: Produced value %d\n", producer_id, value);
        fflush(stdout);

        // unlock  buffer
        sem_post(sem_mutex);

        //signal one more item is available
        sem_post(sem_full);
    }

    
    shmdt(shm);

   
    sem_close(sem_empty);
    sem_close(sem_full);
    sem_close(sem_mutex);

    return 0;
}