#!/bin/python3

import unbound

def query_planned_queries(hour, vpn_id):
    # TODO query database
    # for now, return some sample thought-up data
    return (
        # dns server IP  | dns server id | service_id | service_name
        ("195.98.79.117",  23,           ((89,          "devuan.org"),
                                          (44,          "gry.pl"),
                                          (112,         "invidio.us"))),
        ("192.71.245.208", 33,           ((77,          "debian.org"),
                                          (22,          "nie.ma.takiej.domeny"),
                                          (100,         "onet.pl")))
    )

def resolve_call_back(mydata, status, result):
    dns_id, service_id = mydata
    # TODO write to database
    print("callback called for {}".format(result.qname))
    if status==0 and result.havedata:
        print("Result:",result.data.address_list)

#                                                       hour from argv    | vpn_id in database
contexts = []
for dns_addr, dns_id, services in query_planned_queries("1999-01-08 04:00", 11):
    ctx = unbound.ub_ctx()
    ctx.set_fwd(dns_addr)
    for service_id, service_name in services:
        print(service_name)
        print("starting resolution: {} through {}".format(service_name, dns_addr))
        ctx.resolve_async(service_name, (dns_id, service_id),
                          resolve_call_back,
                          unbound.RR_TYPE_A, unbound.RR_CLASS_IN)
    contexts.append(ctx)
    
for ctx in contexts:
    ctx.wait()
