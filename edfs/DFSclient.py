import socket


class DFSClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def execute_command(self, command):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.sendall(command.encode())
            response_list = []
            response = s.recv(1024*1024).decode()
            return response


if __name__ == '__main__':
    client = DFSClient('localhost', 6000)
    while True:
        command = input('> ')
        if not command:
            continue
        elif command == 'exit':
            break
        response = client.execute_command(command)
        print(response)