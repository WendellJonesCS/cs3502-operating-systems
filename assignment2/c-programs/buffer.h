// buffer.h
#ifndef BUFFER_H
#define BUFFER_H

#define BUFFER_SIZE 10
#define SHM_KEY 0x124

typedef struct{
    int value, producer_id;
}item_t;

typedef struct{
    item_t buffer[BUFFER_SIZE];
    int head, tail, count;
}shared_buffer_t;

#endif