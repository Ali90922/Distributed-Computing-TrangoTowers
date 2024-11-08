#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netdb.h>

#define BUFFER_SIZE 4096 // Define a constant for the buffer size used in requests and responses

// Function declarations for POST, GET requests, and setting up the connection
void send_post(int sockfd, const char *host, const char *username, const char *message);
void send_get(int sockfd, const char *host, const char *username, const char *message);
void setup_connection(const char *host, const char *port, int *sockfd);

int main(int argc, char *argv[])
{
    // Check for correct number of command-line arguments
    if (argc != 5)
    {
        fprintf(stderr, "Usage: %s [host] [port] [username] [message]\n", argv[0]);
        return EXIT_FAILURE; // Exit if incorrect arguments are provided
    }

    const char *host = argv[1];     // Host address
    const char *port = argv[2];     // Port number
    const char *username = argv[3]; // Username to use as a cookie value
    const char *message = argv[4];  // Message to post
    int sockfd;

    // Step 1: POST a message with a username
    setup_connection(host, port, &sockfd);
    send_post(sockfd, host, username, message);
    close(sockfd);

    // Step 2: GET to verify the message is present
    setup_connection(host, port, &sockfd);
    send_get(sockfd, host, username, message);
    close(sockfd);

    // Step 3: Test POST without a username (should be forbidden)
    setup_connection(host, port, &sockfd);
    send_post(sockfd, host, NULL, message);
    close(sockfd);

    // Step 4: Test GET without a username (should be forbidden)
    setup_connection(host, port, &sockfd);
    send_get(sockfd, host, NULL, message);
    close(sockfd);

    return EXIT_SUCCESS;
}

// Function to set up a connection to the server using the host and port
void setup_connection(const char *host, const char *port, int *sockfd)
{
    struct addrinfo hints, *res;
    memset(&hints, 0, sizeof hints); // Clear the hints structure
    hints.ai_family = AF_INET;       // Use IPv4
    hints.ai_socktype = SOCK_STREAM; // Use TCP

    // Resolve the server address and port
    if (getaddrinfo(host, port, &hints, &res) != 0)
    {
        perror("getaddrinfo failed");
        exit(EXIT_FAILURE); // Exit if address resolution fails
    }

    // Create a socket
    *sockfd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (*sockfd == -1)
    {
        perror("Socket creation failed");
        exit(EXIT_FAILURE); // Exit if socket creation fails
    }

    // Connect the socket to the server address
    if (connect(*sockfd, res->ai_addr, res->ai_addrlen) == -1)
    {
        perror("Connection failed");
        close(*sockfd); // Close the socket if connection fails
        exit(EXIT_FAILURE);
    }
    freeaddrinfo(res); // Free the address information structure
}

// Function to send a POST request with the message to the server
void send_post(int sockfd, const char *host, const char *username, const char *message)
{
    char request[BUFFER_SIZE];

    // Construct the HTTP POST request
    if (username) {
        snprintf(request, sizeof(request),
                 "POST /api/messages HTTP/1.1\r\n"
                 "Host: %s\r\n"
                 "Content-Type: application/json\r\n"
                 "Cookie: nickname=%s\r\n"     // Include the username as a cookie
                 "Content-Length: %zu\r\n\r\n" // Specify the content length
                 "{\"message\": \"%s\"}",      // JSON body with the message content
                 host, username, strlen(message) + 13, message);
    } else {
        // No cookie header if username is NULL (simulate not logged in)
        snprintf(request, sizeof(request),
                 "POST /api/messages HTTP/1.1\r\n"
                 "Host: %s\r\n"
                 "Content-Type: application/json\r\n"
                 "Content-Length: %zu\r\n\r\n" // Specify the content length
                 "{\"message\": \"%s\"}",
                 host, strlen(message) + 13, message);
    }

    // Send the POST request to the server
    send(sockfd, request, strlen(request), 0);

    // Receive the response from the server
    char response[BUFFER_SIZE];
    int len = recv(sockfd, response, sizeof(response) - 1, 0);
    response[len] = '\0';
    printf("POST response:\n%s\n", response); // Print the server's response

    // If no username, expect 403 Forbidden
    if (!username) {
        assert(strstr(response, "403 Forbidden") != NULL); // Ensure forbidden access
    }
}

// Function to send a GET request to retrieve messages and verify the posted message
void send_get(int sockfd, const char *host, const char *username, const char *message)
{
    char request[BUFFER_SIZE];

    if (username) {
        snprintf(request, sizeof(request),
                 "GET /api/messages HTTP/1.1\r\n"
                 "Host: %s\r\n"
                 "Cookie: nickname=%s\r\n\r\n", // Include the username as a cookie
                 host, username);
    } else {
        snprintf(request, sizeof(request),
                 "GET /api/messages HTTP/1.1\r\n"
                 "Host: %s\r\n\r\n", host);
    }

    // Send the GET request to the server
    send(sockfd, request, strlen(request), 0);

    // Receive the response from the server
    char response[BUFFER_SIZE];
    int len = recv(sockfd, response, sizeof(response) - 1, 0);
    response[len] = '\0';
    printf("GET response:\n%s\n", response); // Print the full GET response for debugging

    // Adjust the assertion to look for a substring if the message might have metadata
    if (username) {
        assert(strstr(response, message) != NULL); // Ensure the posted message is present
    } else {
        assert(strstr(response, "403 Forbidden") != NULL); // Expect forbidden access without username
    }
}


    // Send the GET request to the server
    send(sockfd, request, strlen(request), 0);

    // Receive the response from the server
    char response[BUFFER_SIZE];
    int len = recv(sockfd, response, sizeof(response) - 1, 0);
    response[len] = '\0';
    printf("GET response:\n%s\n", response); // Print the server's response

    // Use assert to verify that the message is in the response
    if (username) {
        assert(strstr(response, message) != NULL); // Ensure the posted message is present
    } else {
        assert(strstr(response, "403 Forbidden") != NULL); // Expect forbidden access without username
    }
}
