CC ?= gcc
CFLAGS = -std=c99 -Wall -Werror -I include

0tDNS : build/0tDNS.o build/receive_respond.o
	$(CC) $^ -lunbound -lldns -o $@

build/%.o : src/%.c | build
	gcc $(CFLAGS) $^ -c -o $@

ask_resolver : build/ask_resolver.o
	$(CC) $^ -lunbound -o $@

build :
	mkdir build

all : 0tDNS receive_respond

clean :
	-rm -r build 0tDNS ask_resolver

.PHONY : clean
