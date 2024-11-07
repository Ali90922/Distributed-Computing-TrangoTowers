CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -D_POSIX_C_SOURCE=200112L -D_GNU_SOURCE
TARGET = screen_scraper

all: $(TARGET)

$(TARGET): screen_scraper.c
	$(CC) $(CFLAGS) -o $(TARGET) screen_scraper.c

clean:
	rm -f $(TARGET)
