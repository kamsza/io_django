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

/* for strdup() */
#define _POSIX_C_SOURCE 200809L
#include <string.h>

#include <stdio.h>
#include <stdlib.h>
#include <err.h>

#include <netinet/in.h>
#include <arpa/inet.h>

#include <ldns/ldns.h>

#define MAXLINE 256
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

ldns_pkt *
receive_and_print(int so) {
	uint8_t			inbuf[INBUF_SIZE];
	ssize_t			nb;
	ldns_status		status;
	ldns_pkt		*query_pkt;

	nb = recvfrom(so, inbuf, INBUF_SIZE, 0, &paddr, &plen);
	if (nb == -1) {
		if (errno == EINTR || errno == EAGAIN)
			return NULL;
		else
			err(EXIT_FAILURE, "recvfrom");
	}

	status = ldns_wire2pkt(&query_pkt, inbuf, (size_t)nb);
	if (status != LDNS_STATUS_OK) {
		warnx("bad packet: %s", ldns_get_errorstr_by_id(status));
		return NULL;
	} else {
		puts("received packet:");
		printpacket(query_pkt);
	}

	return query_pkt;
}

int
send_response(int so, const char *hostname, ldns_pkt *respkt, uint16_t id)
{
	size_t			answer_size;
	ldns_status		status;
	uint8_t			*outbuf = NULL;
	int			rv = 1;

	if (hostname == NULL || respkt == NULL) {
		warnx("send_response: invalid parameters");
		return (0);
	}

	ldns_pkt_set_id(respkt, id);
	status = ldns_pkt2wire(&outbuf, respkt, &answer_size);
	if (status != LDNS_STATUS_OK)
		warnx("can't create answer: %s",
		      ldns_get_errorstr_by_id(status));
	else {
		puts("response packet:");
		printpacket(respkt);

		if (sendto(so, outbuf, answer_size, 0, &paddr, plen) == -1)
			warn("send_response: sendto");
		else {
			rv = 0;

			printf("send_response: resolved %s", hostname);
		}
	}

	if (outbuf)
		LDNS_FREE(outbuf);

	return (rv);
}

char *
hostnamefrompkt(ldns_pkt *pkt, ldns_rr **qrr)
{
	ldns_rr			*query_rr;
	ldns_buffer		*out = NULL;
	ldns_rdf		*rdf;
	char			*ret = NULL;

	if (pkt == NULL)
		return (NULL);

	query_rr = ldns_rr_list_rr(ldns_pkt_question(pkt), 0);
	if (query_rr == NULL) {
		warnx("hostnamefrompkt invalid parameters");
		goto done;
	}

	out = ldns_buffer_new(LDNS_MAX_DOMAINLEN);
	if (out == NULL) {
		warnx("no memory for out buffer");
		goto done;
	}

	rdf = ldns_rr_owner(query_rr);
	if (ldns_rdf2buffer_str_dname(out, rdf) != LDNS_STATUS_OK) {
		warnx("can't get hostname");
		goto done;
	}

	ret = strdup((char *)ldns_buffer_begin(out));
	if (ret == NULL) {
		warn("no memory for hostname");
		goto done;
	}

	if (qrr)
		*qrr = query_rr;
done:
	if (out)
		ldns_buffer_free(out);

	return (ret);
}

