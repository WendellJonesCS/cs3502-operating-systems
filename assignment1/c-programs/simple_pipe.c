#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/wait.h>

int main() {
    int pipefd[2];
    pid_t pid;
    char buffer[100];
    char *message = "Hello from parent!";

    // Create the pipe
    if (pipe(pipefd) == -1) {
        perror("pipe failed");
        return 1;
    }

    // Fork the process
    pid = fork();

    if (pid == -1) {
        perror("fork failed");
        return 1;
    }

    if (pid == 0) {
        // CHILD PROCESS
        close(pipefd[1]);
        read(pipefd[0], buffer, sizeof(buffer));
        printf("Child received: %s\n", buffer);
        close(pipefd[0]);

    } else {
        // PARENT PROCESS
        close(pipefd[0]);
        write(pipefd[1], message, strlen(message) + 1);
        close(pipefd[1]);
        wait(NULL);
    }

    return 0;
}
