import socket
import argparse
import os

def send_cmd(cmd):
    """
    Send a command to the DFS server and receive the response.
    """
    HOST = 'localhost'
    PORT = 8010

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(cmd.encode())
        data = s.recv(1024)
    return data.decode()

def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description='DFS client')
    parser.add_argument('cmd', metavar='cmd', type=str, help='DFS command')
    parser.add_argument('path', metavar='path', type=str, help='DFS path')

    return parser.parse_args()

def dfs_ls(path):
    """
    List the contents of a directory in the DFS.
    """
    return send_cmd(f'ls {path}')

def dfs_rm(path):
    """
    Remove a file or directory from the DFS.
    """
    return send_cmd(f'rm {path}')

def dfs_put(local_path, dfs_path):
    """
    Copy a file from the local filesystem to the DFS.
    """
    return send_cmd(f'put {local_path} {dfs_path}')

def dfs_get(dfs_path, local_path):
    """
    Copy a file from the DFS to the local filesystem.
    """
    return send_cmd(f'get {dfs_path} {local_path}')

def dfs_mkdir(path):
    """
    Create a directory in the DFS.
    """
    return send_cmd(f'mkdir {path}')

def dfs_rmdir(path):
    """
    Remove a directory from the DFS.
    """
    return send_cmd(f'rmdir {path}')

def dfs_cat(path):
    """
    Display the contents of a file in the DFS.
    """
    return send_cmd(f'cat {path}')

if __name__ == '__main__':
    args = parse_args()

    cmd = args.cmd
    path = args.path

    if cmd == 'ls':
        print(dfs_ls(path))
    elif cmd == 'rm':
        print(dfs_rm(path))
    elif cmd == 'put':
        local_path = path
        dfs_path = os.path.basename(path)
        print(dfs_put(local_path, dfs_path))
    elif cmd == 'get':
        dfs_path = path
        local_path = os.path.basename(path)
        print(dfs_get(dfs_path, local_path))
    elif cmd == 'mkdir':
        print(dfs_mkdir(path))
    elif cmd == 'rmdir':
        print(dfs_rmdir(path))
    elif cmd == 'cat':
        print(dfs_cat(path))
    else:
        print('Invalid command')