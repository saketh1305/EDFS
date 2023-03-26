import socket

HOST = 'localhost'
PORT = 8000

def run_client(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(command.encode())
        data = s.recv(1024)
        print(f"Server response: {data.decode()}")

if __name__ == '__main__':
    filename = input("Enter filename: ")
    run_client(filename)