//Phase 3: Deadlock Creation


#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>

#define NUM_ACCOUNTS 2
#define DEADLOCK_TIMEOUT_SEC 5

typedef struct {
    int account_id;
    double balance;
    pthread_mutex_t lock;
} Account;

Account accounts[NUM_ACCOUNTS];

/* incremented each time a transfer fully completes; used to detect
 * "no progress" (a decent, simple stand-in for real deadlock detection) */
volatile int completed_transfers = 0;

void transfer(int from_id, int to_id, double amount) {
    printf("Thread %lu: attempting transfer account %d -> account %d\n",
           (unsigned long)pthread_self(), from_id, to_id);

    pthread_mutex_lock(&accounts[from_id].lock);
    printf("Thread %lu: locked account %d\n", (unsigned long)pthread_self(), from_id);

    /* Simulate processing delay - gives the other thread time to grab
     * its first lock too, which is what makes the deadlock reliable */
    usleep(200000); /* 200 ms */

    printf("Thread %lu: waiting for account %d...\n", (unsigned long)pthread_self(), to_id);
    pthread_mutex_lock(&accounts[to_id].lock);

    /* If we get here, no deadlock happened this time */
    accounts[from_id].balance -= amount;
    accounts[to_id].balance += amount;
    completed_transfers++;

    pthread_mutex_unlock(&accounts[to_id].lock);
    pthread_mutex_unlock(&accounts[from_id].lock);

    printf("Thread %lu: transfer complete (%d -> %d)\n",
           (unsigned long)pthread_self(), from_id, to_id);
}

void *thread_a_to_b(void *arg) {
    (void)arg;
    for (int i = 0; i < 5; i++) {
        transfer(0, 1, 50.00); /* lock A first, then B */
    }
    return NULL;
}

void *thread_b_to_a(void *arg) {
    (void)arg;
    for (int i = 0; i < 5; i++) {
        transfer(1, 0, 30.00); /* lock B first, then A -> opposite order! */
    }
    return NULL;
}

int main(void) {
    pthread_t t1, t2;

    for (int i = 0; i < NUM_ACCOUNTS; i++) {
        accounts[i].account_id = i;
        accounts[i].balance = 1000.00;
        pthread_mutex_init(&accounts[i].lock, NULL);
    }

    printf("=== Phase 3: Deadlock Demonstration ===\n");
    printf("Thread 1 will transfer A->B (locks A then B)\n");
    printf("Thread 2 will transfer B->A (locks B then A)\n");
    printf("Watch for the program to stop producing output - that's the deadlock.\n\n");

    pthread_create(&t1, NULL, thread_a_to_b, NULL);
    pthread_create(&t2, NULL, thread_b_to_a, NULL);

    /* Watchdog / timeout detector running in main thread instead of
     * blocking forever on pthread_join */
    time_t start = time(NULL);
    int last_seen_progress = 0;
    while (1) {
        sleep(1);
        int now_progress = completed_transfers;
        long elapsed = (long)(time(NULL) - start);

        printf("[watchdog] %lds elapsed, completed_transfers=%d\n", elapsed, now_progress);

        if (now_progress >= 10) {
            printf("\nAll transfers completed with no deadlock this run - "
                   "timing got lucky, try again.\n");
            break;
        }

        if (now_progress == last_seen_progress && elapsed >= DEADLOCK_TIMEOUT_SEC) {
            printf("\n*** POSSIBLE DEADLOCK DETECTED: no progress for %d seconds ***\n",
                   DEADLOCK_TIMEOUT_SEC);
            printf("*** Thread 1 and Thread 2 are stuck waiting on each other's lock ***\n");
            break;
        }
        last_seen_progress = now_progress;
    }

    printf("\nExiting Phase 3 (stuck threads, if any, are abandoned on process exit).\n");
    /* Intentionally NOT joining t1/t2 here - if they are deadlocked,
     * pthread_join would hang forever. This is expected/discussed in
     * the report as the motivation for Phase 4. */
    return 0;
}
