#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/wait.h>

int main() {
    // Pipe used for communication from parent to child
    int pipe1[2];

    // Pipe used for communication from child to parent
    int pipe2[2];

    // Stores the process ID returned by fork()
    pid_t pid;

    // Buffer used to store messages read from the pipes
    char buffer[100];

    // Create both pipes for two-way communication
    if (pipe(pipe1) == -1 || pipe(pipe2) == -1) {
        perror("pipe failed");
        return 1;
    }

    // Create a child process
    pid = fork();

    if (pid == -1) {
        perror("fork failed");
        return 1;
    }

    if (pid == 0) {
        // CHILD PROCESS

        // Close pipe ends that the child does not use
        close(pipe1[1]);  // child only reads from pipe1
        close(pipe2[0]);  // child only writes to pipe2

        // Read the message sent by the parent
        read(pipe1[0], buffer, sizeof(buffer));
        printf("Child received: %s\n", buffer);

        // Create a response message to send back to the parent
        char *response = "Hello back from child!";

        // Send the response through pipe2
        write(pipe2[1], response, strlen(response) + 1);

        // Close remaining pipe ends before exiting
        close(pipe1[0]);
        close(pipe2[1]);

    } else {
        // PARENT PROCESS

        // Close pipe ends that the parent does not use
        close(pipe1[0]);  // parent only writes to pipe1
        close(pipe2[1]);  // parent only reads from pipe2

        // Message that will be sent to the child
        char *message = "Hello from parent!";

        // Send the message through pipe1
        write(pipe1[1], message, strlen(message) + 1);

        // Close write end after sending data
        close(pipe1[1]);

        // Read the child's response from pipe2
        read(pipe2[0], buffer, sizeof(buffer));
        printf("Parent received: %s\n", buffer);

        // Close the read end when finished
        close(pipe2[0]);

        // Wait for the child process to finish
        wait(NULL);
    }

    return 0;
}

