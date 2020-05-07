/*
 * Code in examine_result() is taken from official libunbound examples:
 * https://nlnetlabs.nl/documentation/unbound/libunbound-tutorial-3/
 * The rest of this file is
 * Copyright (C) 2020 by Wojtek Kosior <echo a3dvanR1c0Bwcm90b25tYWlsLmNvbQo= | base64 --decode>

 * Permission to use, copy, modify, and/or distribute this software
 * for any purpose with or without fee is hereby granted.

 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
 * REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
 * AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
 * INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
 * LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
 * OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
 * PERFORMANCE OF THIS SOFTWARE.
 */

/*
 * This is a simple helper program for testing our resolver.
 */

#include <stdio.h>
#include <stdlib.h>
#include <arpa/inet.h>

#include <unbound.h>

/* examine the result structure in detail */
void examine_result(const char *query, struct ub_result *result)
{
        int i;
        int num;

        printf("The query is for: %s\n", query);
        printf("The result has:\n");
        printf("qname: %s\n", result->qname);
        printf("qtype: %d\n", result->qtype);
        printf("qclass: %d\n", result->qclass);
        if(result->canonname)
                printf("canonical name: %s\n",
		       result->canonname);
        else    printf("canonical name: <none>\n");

        if(result->havedata)
                printf("has data\n");
        else    printf("has no data\n");

        if(result->nxdomain)
                printf("nxdomain (name does not exist)\n");
        else    printf("not an nxdomain (name exists)\n");

        if(result->secure)
                printf("validated to be secure\n");
        else    printf("not validated as secure\n");

        if(result->bogus)
                printf("a security failure! (bogus)\n");
        else    printf("not a security failure (not bogus)\n");

        printf("DNS rcode: %d\n", result->rcode);

        if(!result->havedata)
		return;

        num = 0;
        for(i=0; result->data[i]; i++) {
                printf("result data element %d has length %d\n",
		       i, result->len[i]);
                printf("result data element %d is: %s\n",
		       i, inet_ntoa(*(struct in_addr*)result->data[i]));
                num++;
        }
        printf("result has %d data element(s)\n", num);
}

struct ub_ctx *create_ub_context(int debuglevel) {
	int rc;
	struct ub_ctx* ctx;
	char *error_message_format;

        ctx = ub_ctx_create();
        if (!ctx) {
		fprintf(stderr, "Couldn't create libunbound context.\n");
		return NULL;
	}

	error_message_format = "Couldn't set forwarder: %s\n";
	rc = ub_ctx_set_fwd(ctx, "127.0.0.1");
	if (rc)
		goto out;

	error_message_format = "Couldn't set debuglevel: %s\n";
	rc = ub_ctx_debuglevel(ctx, debuglevel);

out:
	if (rc) {
		fprintf(stderr, error_message_format, ub_strerror(rc));
		ub_ctx_delete(ctx);
		return NULL;
	}

	return ctx;
}

void ztdns_try_resolve(struct ub_ctx *ctx, const char *name) {
	struct ub_result* result;
	int rc;
        rc = ub_resolve(ctx, name,
			1 /* TYPE A (IPv4 address) */,
			1 /* CLASS IN (internet) */, &result);
        if(rc)
                printf("resolve error: %s\n", ub_strerror(rc));
	else {
		examine_result(name, result);
		ub_resolve_free(result);
	}
}

int main(int argc, char** argv)
{
	struct ub_ctx *ctx;
	
	if (argc < 2) {
		printf("Usage: %s DOMAINNAME\n", argv[0]);
		return EXIT_FAILURE;
	}

	ctx = create_ub_context(3);
	if (!ctx)
		return EXIT_FAILURE;

	ztdns_try_resolve(ctx, argv[1]);

	ub_ctx_delete(ctx);

	return EXIT_SUCCESS;
}
