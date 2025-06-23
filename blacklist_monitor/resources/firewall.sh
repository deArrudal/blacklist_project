#!/bin/bash

sudo nft add table inet filter

sudo nft add set inet filter blocked_ips '{ type ipv4_addr; flags timeout; }'

sudo nft add chain inet filter input '{ type filter hook input priority 0; }'

sudo nft add rule inet filter input ip saddr @blocked_ips drop
