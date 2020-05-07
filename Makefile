CC ?= gcc
CFLAGS = -std=c99 -Wall -Werror -I include

0tDNS : build/0tDNS.o
	$(CC) $^ -lunbound -o $@

build/0tDNS.o : src/0tDNS.c | build
	gcc $(CFLAGS) $^ -c -o $@

receive_respond : build/receive_respond.o
	$(CC) $^ -lldns -o $@

build/receive_respond.o : src/receive_respond.c | build
	gcc $(CFLAGS) $^ -c -o $@

ask_localhost : build/ask_localhost.o
	$(CC) $^ -lunbound -o $@

build/ask_localhost.o : src/ask_localhost.c | build
	gcc $(CFLAGS) $^ -c -o $@

build :
	mkdir build

all : 0tDNS receive_respond

clean :
	-rm -r build 0tDNS receive_respond ask_localhost

.PHONY : clean
