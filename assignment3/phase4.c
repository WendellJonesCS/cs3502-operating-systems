
 //Phase 4: Deadlock Resolution (Lock Ordering strategy)

#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>

#define NUM_ACCOUNTS 2
#define TRANSFERS_PER_THREAD 2000

typedef struct {
    int account_id;
    double balance;
    pthread_mutex_t lock;
} Account;

Account accounts[NUM_ACCOUNTS];

void safe_transfer(int from_id, int to_id, double amount) {
    /* Always lock the lower-numbered account first - this consistent
     * global ordering is what prevents circular wait. */
    int first  = (from_id < to_id) ? from_id : to_id;
    int second = (from_id < to_id) ? to_id   : from_id;

    pthread_mutex_lock(&accounts[first].lock);
    pthread_mutex_lock(&accounts[second].lock);

    accounts[from_id].balance -= amount;
    accounts[to_id].balance   += amount;

    pthread_mutex_unlock(&accounts[second].lock);
    pthread_mutex_unlock(&accounts[first].lock);
}

void *thread_a_to_b(void *arg) {
    (void)arg;
    for (int i = 0; i < TRANSFERS_PER_THREAD; i++) {
        safe_transfer(0, 1, 5.00);
    }
    return NULL;
}

void *thread_b_to_a(void *arg) {
    (void)arg;
    for (int i = 0; i < TRANSFERS_PER_THREAD; i++) {
        safe_transfer(1, 0, 3.00);
    }
    return NULL;
}

int main(void) {
    pthread_t t1, t2;
    struct timespec start, end;

    for (int i = 0; i < NUM_ACCOUNTS; i++) {
        accounts[i].account_id = i;
        accounts[i].balance = 1000.00;
        pthread_mutex_init(&accounts[i].lock, NULL);
    }

    double total_before = accounts[0].balance + accounts[1].balance;

    printf("=== Phase 4: Deadlock Resolution (Lock Ordering) ===\n");
    printf("Starting balances: A=%.2f  B=%.2f\n", accounts[0].balance, accounts[1].balance);
    printf("Thread 1: %d transfers A->B of 5.00\n", TRANSFERS_PER_THREAD);
    printf("Thread 2: %d transfers B->A of 3.00\n\n", TRANSFERS_PER_THREAD);

    clock_gettime(CLOCK_MONOTONIC, &start);

    pthread_create(&t1, NULL, thread_a_to_b, NULL);
    pthread_create(&t2, NULL, thread_b_to_a, NULL);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);

    clock_gettime(CLOCK_MONOTONIC, &end);
    double elapsed = (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;

    double total_after = accounts[0].balance + accounts[1].balance;
    double expected_a = 1000.00 - (double)TRANSFERS_PER_THREAD * 5.00 + (double)TRANSFERS_PER_THREAD * 3.00;
    double expected_b = 1000.00 + (double)TRANSFERS_PER_THREAD * 5.00 - (double)TRANSFERS_PER_THREAD * 3.00;

    printf("\n=== Results ===\n");
    printf("No deadlock occurred - both threads completed all transfers.\n");
    printf("Final balance A: %.2f (expected %.2f)\n", accounts[0].balance, expected_a);
    printf("Final balance B: %.2f (expected %.2f)\n", accounts[1].balance, expected_b);
    printf("Total money before: %.2f, after: %.2f (should match - money is conserved)\n",
           total_before, total_after);
    printf("Elapsed time: %.4f seconds\n", elapsed);

    for (int i = 0; i < NUM_ACCOUNTS; i++) {
        pthread_mutex_destroy(&accounts[i].lock);
    }

    return 0;
}
