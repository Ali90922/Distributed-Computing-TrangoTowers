#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netdb.h>

#define BUFFER_SIZE 4096

void setup_connection(const char *host, const char *port, int *sockfd);
void send_post(int sockfd, const char *host, const char *username, const char *message);
void send_get(int sockfd, const char *host, const char *username, const char *message);
void assert_response_code(const char *response, const char *expected_code);

int main(int argc, char *argv[])
{
    if (argc != 5)
    {
        fprintf(stderr, "Usage: %s [host] [port] [username] [message]\n", argv[0]);
        return EXIT_FAILURE;
    }

    const char *host = argv[1];
    const char *port = argv[2];
    const char *username = argv[3];
    const char *message = argv[4];
    int sockfd;

    setup_connection(host, port, &sockfd);

    // Step 1: Initial GET to ensure message isn’t already present
    send_get(sockfd, host, username, message);

    close(sockfd);
    setup_connection(host, port, &sockfd);

    // Step 2: POST a new message
    send_post(sockfd, host, username, message);

    close(sockfd);
    setup_connection(host, port, &sockfd);

    // Step 3: Confirm message is present with a second GET
    send_get(sockfd, host, username, message);

    // Testing without login
    close(sockfd);
    setup_connection(host, port, &sockfd);
    printf("\nTesting GET without cookie:\n");
    send_get(sockfd, host, NULL, message);

    close(sockfd);
    setup_connection(host, port, &sockfd);
    printf("\nTesting POST without cookie:\n");
    send_post(sockfd, host, NULL, message);

    close(sockfd);
    return EXIT_SUCCESS;
}

void setup_connection(const char *host, const char *port, int *sockfd)
{
    struct addrinfo hints, *res;
    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;

    if (getaddrinfo(host, port, &hints, &res) != 0)
    {
        perror("getaddrinfo failed");
        exit(EXIT_FAILURE);
    }

    *sockfd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (*sockfd == -1)
    {
        perror("Socket creation failed");
        exit(EXIT_FAILURE);
    }

    if (connect(*sockfd, res->ai_addr, res->ai_addrlen) == -1)
    {
        perror("Connection failed");
        close(*sockfd);
        exit(EXIT_FAILURE);
    }
    freeaddrinfo(res);
}

void send_post(int sockfd, const char *host, const char *username, const char *message)
{
    char request[BUFFER_SIZE];

    if (username) {
        snprintf(request, sizeof(request),
                 "POST /api/messages HTTP/1.1\r\n"
                 "Host: %s\r\n"
                 "Content-Type: application/json\r\n"
                 "Cookie: nickname=%s\r\n"
                 "Content-Length: %zu\r\n\r\n"
                 "{\"message\": \"%s\"}",
                 host, username, strlen(message) + 13, message);
    } else {
        snprintf(request, sizeof(request),
                 "POST /api/messages HTTP/1.1\r\n"
                 "Host: %s\r\n"
                 "Content-Type: application/json\r\n"
                 "Content-Length: %zu\r\n\r\n"
                 "{\"message\": \"%s\"}",
                 host, strlen(message) + 13, message);
    }

    send(sockfd, request, strlen(request), 0);

    char response[BUFFER_SIZE];
    recv(sockfd, response, sizeof(response) - 1, 0);
    printf("POST response:\n%s\n", response);

    if (username) {
        assert_response_code(response, "201 Created");
    } else {
        assert_response_code(response, "403 Forbidden");
    }
}

void send_get(int sockfd, const char *host, const char *username, const char *message)
{
    char request[BUFFER_SIZE];

    if (username) {
        snprintf(request, sizeof(request),
                 "GET /api/messages HTTP/1.1\r\n"
                 "Host: %s\r\n"
                 "Cookie: nickname=%s\r\n\r\n",
                 host, username);
    } else {
        snprintf(request, sizeof(request),
                 "GET /api/messages HTTP/1.1\r\n"
                 "Host: %s\r\n\r\n",
                 host);
    }

    send(sockfd, request, strlen(request), 0);

    char response[BUFFER_SIZE];
    recv(sockfd, response, sizeof(response) - 1, 0);
    printf("GET response:\n%s\n", response);

    if (username) {
        assert_response_code(response, "200 OK");
        assert(strstr(response, message) != NULL);
    } else {
        assert_response_code(response, "403 Forbidden");
    }
}

void assert_response_code(const char *response, const char *expected_code)
{
    char expected_response[BUFFER_SIZE];
    snprintf(expected_response, sizeof(expected_response), "HTTP/1.1 %s", expected_code);
    assert(strstr(response, expected_response) != NULL);
}
