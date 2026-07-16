/*
 * CS 3502 - Project 1: Multi-Threaded Banking System
 * Phase 2: Resource Protection (pthread mutex)
 *
 * Same setup as Phase 1, but now the shared account has its own
 * pthread_mutex_t. Every read-modify-write of account.balance happens
 * inside lock/unlock, so only one thread can touch it at a time.
 * This should produce the mathematically correct final balance every
 * single time, no matter how many threads or transactions we use.
 *
 * We also time the run so we can compare Phase 1 (unsafe/fast) vs
 * Phase 2 (safe/slower due to lock contention) in the report.
 */

#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <string.h>
#include <errno.h>

#define NUM_THREADS 5
#define TRANSACTIONS_PER_THREAD 1000
#define INITIAL_BALANCE 1000.00
#define DEPOSIT_AMOUNT 10.00

typedef struct {
    int account_id;
    double balance;
    int transaction_count;
    pthread_mutex_t lock;   /* protects balance + transaction_count */
} Account;

Account account;

void deposit(double amount) {
    if (pthread_mutex_lock(&account.lock) != 0) {
        perror("Failed to acquire lock");
        return;
    }

    /* ---- Critical section: only one thread executes this at a time ---- */
    double current = account.balance;
    usleep(1); /* keep the same artificial delay as Phase 1 so the ONLY */
               /* difference between the two programs is the locking     */
    account.balance = current + amount;
    account.transaction_count++;
    /* --------------------------------------------------------------- */

    pthread_mutex_unlock(&account.lock);
}

void *teller_thread(void *arg) {
    int teller_id = *(int *)arg;

    for (int i = 0; i < TRANSACTIONS_PER_THREAD; i++) {
        deposit(DEPOSIT_AMOUNT);
    }

    printf("Teller %d: finished %d transactions\n", teller_id, TRANSACTIONS_PER_THREAD);
    return NULL;
}

int main(void) {
    pthread_t threads[NUM_THREADS];
    int thread_ids[NUM_THREADS];
    struct timespec start, end;

    account.account_id = 1;
    account.balance = INITIAL_BALANCE;
    account.transaction_count = 0;
    pthread_mutex_init(&account.lock, NULL);

    double expected_final = INITIAL_BALANCE +
        (double)(NUM_THREADS * TRANSACTIONS_PER_THREAD) * DEPOSIT_AMOUNT;

    printf("=== Phase 2: Mutex-Protected Deposits ===\n");
    printf("Initial balance: %.2f\n", account.balance);
    printf("Spawning %d threads, %d deposits of %.2f each\n\n",
           NUM_THREADS, TRANSACTIONS_PER_THREAD, DEPOSIT_AMOUNT);

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int i = 0; i < NUM_THREADS; i++) {
        thread_ids[i] = i;
        if (pthread_create(&threads[i], NULL, teller_thread, &thread_ids[i]) != 0) {
            perror("pthread_create failed");
            exit(1);
        }
    }

    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    clock_gettime(CLOCK_MONOTONIC, &end);
    double elapsed = (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;

    printf("\n=== Results ===\n");
    printf("Expected final balance : %.2f\n", expected_final);
    printf("Actual final balance   : %.2f\n", account.balance);
    printf("Expected transaction_count: %d, actual: %d\n",
           NUM_THREADS * TRANSACTIONS_PER_THREAD, account.transaction_count);
    printf("Elapsed time: %.4f seconds\n", elapsed);

    if (account.balance == expected_final) {
        printf("\n>>> CORRECT: mutex eliminated the race condition <<<\n");
    } else {
        printf("\n>>> UNEXPECTED MISMATCH - check locking logic <<<\n");
    }

    pthread_mutex_destroy(&account.lock);
    return 0;
}
