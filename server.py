import socket
import os
import argparse

def handle_cmd(cmd):
    """
    Handle a DFS command and return the result.
    """
    parts = cmd.split(' ')
    cmd_name = parts[0]
    path = ' '.join(parts[1:])

    if cmd_name == 'ls':
        return '\n'.join(os.listdir(path))
    elif cmd_name == 'rm':
        if os.path.isdir(path):
            os.rmdir(path)
        else:
            os.remove(path)
        return f'Removed {path}'
    elif cmd_name == 'put':
        filename = parts[1]
        with open(filename, 'rb') as f:
            with open(path, 'wb') as dfs_file:
                dfs_file.write(f.read())
        return f'Copied {filename} to {path}'
    elif cmd_name == 'get':
        filename = os.path.basename(path)
        with open(path, 'rb') as dfs_file:
            with open(filename, 'wb') as f:
                f.write(dfs_file.read())
        return f'Copied {path} to {filename}'
    elif cmd_name == 'mkdir':
        os.mkdir(path)
        return f'Created directory {path}'
    elif cmd_name == 'rmdir':
        os.rmdir(path)
        return f'Removed directory {path}'
    elif cmd_name == 'cat':
        with open(path, 'r') as f:
            return f.read()
    else:
        return 'Invalid command'

def start_server(port):
    """
    Start the DFS server.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', port))
        s.listen()

        print(f'DFS server started on port {port}')

        while True:
            conn, addr = s.accept()
            with conn:
                print('Connected by', addr)
                data = conn.recv(1024).decode()
                result = handle_cmd(data)
                conn.sendall(result.encode())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DFS server')
    parser.add_argument('port', metavar='port', type=int, help='Port number')
    args = parser.parse_args()

    start_server(args.port)