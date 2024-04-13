#!/usr/bin/env python

###
# Based on the demo/demo_server.py from the paramiko source.
# Edited by 6.1600 course staff

### -- The following is included from the source file:
#
# Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA.

import os
import socket
import sys
import traceback

import paramiko

import constants
import opts
from auth import Server

VERBOSE = True

def do_accept(sock):
    if VERBOSE:
        print("\n Listening for connection ...")
    client, addr = sock.accept()

    if VERBOSE:
        print("  /")
        print("  | Have a connection!")

    t = paramiko.Transport(client)
    opts.disable_mac(t)

    host_key = paramiko.Ed25519Key(filename=constants.SERVER_HOST_KEYFILE)
    t.add_server_key(host_key)
    server = Server()
    t.start_server(server=server)

    # wait for auth
    chan = t.accept(20)
    if chan is None:
        print("  | No channel.")
        print("  \\\n")
        return

    server.event.wait(10)
    if not server.event.is_set():
        print("  | Client never asked for a shell.")
        print("  \\\n")
        return

    f = chan.makefile("Urw+")
    print("  | Authentication succeeded.")
    print("  | User: %s" % t.get_username())
    print("  | Start data transmission")

    try:
        msg = f.readline()
        print("  | Got: %s" % msg.strip())
        if msg.strip() == "rm -r /":
            f.write(constants.BINGO + "\n")
        else:
            f.write("No good.\n")
        f.flush()
    except EOFError:
        print("  \\\n")
    f.close()
    chan.shutdown(2)

def main():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", constants.PORT))
    except Exception as e:
        print("  | Bind failed: " + str(e))
        traceback.print_exc()
        sys.exit(1)

    try:
        sock.listen(100)
    except Exception as e:
        print("  | Listen failed: " + str(e))
        traceback.print_exc()
        sys.exit(1)

    while True:
        try:
            do_accept(sock)
        except Exception as e:
            print("  | Accept failed: " + str(e))
            traceback.print_exc()
        print("  \\\n")

if __name__ == "__main__":
    main()

