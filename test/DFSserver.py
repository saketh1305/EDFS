import socket
import os
import threading
from servers import MetadataServer,DataServer


metadata_server = MetadataServer('metadata.json')
data_servers = [DataServer(port) for port in [5000, 5001, 5002]]


class DFSServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            print(f'DFS server listening on {self.host}:{self.port}...')
            while True:
                conn, addr = s.accept()
                print(f'Connection from {addr} received')
                threading.Thread(target=self.handle_request, args=(conn,)).start()

    def handle_request(self, conn):
        data = conn.recv(1024).decode()
        tokens = data.split()
        if tokens[0] == 'ls':
            if len(tokens) == 1:
                response = '\n'.join(os.listdir('/'))
            else:
                path = tokens[1]
                response = '\n'.join(os.listdir(path))
            conn.sendall(response.encode())
        elif tokens[0] == 'rm':
            file_path = tokens[1]
            try:
                os.remove(file_path)
                metadata_server.remove_file(file_path)
                conn.sendall('OK'.encode())
            except FileNotFoundError:
                conn.sendall(f'File not found: {file_path}'.encode())
        elif tokens[0] == 'put':
            file_path = tokens[1]
            block_size = 1024 * 1024
            block_paths = []
            with open(file_path, 'rb') as f:
                while True:
                    block_data = f.read(block_size)
                    if not block_data:
                        break
                    block_path = f'{file_path}.{len(block_paths)}'
                    with open(block_path, 'wb') as bf:
                        bf.write(block_data)
                    block_paths.append(block_path)
            metadata_server.add_file(file_path, block_paths)
            conn.sendall('OK'.encode())
        elif tokens[0] == 'get':
            file_path = tokens[1]
            block_paths = metadata_server.get_block_paths(file_path)
            with open(file_path, 'wb') as f:
                for block_path in block_paths:
                    data_server = self.choose_data_server()
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ds_conn:
                        ds_conn.connect(('localhost', data_server.port))
                        ds_conn.sendall(block_path.encode())
                        block_data = ds_conn.recv(1024)
                    f.write(block_data)
            conn.sendall('OK'.encode())
        elif tokens[0] == 'mkdir':
            dir_path = tokens[1]
            os.makedirs(dir_path, exist_ok=True)
            conn.sendall('OK'.encode())
        elif tokens[0] == 'rmdir':
            dir_path = tokens[1]
            try:
                os.rmdir(dir_path)
                conn.sendall('OK'.encode())
            except OSError:
                conn.sendall(f'Directory not empty: {dir_path}'.encode())
        elif tokens[0] == 'cat':
            file_path = tokens[1]
            block_paths = metadata_server.get_block_paths(file_path)
            response = ''
            for block_path in block_paths:
                with open(block_path, 'r') as bf:
                    response += bf.read()
            conn.sendall(response.encode())
        else:
            conn.sendall(f'Unknown command: {tokens[0]}'.encode())
    def choose_data_server(self):
        # Choose the data server with the fewest blocks
        return min(data_servers, key=lambda ds: len(ds.block_paths))

    def shutdown(self):
        for data_server in data_servers:
            data_server.shutdown()


if __name__ == '__main__':
    server = DFSServer('localhost', 6000)
    server.start()


