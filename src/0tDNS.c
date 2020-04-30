#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
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

struct ub_ctx *ztdns_create_context_with_resolver(const char *resolver_addr) {
	int rc;
	struct ub_ctx* ctx;
        ctx = ub_ctx_create();
        if (!ctx) {
		fprintf(stderr, "Couldn't create libunbound context.\n");
		return NULL;
	}
	rc = ub_ctx_set_fwd(ctx, resolver_addr);
	if (rc) {
                fprintf(stderr, "Couldn't set forward server: %s\n",
			ub_strerror(rc));
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
	else
		examine_result(name, result);
	ub_resolve_free(result);
}

int main(int argc, char** argv)
{
        struct ub_ctx
		*ctx_google1 = NULL,
		*ctx_google2 = NULL,
		*ctx_cloudflare = NULL;
        int rc = EXIT_SUCCESS;

        if(argc != 2) {
                printf("usage: <hostname>\n");
                return EXIT_FAILURE;
        }

	ctx_google1 = ztdns_create_context_with_resolver("8.8.8.8");
	ctx_google2 = ztdns_create_context_with_resolver("8.8.4.4");
	ctx_cloudflare = ztdns_create_context_with_resolver("1.1.1.1");

	if (!ctx_google1 || !ctx_google2 || !ctx_cloudflare) {
		rc = EXIT_FAILURE;
		goto abort;
	}

	printf("* VIA GOOGLE (8.8.8.8)\n");
	ztdns_try_resolve(ctx_google1, argv[1]);
	printf("* VIA GOOGLE (8.8.4.4)\n");
	ztdns_try_resolve(ctx_google2, argv[1]);
	printf("* VIA CLOUDFLARE (1.1.1.1)\n");
	ztdns_try_resolve(ctx_cloudflare, argv[1]);

abort:
        if (ctx_google1)
		ub_ctx_delete(ctx_google1);
        if (ctx_google2)
		ub_ctx_delete(ctx_google2);
        if (ctx_cloudflare)
		ub_ctx_delete(ctx_cloudflare);

	return rc;
}
