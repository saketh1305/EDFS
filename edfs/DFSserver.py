import socket
import os
import threading
import json
from servers import MetadataServer,DataServer


metadata_server = MetadataServer('metadata.json')
data_servers = [DataServer(port) for port in [5000, 5001, 5002]]


class DFSServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.rf = 2

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            print(f'DFS server listening on {self.host}:{self.port}...')
            while True:
                conn, addr = s.accept()
                print(f'Connection from {addr} received')
                threading.Thread(target=self.handle_request, args=(conn,)).start()

    def write_file(self,path,data):
            block_size = 1024*4
            blocks = [data[i:i+block_size] for i in range(0, len(data), block_size)]
            block_paths = []
            for block in blocks:
                block_path  = []
                block_id = len(block_paths)
                for i in range(self.rf):
                    data_server = self.choose_data_server()
                    block_path.append(data_server.write_block(path,block_id,block))
                block_paths.append(block_path)
            return block_paths
    
    def read_file(self, path):
        if path not in metadata_server.metadata:
            return 'File not found'
        block_paths = metadata_server.metadata[path]["blocks"]
        data = b''
        for block_path in block_paths:
            data_server = None
            for server in data_servers:
                if server.has_block(block_path[0]):
                    data_server = server
                    break
            if data_server is None:
                return 'Error: block not found on any data server'
            block_data = data_server.read_block(block_path[0])
            data += block_data
        return data.decode()

    def dir_already_exist(self,dfs_dir_path):
        metadata = metadata_server.metadata
        items = list(metadata.keys())
        if dfs_dir_path in items:
            return True
        else:
            dfs_dir_path = dfs_dir_path + '/'
            for item in items:
                if not (item.find(dfs_dir_path) == -1):
                    return True
        return False

    def isFile(self, dfs_dir_path):
        return metadata_server.metadata[dfs_dir_path]['type'] == 'file'

    def is_dir_empty(self,dfs_dir_path):
        dirs = metadata_server.metadata[dfs_dir_path]
        return dirs['files'] == [] and dirs['sub_dir'] == []

    def parent_dir_exist(self,dfs_dir_path):
        splits = dfs_dir_path.split("/")
        if len(splits) == 2:
            return True
        parent_dir = "/".join(splits[:-1])
        if self.dir_already_exist(parent_dir):
            return True
        return False

    def is_file(self, path):
        return path.split('/')[-1].find(".") != -1

    def is_directory(self, path):
        return metadata_server.metadata[path]['type'] == 'directory'

    def handle_request(self, conn):
        data = conn.recv(1024).decode()
        tokens = data.split()

        if tokens[0] == 'put':
            local_file_path = tokens[1]
            dfs_file_path = tokens[2]
            if not self.is_file(dfs_file_path):
                conn.sendall(f'Not a file!!'.encode())
            elif self.dir_already_exist(dfs_file_path):
                conn.sendall(f'File cannot be Uploaded! \n{dfs_file_path} Already Exists!'.encode())
            elif not self.parent_dir_exist(dfs_file_path):
                conn.sendall(f'Invalid Path! \nParent Directory doesn\'t Exists!'.encode())
            else:
                with open(local_file_path, 'rb') as f:
                    file_data = f.read()
                block_paths = self.write_file(dfs_file_path,file_data)
                metadata_server.add_file(dfs_file_path, block_paths)
                conn.sendall('File Uploaded Successfully :-)!!'.encode())

        elif tokens[0] == 'get':
            dfs_file_path = tokens[1]
            local_file_path = tokens[2]
            if not self.is_file(dfs_file_path):
                conn.sendall(f'Not a file!!'.encode())
            if not self.dir_already_exist(dfs_file_path):
                conn.sendall(f'File not available!'.encode())
            file_data = self.read_file(dfs_file_path)
            with open(local_file_path , 'w') as f:
                f.write(file_data)
            conn.sendall('File Downloaded Successfully!!'.encode())

        elif tokens[0] == 'cat':
            dfs_file_path = tokens[1]
            if not self.dir_already_exist(dfs_file_path):
                conn.sendall(f'File not exists!!'.encode())
            elif self.is_directory(dfs_file_path):
                conn.sendall(f'{dfs_file_path} is a directory!'.encode())
            else:
                file_data = self.read_file(dfs_file_path)
                conn.sendall(file_data.encode())

        elif tokens[0] == 'mkdir':
            dfs_dir_path = tokens[1]
            if dfs_dir_path[-1] == '/' and dfs_dir_path != '/':
                conn.sendall(f'Invalid Path!!'.encode())
            if dfs_dir_path == '/':
                conn.sendall(f'Root Directory Cannot be Created!!'.encode())
            elif self.dir_already_exist(dfs_dir_path):
                conn.sendall(f'Directory Cannot be Created!!\n {dfs_dir_path} Already Exists :-('.encode())
            else:
                if not self.parent_dir_exist(dfs_dir_path):
                    conn.sendall(f'{dfs_dir_path} : Invalid Path\nParent directory doesn\'t exist!'.encode())
                metadata_server.add_dir(dfs_dir_path)
                splits = dfs_dir_path.split("/")
                if len(splits) > 2:
                    parent_dir = "/".join(splits[:-1])
                else:
                    parent_dir = "/"
                dir_name = dfs_dir_path.split('/')[-1]
                metadata_server.metadata[parent_dir]['sub_dir'].append(dir_name)
                metadata_server.save_metadata()
                conn.sendall(f'{dfs_dir_path} : Directory Created Successfully!!'.encode())

        elif tokens[0] == 'rmdir':
            dfs_dir_path = tokens[1]
            if dfs_dir_path == '/':
                conn.sendall(f'Root Directory Cannot be Removed!!'.encode())
            elif not self.dir_already_exist(dfs_dir_path):
                conn.sendall(f'{dfs_dir_path} path doesn\'t exists!!'.encode())
            elif self.isFile(dfs_dir_path):
                conn.sendall(f'{dfs_dir_path} is not a Directory!!'.encode())
            else:
                if self.is_dir_empty(dfs_dir_path):
                    metadata_server.remove_dir(dfs_dir_path)
                    conn.sendall(f'{dfs_dir_path} : Directory Removed Successfully!!'.encode())
                else:
                    conn.sendall(f'{dfs_dir_path} : Directory Not Empty!!'.encode())

        elif tokens[0] == 'rm':
            dfs_file_path = tokens[1]
            if not self.dir_already_exist(dfs_file_path):
                conn.sendall(f'{dfs_file_path} file path doesn\'t exists!!'.encode())
            elif self.is_directory(dfs_file_path):
                conn.sendall(f'{dfs_file_path} is a directory'.encode())
            else:
                block_paths = metadata_server.metadata[dfs_file_path]["blocks"]
                for block_path in block_paths:
                    for i in range(len(block_path)):
                        data_server = None
                        for server in data_servers:
                            if server.has_block(block_path[i]):
                                data_server = server
                                break
                        if data_server is None:
                            return 'Error: block not found on any data server'
                        os.remove(block_path[i])
                        data_server.remove_block(block_path[i])
                metadata_server.metadata.pop(dfs_file_path)
                metadata_server.save_metadata()
                splits = dfs_file_path.split("/")
                if len(splits) > 2:
                    parent_dir = "/".join(splits[:-1])
                else:
                    parent_dir = "/"
                file_name = dfs_file_path.split('/')[-1]
                metadata_server.metadata[parent_dir]['files'].remove(file_name)
                metadata_server.save_metadata()
                conn.sendall(f'File removed successfully!!'.encode())
        elif tokens[0] == 'ls':
            if len(tokens) == 1:
                path = '/'
            else:
                path = tokens[1]
            if not self.dir_already_exist(path):
                conn.sendall(f'Invalid path'.encode())
            elif not self.is_directory(path):
                conn.sendall(f'{path} Not a directory!!'.encode())
            else:
                files = metadata_server.metadata[path]["files"]
                dirs = metadata_server.metadata[path]["sub_dir"]
                objects = '\n'.join(dirs+files)
                conn.sendall(objects.encode())
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