int
spoofquery(int so, const char *hostname, ldns_rr *query_rr, u_int16_t id)
{
	ldns_status		status;
	ldns_rr_list		*answer_an = NULL;
	ldns_rr_list		*answer_ns = NULL;
	ldns_rr_list		*answer_ad = NULL;
	ldns_rr_list		*answer_qr = NULL;
	ldns_pkt		*answer_pkt = NULL;
	ldns_rr			*myrr = NULL, *myaurr = NULL, *myasrr = NULL;
	ldns_rdf		*prev = NULL;
	char			buf[MAXLINE * 2];
	uint8_t			*outbuf = NULL;
	int			rv = 1;
	const char	        *ipaddr = "127.0.0.1";

	/* answer section */
	answer_an = ldns_rr_list_new();
	if (answer_an == NULL)
		goto unwind;

	/* authority section */
	answer_ns = ldns_rr_list_new();
	if (answer_ns == NULL)
		goto unwind;

	/* if we have an ip spoof it there */
	if (ipaddr) {
		/* an */
		snprintf(buf, sizeof buf, "%s\t%d\tIN\tA\t%s",
			 hostname, 259200, ipaddr);
		status = ldns_rr_new_frm_str(&myrr, buf, 0, NULL, &prev);
		if (status != LDNS_STATUS_OK) {
			fprintf(stderr, "can't create answer section: %s\n",
				ldns_get_errorstr_by_id(status));
			goto unwind;
		}
		ldns_rr_list_push_rr(answer_an, myrr);
		ldns_rdf_deep_free(prev);
		prev = NULL;

		/* ns */
		snprintf(buf, sizeof buf, "%s\t%d\tIN\tNS\t%s.",
			 hostname, 259200, "localhost");
		status = ldns_rr_new_frm_str(&myaurr, buf, 0, NULL, &prev);
		if (status != LDNS_STATUS_OK) {
			fprintf(stderr, "can't create authority section: %s\n",
				ldns_get_errorstr_by_id(status));
			goto unwind;
		}
		ldns_rr_list_push_rr(answer_ns, myaurr);
		ldns_rdf_deep_free(prev);
		prev = NULL;
	} else {
		snprintf(buf, sizeof buf, "%s\t3600\tIN\tSOA\t%s root.%s %s",
			 hostname,
			 hostname,
			 hostname,
			 "2 3600 900 3600000 3600");
		status = ldns_rr_new_frm_str(&myaurr, buf, 0, NULL, &prev);
		if (status != LDNS_STATUS_OK) {
			fprintf(stderr, "can't create authority section: %s\n",
				ldns_get_errorstr_by_id(status));
			goto unwind;
		}
		ldns_rr_list_push_rr(answer_ns, myaurr);
		ldns_rdf_deep_free(prev);
		prev = NULL;
	}

	/* question section */
	answer_qr = ldns_rr_list_new();
	if (answer_qr == NULL)
		goto unwind;
	ldns_rr_list_push_rr(answer_qr, ldns_rr_clone(query_rr));

	/* additional section */
	answer_ad = ldns_rr_list_new();
	if (answer_ad == NULL)
		goto unwind;
	if (ipaddr) {
		snprintf(buf, sizeof buf, "%s\t%d\tIN\tA\t%s",
			 "localhost",
			 259200,
			 "127.0.0.1");
		status = ldns_rr_new_frm_str(&myasrr, buf, 0, NULL, &prev);
		if (status != LDNS_STATUS_OK) {
			fprintf(stderr, "can't create additional section: %s\n",
				ldns_get_errorstr_by_id(status));
			goto unwind;
		}
		ldns_rr_list_push_rr(answer_ad, myasrr);
		ldns_rdf_deep_free(prev);
		prev = NULL;

		/* V6 */
		snprintf(buf, sizeof buf, "%s\t%d\tIN\tAAAA\t%s",
			 "localhost",
			 259200,
			 "::1");
		status = ldns_rr_new_frm_str(&myasrr, buf, 0, NULL, &prev);
		if (status != LDNS_STATUS_OK) {
			fprintf(stderr, "can't create additional section: %s\n",
				ldns_get_errorstr_by_id(status));
			goto unwind;
		}
		ldns_rr_list_push_rr(answer_ad, myasrr);
		ldns_rdf_deep_free(prev);
		prev = NULL;
	}

	/* actual packet */
	answer_pkt = ldns_pkt_new();
	if (answer_pkt == NULL)
		goto unwind;

	ldns_pkt_set_qr(answer_pkt, 1);
	ldns_pkt_set_aa(answer_pkt, 1);
	if (ipaddr == NULL)
		ldns_pkt_set_rcode(answer_pkt, LDNS_RCODE_NXDOMAIN);

	ldns_pkt_push_rr_list(answer_pkt, LDNS_SECTION_QUESTION, answer_qr);
	ldns_pkt_push_rr_list(answer_pkt, LDNS_SECTION_ANSWER, answer_an);
	ldns_pkt_push_rr_list(answer_pkt, LDNS_SECTION_AUTHORITY, answer_ns);
	ldns_pkt_push_rr_list(answer_pkt, LDNS_SECTION_ADDITIONAL, answer_ad);

	/* reply to caller */
	if (send_response(so, hostname, answer_pkt, id))
		warnx("send_response failed");

unwind:
	if (answer_pkt)
		ldns_pkt_free(answer_pkt);
	if (outbuf)
		LDNS_FREE(outbuf);
	if (answer_qr)
		ldns_rr_list_free(answer_qr);
	if (answer_an)
		ldns_rr_list_free(answer_an);
	if (answer_ns)
		ldns_rr_list_free(answer_ns);
	if (answer_ad)
		ldns_rr_list_free(answer_ad);

	return (rv);
}

int handle_query(int so) {
	ldns_pkt *query_pkt;
	ldns_rr  *query_rr;
	uint16_t id;
	int rv = 1;
	char *hostname;

	query_pkt = receive_and_print(so);
	if (!query_pkt)
		return 1;

	hostname = hostnamefrompkt(query_pkt, &query_rr);
	if (!hostname)
		goto out_cleanup_pkt;

	id = ldns_pkt_id(query_pkt);

	rv = spoofquery(so, hostname, query_rr, id);

	free(hostname);

out_cleanup_pkt:
	ldns_pkt_free(query_pkt);
	return rv;
}

int main(int argc, char **argv) {
	int so;

	if (geteuid())
		errx(1, "need root privileges");

	so = socket_create(PORT);

	/*
	 * The original adsuck program would additionally do many cool things
	 * in main(), i.e. parse command line options, drop root privileges,
	 * setup signal handlers, etc. We could incorporate some of this into
	 * our program later. I omitted it for now for simplicity and to
	 * ease porting to windoze if You guys want to do that (but don't
	 * count on me in this matter).
	 */

	while (1)
		handle_query(so);
}
