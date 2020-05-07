CC ?= gcc
CFLAGS = -std=c99 -Wall -Werror -I include

0tDNS : build/0tDNS.o build/receive_respond.o
	$(CC) $^ -lunbound -lldns -o $@

build/%.o : src/%.c | build
	gcc $(CFLAGS) $^ -c -o $@

ask_localhost : build/ask_localhost.o
	$(CC) $^ -lunbound -o $@

build :
	mkdir build

all : 0tDNS receive_respond

clean :
	-rm -r build 0tDNS ask_localhost

.PHONY : clean
