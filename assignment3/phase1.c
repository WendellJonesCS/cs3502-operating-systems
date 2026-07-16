/*
 * CS 3502 - Project 1: Multi-Threaded Banking System
 * Phase 1: Basic Threads (NO synchronization)
 *
 * Goal: show that when multiple threads read-modify-write the same
 * shared variable without any protection, the final result is WRONG
 * and inconsistent from run to run. This is a race condition.
 *
 * There is ONE shared account balance. NUM_THREADS threads each perform
 * TRANSACTIONS_PER_THREAD deposits of DEPOSIT_AMOUNT. If everything went
 * perfectly the final balance would be:
 *     INITIAL_BALANCE + NUM_THREADS * TRANSACTIONS_PER_THREAD * DEPOSIT_AMOUNT
 * Because there is no locking, some deposits get "lost" when two threads
 * read the same old balance before either one writes the new balance back.
 */
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define NUM_THREADS 5
#define TRANSACTIONS_PER_THREAD 1000
#define INITIAL_BALANCE 1000.00
#define DEPOSIT_AMOUNT 10.00

/* Shared, UNPROTECTED resource */
typedef struct {
    int account_id;
    double balance;
    int transaction_count;
} Account;

Account account; /* single shared account, on purpose, to make the race obvious */

void *teller_thread(void *arg) {
    int teller_id = *(int *)arg;

    for (int i = 0; i < TRANSACTIONS_PER_THREAD; i++) {
        /* ---- THIS IS THE RACE CONDITION ---- */
        double current = account.balance;   /* 1. read shared value      */
        usleep(1);                          /* 2. force a context switch  */
                                             /*    window so the race is   */
                                             /*    reliably visible        */
        current = current + DEPOSIT_AMOUNT; /* 3. modify local copy       */
        account.balance = current;          /* 4. write shared value back */
        account.transaction_count++;        /* also unprotected           */
        /* -------------------------------------- */
    }

    printf("Teller %d: finished %d transactions\n", teller_id, TRANSACTIONS_PER_THREAD);
    return NULL;
}

int main(void) {
    pthread_t threads[NUM_THREADS];
    int thread_ids[NUM_THREADS];

    account.account_id = 1;
    account.balance = INITIAL_BALANCE;
    account.transaction_count = 0;

    double expected_final = INITIAL_BALANCE +
        (double)(NUM_THREADS * TRANSACTIONS_PER_THREAD) * DEPOSIT_AMOUNT;

    printf("=== Phase 1: Race Condition Demo ===\n");
    printf("Initial balance: %.2f\n", account.balance);
    printf("Spawning %d threads, %d deposits of %.2f each\n\n",
           NUM_THREADS, TRANSACTIONS_PER_THREAD, DEPOSIT_AMOUNT);

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

    printf("\n=== Results ===\n");
    printf("Expected final balance : %.2f\n", expected_final);
    printf("Actual final balance   : %.2f\n", account.balance);
    printf("Difference (lost money): %.2f\n", expected_final - account.balance);
    printf("Expected transaction_count: %d, actual: %d\n",
           NUM_THREADS * TRANSACTIONS_PER_THREAD, account.transaction_count);

    if (account.balance != expected_final) {
        printf("\n>>> RACE CONDITION CONFIRMED: actual != expected <<<\n");
    } else {
        printf("\n>>> No race observed this run - try increasing TRANSACTIONS_PER_THREAD or run again <<<\n");
    }

    return 0;
}
