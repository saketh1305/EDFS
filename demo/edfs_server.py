import socket
import os

HOST = 'localhost'
PORT = 8000

def handle_request(conn):
    data = conn.recv(1024)
    filename = data.decode().strip()
    if os.path.isfile(filename):
        filesize = os.path.getsize(filename)
        conn.send(str(filesize).encode())
    else:
        conn.send(b"File not found")

def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server started on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                handle_request(conn)

run_server()