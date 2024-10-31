#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netdb.h>

#define BUFFER_SIZE 4096

void send_post(int sockfd, const char *host, const char *username, const char *message);
void send_get(int sockfd, const char *host, const char *username, const char *message);
void setup_connection(const char *host, const char *port, int *sockfd);

int main(int argc, char *argv[]) {
    if (argc != 5) {
        fprintf(stderr, "Usage: %s [host] [port] [username] [message]\n", argv[0]);
        return EXIT_FAILURE;
    }

    const char *host = argv[1];
    const char *port = argv[2];
    const char *username = argv[3];
    const char *message = argv[4];
    int sockfd;

    setup_connection(host, port, &sockfd);

    send_post(sockfd, host, username, message);

    // Close and reconnect for GET request to check the message
    close(sockfd);
    setup_connection(host, port, &sockfd);
    send_get(sockfd, host, username, message);

    close(sockfd);
    return EXIT_SUCCESS;
}

void setup_connection(const char *host, const char *port, int *sockfd) {
    struct addrinfo hints, *res;
    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;

    if (getaddrinfo(host, port, &hints, &res) != 0) {
        perror("getaddrinfo failed");
        exit(EXIT_FAILURE);
    }

    *sockfd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (*sockfd == -1) {
        perror("Socket creation failed");
        exit(EXIT_FAILURE);
    }

    if (connect(*sockfd, res->ai_addr, res->ai_addrlen) == -1) {
        perror("Connection failed");
        close(*sockfd);
        exit(EXIT_FAILURE);
    }
    freeaddrinfo(res);
}

void send_post(int sockfd, const char *host, const char *username, const char *message) {
    char request[BUFFER_SIZE];
    snprintf(request, sizeof(request),
             "POST /api/messages HTTP/1.1\r\n"
             "Host: %s\r\n"
             "Content-Type: application/json\r\n"
             "Cookie: nickname=%s\r\n"
             "Content-Length: %zu\r\n\r\n"
             "{\"message\": \"%s\"}",
             host, username, strlen(message) + 13, message);

    send(sockfd, request, strlen(request), 0);

    char response[BUFFER_SIZE];
    recv(sockfd, response, sizeof(response) - 1, 0);
    printf("POST response:\n%s\n", response);
}

void send_get(int sockfd, const char *host, const char *username, const char *message) {
    char request[BUFFER_SIZE];
    snprintf(request, sizeof(request),
             "GET /api/messages HTTP/1.1\r\n"
             "Host: %s\r\n"
             "Cookie: nickname=%s\r\n\r\n",
             host, username);

    send(sockfd, request, strlen(request), 0);

    char response[BUFFER_SIZE];
    recv(sockfd, response, sizeof(response) - 1, 0);
    printf("GET response:\n%s\n", response);

    // Assert that message is in the response
    assert(strstr(response, message) != NULL);
}


