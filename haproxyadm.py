#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Module to find application sockets"""

import argparse
from haproxyadmin import haproxy


def fetch_backend_sockets(data):
    """
    Function to fetch data from haproxy sockets
    """
    hap = haproxy.HAProxy(socket_dir="/var/lib/haproxy")
    backends = hap.backends()
    for backend in backends:
        if backend.name == data:
            print backend.process_nb


def main():
    """
    Main Function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--backend_name', help="Enter backend name")
    args = parser.parse_args()
    fetch_backend_sockets(data=args.backend_name)

if __name__ == "__main__":
    main()
