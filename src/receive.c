/*
 * Copyright (c) 2009 - 2012 Marco Peereboom <marco@peereboom.us>
 *
 * Permission to use, copy, modify, and distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 */

#include <stdio.h>
#include <stdlib.h>
#include <err.h>

#include <netinet/in.h>

#include <arpa/inet.h>

#include <ldns/ldns.h>

#define INBUF_SIZE 4096
#define PORT 53

struct sockaddr		paddr;
socklen_t		plen = (socklen_t)sizeof(paddr);

int
udp_bind(int sock, uint16_t port)
{
	struct sockaddr_in		addr;
	in_addr_t			maddr = INADDR_ANY;

	addr.sin_family = AF_INET;
	addr.sin_port = (in_port_t) htons((uint16_t)port);
	addr.sin_addr.s_addr = maddr;
	return (bind(sock, (struct sockaddr*)&addr, (socklen_t) sizeof(addr)));
}

int
socket_create(uint16_t port) {
	int so = socket(AF_INET, SOCK_DGRAM, 0);
	if (so == -1)
		err(1, "can't open socket");
	if (udp_bind(so, port))
		err(1, "can't udp bind");
	return so;
}

void
printpacket(ldns_pkt *pkt)
{
	char			*str = ldns_pkt2str(pkt);
	
	if (str) {
		printf("%s", str);
		LDNS_FREE(str);
	} else
		warnx("could not convert packet to string");
}

void receive_and_print(int so) {
	uint8_t			inbuf[INBUF_SIZE];
	ssize_t			nb;
	ldns_status		status;
	ldns_pkt		*query_pkt;
	
	nb = recvfrom(so, inbuf, INBUF_SIZE, 0, &paddr, &plen);
	if (nb == -1) {
		if (errno == EINTR || errno == EAGAIN)
			return;
		else
			err(EXIT_FAILURE, "recvfrom");
	}

	status = ldns_wire2pkt(&query_pkt, inbuf, (size_t)nb);
	if (status != LDNS_STATUS_OK) {
		warnx("bad packet: %s", ldns_get_errorstr_by_id(status));
		return;
	} else {
		puts("received packet:");
		printpacket(query_pkt);
	}

	ldns_pkt_free(query_pkt);
}

int main(int argc, char **argv) {
	int so;
	
	if (geteuid())
		errx(1, "need root privileges");

	so = socket_create(PORT);

	while (1)
		receive_and_print(so);
}
