CS 3502 - Project 1: Multi-Threaded Banking System
Wendell Jones


OVERVIEW

This project implements a four-phase multi-threaded banking simulation
in C using POSIX threads (pthreads), demonstrating race conditions,
mutex-based synchronization, deadlock creation, and deadlock resolution.

FILES

phase1.c - Multiple threads deposit into ONE shared, unprotected account.
           No locking is used, so concurrent read-modify-write operations
           overwrite each other and money is silently "lost." Running the
           program multiple times produces a different (wrong) final
           balance each time, demonstrating a classic race condition.

phase2.c - Same scenario as Phase 1, but the account now has its own
           pthread_mutex_t. Every deposit locks the mutex, updates the
           balance, then unlocks. The final balance is now correct on
           every run. Elapsed time is printed to show the (small) cost
           of synchronization.

phase3.c - Two accounts (A and B). Thread 1 repeatedly transfers A->B
           (locks A, then B). Thread 2 repeatedly transfers B->A (locks
           B, then A). Because the two threads acquire locks in opposite
           order, they deadlock: Thread 1 holds A and waits for B while
           Thread 2 holds B and waits for A. A watchdog loop in main()
           prints progress every second and reports "POSSIBLE DEADLOCK
           DETECTED" after 5 seconds with no completed transfers.

phase4.c - Same A/B transfer scenario as Phase 3, but safe_transfer()
           always locks the LOWER-numbered account first, no matter
           which direction money is moving. This consistent lock
           ordering removes the circular-wait condition required for
           deadlock (one of the four Coffman conditions), so the
           program always completes, and the final balances are
           verified to be mathematically correct and money-conserving.

HOW TO BUILD

gcc -Wall -pthread phase1.c -o phase1
gcc -Wall -pthread phase2.c -o phase2
gcc -Wall -pthread phase3.c -o phase3
gcc -Wall -pthread phase4.c -o phase4

HOW TO RUN

./phase1     (run 2-3 times back to back - balance differs each time)
./phase2     (run 2-3 times - balance is always correct)
./phase3     (will hang, then self-report deadlock after ~5 seconds;
              Ctrl+C to exit if it doesn't self-terminate)
./phase4     (always completes cleanly, balances verified correct)

DEADLOCK RESOLUTION STRATEGY CHOSEN
Lock Ordering. All transfer operations acquire the lower account_id's
mutex first and the higher account_id's mutex second, regardless of
transfer direction. This guarantees every thread requests locks in the
same global order, which makes circular wait impossible.

CHALLENGES ENCOUNTERED

- Phase 1 needed an artificial usleep(1) inside the critical section to
  make the race condition show up reliably on every run; without a
  delay, some runs could get lucky and appear correct even without
  locking.
- Phase 3's deadlock had to be made reliable rather than "possible" -
  adding a usleep(200000) between acquiring the first and second lock
  gives the other thread a wide enough window to also grab its first
  lock, guaranteeing deadlock instead of just risking it.
- Phase 3 intentionally does not join the two transfer threads, since
  pthread_join would hang forever on a truly deadlocked thread - the
  watchdog loop in main() is a simple, from-scratch stand-in for a
  deadlock detection algorithm.

ENVIRONMENT

Developed and tested on Ubuntu (WSL2), gcc, pthreads.

REPOSITORY
https://github.com/WendellJonesCS/cs3502-operating-systems
(this project lives under cs3502/assignment3)
