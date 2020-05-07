#ifndef ZTDNS_LOG_H
#define ZTDNS_LOG_H

#include <stdio.h>

/* These functions will change later - it's just a "mock", so that every1 can
 * already write code with ztdns_info() :)
 * Use like ztdns_info("something wrong happened! %s", errorstring);
 */
#define ztdns_debug(printfargs...) printf(printfargs)
#define ztdns_info(printfargs...) printf(printfargs)
#define ztdns_warn(printfargs...) printf(printfargs)
#define ztdns_error(printfargs...) printf(printfargs)

#endif /* ZTDNS_LOG_H */
