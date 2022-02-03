#!/bin/bash

#Execute this script by
#  -> passing it a runtime argument which will be the FQDN of the DOMAIN
#  -> place the name of your MASTER    role  in local file MASTER.var
#  -> place the name of your SLAVE     roles in local file SLAVES.var
#  -> place the name of your FORWARDER roles in local file FORWARD.var


DOMAIN=$1

for MASTER in $(cat MASTER.txt); do \
	python add-roles.py $DOMAIN MASTER $MASTER; \
done

for SLAVE in $(cat SLAVES.txt); do \
        python add-roles.py $DOMAIN SLAVE $SLAVE; \
done

for FORWARD in $(cat FORWARD.txt); do \
        python add-roles.py $DOMAIN FORWARDER $FORWARD; \
done
