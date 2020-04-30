#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <arpa/inet.h>
#include <unbound.h>

#define DEFAULT_DEBUGLEVEL 0

/* In the long run me might rename this file to somewhere else... */
#define TRUST_ANCHOR_FILE "./root.key"

#define MALLOC_FAILURE_STRING "Couldn't allocate memory.\n"

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

enum resolution_mode {
	RECURSIVE,
	FULL,
	RESOLV_CONF
};

struct ub_ctx *ztdns_create_ub_context(enum resolution_mode mode,
				       const char *resolver_addr,
				       int debuglevel) {
	int rc;
	struct ub_ctx* ctx;
	const char *error_message_format;

        ctx = ub_ctx_create();
        if (!ctx) {
		fprintf(stderr, "Couldn't create libunbound context.\n");
		return NULL;
	}

	if (mode == RECURSIVE) {
		rc = ub_ctx_set_fwd(ctx, resolver_addr);
		error_message_format = "Couldn't set forward server: %s\n";
	} else if (mode == FULL) {
		/* TODO use root_hints here for better reliability */
		/* For iterative queries we use DNSSEC if possible */
		rc = ub_ctx_add_ta_autr(ctx, TRUST_ANCHOR_FILE);
		error_message_format = "Couldn't set trust anchors: %s\n";
	} else /* if (mode == RESOLV_CONF) */ {
		/* NULL can be passed to use system's default resolv.conf*/
		rc = ub_ctx_resolvconf(ctx, NULL);
		error_message_format = "Couldn't use system resolv.conf: %s\n";
	}

	if (rc)
		goto out;

	rc = ub_ctx_debuglevel(ctx, debuglevel);
	error_message_format = "Couldn't set debuglevel: %s\n";

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
	else
		examine_result(name, result);
	ub_resolve_free(result);
}

struct ztdns_resolver {
	struct ub_ctx *ctx;
	const char *name; /* arbitrary name - only used for printing to user */
	const char *address; /* IP addr in dot notation stored as string */
	struct ztdns_resolver *next;
};

struct ztdns_resolver *ztdns_create_recursive_resolver(const char *name,
						       const char *address,
						       int debuglevel) {
	struct ztdns_resolver *resolver;
	resolver = malloc(sizeof(struct ztdns_resolver));
	if (!resolver) {
		fprintf(stderr, MALLOC_FAILURE_STRING);
		return NULL;
	}

	resolver->ctx = ztdns_create_ub_context(RECURSIVE, address, debuglevel);
	if (!resolver->ctx)
		goto out_err;

	resolver->name = name;
	resolver->address = address;
	resolver->next = NULL;
	return resolver;

out_err:
	free(resolver);
	return NULL;
}

void ztdns_delete_recursive_resolver(struct ztdns_resolver *resolver) {
	ub_ctx_delete(resolver->ctx);
	free(resolver);
}

struct ztdns_instance {
        struct ub_ctx *ctx_resolv_conf, *ctx_full;
	struct ztdns_resolver *recursive_resolvers;
};

/*
 * Hardcoded recursive DNS servers. A temporary solution - those should
 * ideally by obtained from command line or configuration file.
 */
const char *resolvers_addresses[] = {"8.8.8.8", "8.8.4.4", "1.1.1.1"};
const char *resolvers_names[] = {"google", "google", "cloudflare"};
#define RESOLVERS_COUNT 3

int main(int argc, char** argv)
{
	struct ztdns_instance ztdns;
	int rc = EXIT_FAILURE;
	int i;
	struct ztdns_resolver *tmp;

        if(argc != 2) {
                printf("usage: %s HOSTNAME\n", argv[0]);
                goto out_err;
        }

	ztdns.ctx_full =
		ztdns_create_ub_context(FULL, NULL, DEFAULT_DEBUGLEVEL);
	if (!ztdns.ctx_full)
		goto out_err;

	ztdns.ctx_resolv_conf =
		ztdns_create_ub_context(RESOLV_CONF, NULL, DEFAULT_DEBUGLEVEL);
	if (!ztdns.ctx_resolv_conf)
		goto out_err_cleanup_ctx_full;

	ztdns.recursive_resolvers = NULL;
	for (i = 0; i < RESOLVERS_COUNT; i++) {
		tmp = ztdns_create_recursive_resolver(resolvers_names[i],
						      resolvers_addresses[i],
						      DEFAULT_DEBUGLEVEL);
		if (!tmp)
			goto out_err_cleanup_recursive_resolvers;

		tmp->next = ztdns.recursive_resolvers;
		ztdns.recursive_resolvers = tmp;
	}

	printf("* FULL RESOLUTION\n");
	ztdns_try_resolve(ztdns.ctx_full, argv[1]);
	printf("* USING RESOLVER FROM resolv.conf\n");
	ztdns_try_resolve(ztdns.ctx_resolv_conf, argv[1]);

	for (tmp = ztdns.recursive_resolvers; tmp; tmp = tmp->next) {
		printf("* VIA %s (%s)\n", tmp->name, tmp->address);
		ztdns_try_resolve(tmp->ctx, argv[1]);
	}

	rc = EXIT_SUCCESS;

out_err_cleanup_recursive_resolvers:
	while (ztdns.recursive_resolvers) {
		tmp = ztdns.recursive_resolvers->next;
		ztdns_delete_recursive_resolver(ztdns.recursive_resolvers);
		ztdns.recursive_resolvers = tmp;
	}

	ub_ctx_delete(ztdns.ctx_resolv_conf);
out_err_cleanup_ctx_full:
	ub_ctx_delete(ztdns.ctx_full);
out_err:
	return rc;
}
