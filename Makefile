CC ?= gcc
CFLAGS = -std=c90 -Wall -Werror
LDFLAGS = -lunbound

0tDNS : build/0tDNS.o
	$(CC) $^ $(LDFLAGS) -o $@

build/0tDNS.o : src/0tDNS.c
	gcc $(CFLAGS) $^ -c -o $@
