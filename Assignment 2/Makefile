CC = gcc
CFLAGS = -Wall -Wextra -std=c99
TARGET = screen_scraper

all: $(TARGET)

$(TARGET): screen_scraper.c
	$(CC) $(CFLAGS) -o $(TARGET) screen_scraper.c

clean:
	rm -f $(TARGET)

