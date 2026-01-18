import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 49000))
sock.settimeout(1.0)

print("Listening for X-Plane data on port 49000...")

try:
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            print(f"Received {len(data)} bytes from {addr}")
        except socket.timeout:
            continue
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    sock.close()