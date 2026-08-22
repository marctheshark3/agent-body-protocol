#!/usr/bin/env python3
"""Forward tailnet bind -> loopback. Not Funnel. Not 0.0.0.0."""

from __future__ import annotations

import argparse
import socket
import threading

TS_IP = "100.110.151.120"


def pump(src: socket.socket, dst: socket.socket) -> None:
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except OSError:
        pass
    finally:
        try:
            dst.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def handle(client: socket.socket, dest_port: int) -> None:
    upstream = socket.create_connection(("127.0.0.1", dest_port), timeout=5)
    threading.Thread(target=pump, args=(client, upstream), daemon=True).start()
    pump(upstream, client)
    client.close()
    upstream.close()


def listen(bind_ip: str, port: int) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((bind_ip, port))
    sock.listen(32)
    print(f"tailnet {bind_ip}:{port} -> 127.0.0.1:{port}", flush=True)
    while True:
        client, _ = sock.accept()
        threading.Thread(target=handle, args=(client, port), daemon=True).start()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", default=TS_IP)
    parser.add_argument("--ports", default="5001,5002,5055")
    args = parser.parse_args()
    if not args.bind.startswith("100."):
        raise SystemExit("bind must be a Tailscale 100.x address")
    for port in (int(p) for p in args.ports.split(",")):
        threading.Thread(target=listen, args=(args.bind, port), daemon=True).start()
    threading.Event().wait()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
