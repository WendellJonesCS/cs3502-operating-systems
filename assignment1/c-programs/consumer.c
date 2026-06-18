#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <signal.h>

// Flag used to tell the program when it should stop running
volatile sig_atomic_t shutdown_flag = 0;

// Keeps track of the total number of bytes sent to stdout
long bytes_sent = 0;

// Signal handler for Ctrl+C (SIGINT)
void handle_sigint(int sig) {
    shutdown_flag = 1;
}

// Signal handler that prints the current progress when SIGUSR1 is received
void handle_sigusr1(int sig) {
    fprintf(stderr, "\n[Producer] Bytes sent so far: %ld\n", bytes_sent);
}

int main(int argc, char *argv[]) {
    // Stores the name of the input file if one is provided
    char *filename = NULL;

    // Default buffer size used for reading data
    int buffer_size = 4096;

    // Variable used by getopt when processing command-line options
    int opt;

    FILE *input;

    // Dynamically allocated buffer for reading file data
    char *buffer;

    // Stores how many bytes were read during each fread call
    size_t bytes_read;

    // Structures used to configure signal handling
    struct sigaction sa_int, sa_usr1;

    // Register handler for SIGINT (Ctrl+C)
    sa_int.sa_handler = handle_sigint;
    sigemptyset(&sa_int.sa_mask);
    sa_int.sa_flags = 0;
    sigaction(SIGINT, &sa_int, NULL);

    // Register handler for SIGUSR1
    sa_usr1.sa_handler = handle_sigusr1;
    sigemptyset(&sa_usr1.sa_mask);
    sa_usr1.sa_flags = 0;
    sigaction(SIGUSR1, &sa_usr1, NULL);

    // Parse command-line flags:
    // -f specifies input file
    // -b specifies buffer size
    while ((opt = getopt(argc, argv, "f:b:")) != -1) {
        switch (opt) {
            case 'f':
                filename = optarg;
                break;

            case 'b':
                // Convert buffer size argument from string to integer
                buffer_size = atoi(optarg);
                break;

            default:
                fprintf(stderr, "Usage: %s [-f file] [-b size]\n", argv[0]);
                exit(1);
        }
    }

    // Open the specified file, otherwise read from standard input
    if (filename != NULL) {
        input = fopen(filename, "r");

        if (input == NULL) {
            perror("Error opening file");
            return 1;
        }
    } else {
        input = stdin;
    }

    // Allocate memory for the read buffer
    buffer = malloc(buffer_size);

    if (buffer == NULL) {
        perror("malloc failed");
        return 1;
    }

    // Continuously read chunks of data and write them to stdout
    // The loop stops if EOF is reached or SIGINT is received
    while (!shutdown_flag &&
           (bytes_read = fread(buffer, 1, buffer_size, input)) > 0) {

        // Write the bytes that were read to standard output
        fwrite(buffer, 1, bytes_read, stdout);

        // Update running total of bytes processed
        bytes_sent += bytes_read;
    }

    // Display a shutdown message if the program was interrupted
    if (shutdown_flag) {
        fprintf(stderr,
                "\n[Producer] Shutting down. Total bytes sent: %ld\n",
                bytes_sent);
    }

    // Free dynamically allocated memory
    free(buffer);

    // Close the file only if one was opened
    if (filename != NULL) {
        fclose(input);
    }

    return 0;
}

