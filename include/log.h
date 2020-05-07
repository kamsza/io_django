#ifndef ZTDNS_LOG_H
#define ZTDNS_LOG_H

#include <stdio.h>

#define ERROR 1
#define WARN  2
#define INFO  3
#define DEBUG 4

/* This function will change later - it's just a "mock", so that every1 can
 * already write code with ztdns_log() :)
 * Use like ztdns_log(DEBUG, "something wrong happened! %s", errorstring);
 */
#define ztdns_log(level, printfargs...) printf(printfargs)

#endif /* ZTDNS_LOG_H */
