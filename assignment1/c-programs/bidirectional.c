#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/wait.h>

int main() {
    int pipe1[2];  // parent writes, child reads
    int pipe2[2];  // child writes, parent reads
    pid_t pid;
    char buffer[100];

    // Create both pipes
    if (pipe(pipe1) == -1 || pipe(pipe2) == -1) {
        perror("pipe failed");
        return 1;
    }

    pid = fork();

    if (pid == -1) {
        perror("fork failed");
        return 1;
    }

    if (pid == 0) {
        // CHILD PROCESS
        // Close ends child doesn't use
        close(pipe1[1]);  // child doesn't write to pipe1
        close(pipe2[0]);  // child doesn't read from pipe2

        // Read message from parent
        read(pipe1[0], buffer, sizeof(buffer));
        printf("Child received: %s\n", buffer);

        // Send response back to parent
        char *response = "Hello back from child!";
        write(pipe2[1], response, strlen(response) + 1);

        // Cleanup
        close(pipe1[0]);
        close(pipe2[1]);

    } else {
        // PARENT PROCESS
        // Close ends parent doesn't use
        close(pipe1[0]);  // parent doesn't read from pipe1
        close(pipe2[1]);  // parent doesn't write to pipe2

        // Send message to child
        char *message = "Hello from parent!";
        write(pipe1[1], message, strlen(message) + 1);
        close(pipe1[1]);

        // Wait for child's response
        read(pipe2[0], buffer, sizeof(buffer));
        printf("Parent received: %s\n", buffer);
        close(pipe2[0]);

        wait(NULL);
    }

    return 0;
}
