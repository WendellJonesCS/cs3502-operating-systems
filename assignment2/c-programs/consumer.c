#include <stdio.h>
#include <stdlib.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <semaphore.h>
#include <fcntl.h>
#include <unistd.h>
#include "buffer.h"

// semaphore names
#define SEM_MUTEX "/sem_mutex"
#define SEM_EMPTY "/sem_empty"
#define SEM_FULL  "/sem_full"

int main(int argc, char *argv[]) {

    // parse cli args
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <id> <num_items>\n", argv[0]);
        exit(1);
    }
    int consumer_id = atoi(argv[1]);
    int num_items   = atoi(argv[2]);

    // attach to existing shared memory
    int shm_id = -1;
    while (shm_id == -1) {
        shm_id = shmget(SHM_KEY, sizeof(shared_buffer_t), 0666);
        if (shm_id == -1) usleep(1000); // wait 1ms and retry
    }

    shared_buffer_t *shm = (shared_buffer_t *)shmat(shm_id, NULL, 0);
    if (shm == (void *)-1) {
        perror("shmat");
        exit(1);
    }

    // open three named semaphores
    sem_t *sem_empty = sem_open(SEM_EMPTY, O_CREAT, 0644, BUFFER_SIZE);
    sem_t *sem_full  = sem_open(SEM_FULL,  O_CREAT, 0644, 0);
    sem_t *sem_mutex = sem_open(SEM_MUTEX, O_CREAT, 0644, 1);

    if (sem_empty == SEM_FAILED || sem_full == SEM_FAILED || sem_mutex == SEM_FAILED) {
        perror("sem_open");
        shmdt(shm);
        exit(1);
    }

    // consume num_items items
    for (int i = 0; i < num_items; i++) {

        // wait for available item
        sem_wait(sem_full);

        // lock buffer 
        sem_wait(sem_mutex);

        // read item from  tail position
        item_t item = shm->buffer[shm->tail];

        // move tail circularly, update count
        shm->tail = (shm->tail + 1) % BUFFER_SIZE;
        shm->count--;

        printf("Consumer %d: Consumed value %d from Producer %d\n",
               consumer_id, item.value, item.producer_id);
        fflush(stdout);

        // unlock  buffer
        sem_post(sem_mutex);

        // signal when one more slot is now free
        sem_post(sem_empty);
    }

    // detach shared memory
    shmdt(shm);

    // final cleanup, delete shared memory and semaphores 
    shmctl(shm_id, IPC_RMID, NULL);

    sem_close(sem_empty);
    sem_close(sem_full);
    sem_close(sem_mutex);

    sem_unlink(SEM_EMPTY);
    sem_unlink(SEM_FULL);
    sem_unlink(SEM_MUTEX);

    return 0;
}