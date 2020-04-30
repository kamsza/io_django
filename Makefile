CC ?= gcc
CFLAGS = -std=c99 -Wall -Werror

0tDNS : build/0tDNS.o
	$(CC) $^ -lunbound -o $@

build/0tDNS.o : src/0tDNS.c
	gcc $(CFLAGS) $^ -c -o $@

receive : build/receive.o
	$(CC) $^ -lldns -o $@

build/receive.o : src/receive.c
	gcc $(CFLAGS) $^ -c -o $@
