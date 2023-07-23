#!/usr/bin/env python3

import argparse
import json
import logging
import subprocess
import sys
from typing import Optional


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true", default=False)
    args = parser.parse_args()
    level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=level)
    sys.exit(
        0
        if get_router_mac_address() in ["00:00:00:00:00:00"]
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
