#!/usr/bin/env python3

# Copyright 2023 Pontus Lurcock
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the “Software”),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

"""Check the MAC address of the currently used router against a whitelist

Exit status 0 if the MAC address is on the whitelist, 1 if not.
"""

import argparse
import json
import logging
import subprocess
import sys
from typing import Optional


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true", default=False)
    parser.add_argument("mac", type=str, nargs="*",
                        help="MAC address to include in the whitelist")
    args = parser.parse_args()
    level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=level)
    macs = map(lambda s: s.lower(), args.mac)
    sys.exit(
        0
        if get_router_mac_address() in macs
        else 1
    )

def get_router_mac_address() -> Optional[str]:
    route_process = subprocess.run(
        ["ip", "--json", "route", "list"], capture_output=True
    )
    routes = json.loads(route_process.stdout.decode())
    logging.info(f"Routes: {routes}")

    gateway_ips = [
        route["gateway"] for route in routes if route["dst"] == "default"
    ]
    logging.info(f"Gateway IPs: {gateway_ips}")
    if len(set(gateway_ips)) != 1:
        logging.info(
            f"{len(set(gateway_ips))} different gateway IPs, giving up."
        )
        return None

    gateway_ip = gateway_ips[0]
    subprocess.run(["ping", "-c", "1", gateway_ip], capture_output=True)
    neighbour_process = subprocess.run(
        ["ip", "--json", "neigh"], capture_output=True
    )
    neighbours = json.loads(neighbour_process.stdout.decode())
    logging.info(f"Neighbours: {neighbours}")

    gateway_macs = [
        neighbour["lladdr"]
        for neighbour in neighbours
        if neighbour["dst"] == gateway_ip and "lladdr" in neighbour
    ]
    logging.info(f"Gateway MACs: {gateway_macs}")

    return (
        gateway_macs[0].lower()
        if len(set(gateway_macs)) == 1
        else None
    )


if __name__ == "__main__":
    main()
