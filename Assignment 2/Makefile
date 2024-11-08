CC = gcc
TARGET = screen_scraper

# Check the OS and set flags accordingly
ifeq ($(shell uname), Darwin)
    CFLAGS = -Wall -Wextra -std=c99
else
    CFLAGS = -Wall -Wextra -std=c99 -D_POSIX_C_SOURCE=200112L -D_GNU_SOURCE
endif

all: $(TARGET)

$(TARGET): screen_scraper.c
	$(CC) $(CFLAGS) -o $(TARGET) screen_scraper.c

clean:
	rm -f $(TARGET)

