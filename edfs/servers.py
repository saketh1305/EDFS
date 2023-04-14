import socket
import json
import os

class MetadataServer:
    def __init__(self, metadata_file):
        self.metadata_file = metadata_file
        try:
            with open(metadata_file, 'r') as f:
                self.metadata = json.load(f)
        except FileNotFoundError:
            self.metadata = {'/' :{
            'type' : "directory",
            'files' : [],
            'sub_dir' : []
        }}
        self.save_metadata()

    def save_metadata(self):
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f)

    def get_block_locations(self, block_path):
        return self.metadata[block_path]['locations']
        
    def get_block_paths(self,file_path):
        return self.metadata[file_path]['blocks']

    def get_file_size(self, file_path):
        if file_path in self.metadata:
            return self.metadata[file_path]['size']
        else:
            return -1

    def add_file(self, file_path, block_paths):
        self.metadata[file_path] = {
            'size': sum(os.path.getsize(bp[0]) for bp in block_paths),
            'blocks': block_paths,
            'type' : "file"
        }
        splits = file_path.split("/")
        if len(splits) > 2:
            parent_dir = "/".join(splits[:-1])
            file_name = file_path.split('/')[-1]
            self.metadata[parent_dir]['files'].append(file_name)
        else:
            parent_dir = "/"
            file_name = file_path.split('/')[-1]
            self.metadata[parent_dir]['files'].append(file_name)
        self.save_metadata()

    def add_dir(self,dfs_dir_path):
        self.metadata[dfs_dir_path] = {
            'type' : "directory",
            'files' : [],
            'sub_dir' : []
        }
        self.save_metadata()

    def remove_dir(self , dfs_dir_path):
        self.metadata.pop(dfs_dir_path)
        splits = dfs_dir_path.split("/")
        if len(splits) > 2:
            parent_dir = "/".join(splits[:-1])
        else:
            parent_dir = "/"
        dir_name = dfs_dir_path.split('/')[-1]
        self.metadata[parent_dir]['sub_dir'].remove(dir_name)
        self.save_metadata()

    def remove_file(self, file_path):
        if file_path in self.metadata:
            for bp in self.metadata[file_path]['blocks']:
                self.metadata[bp]['locations'].remove('')
                if not self.metadata[bp]['locations']:
                    del self.metadata[bp]
            del self.metadata[file_path]
            self.save_metadata()


class DataServer:
    def __init__(self, port):
        self.server_id = port
        self.blocks = {}
        self.block_paths = []
        self.data_dir = f'./data/data_server_{self.server_id}'
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        else:
            self.load_blocks()
        self.metadata_file = "dataserver_metadata.json"
        self.load_metadata()

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', self.server_id))
            s.listen()
            print(f'Data server listening on port {self.server_id}...')
            while True:
                conn, addr = s.accept()
                print(f'Connection from {addr} received')
                threading.Thread(target=self.handle_request, args=(conn,)).start()

    def load_metadata(self):
        with open(self.metadata_file, 'r') as f:
            metadata = json.load(f)
            if str(self.server_id) in metadata:
                self.block_paths = metadata[str(self.server_id)]

    def save_metadata(self):
        metadata = {}
        with open(self.metadata_file, 'r') as f:
            metadata = json.load(f)
        metadata[str(self.server_id)] = self.block_paths
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f)

    def has_block(self, block_path):
        return block_path in self.block_paths
    
    def read_block(self, block_path):
        if block_path in self.blocks:
            return self.blocks[block_path]
        else:
            with open(block_path, 'rb') as f:
                data = f.read()
            self.blocks[block_path] = data
            return data
    def remove_block(self , path):
        self.block_paths.remove(path)
        self.save_metadata()

    def write_block(self, dfs_path,block_id,data):
        dfs_path = dfs_path.replace('/' , "_")
        block_path = f'{self.data_dir}/{dfs_path}.block_{block_id}'
        with open(block_path, 'wb') as f:
            f.write(data)
        self.blocks[block_path] = data
        self.block_paths.append(block_path)
        self.save_metadata()
        return block_path
    
    def load_blocks(self):
        for root, dirs, files in os.walk(self.data_dir):
            for file in files:
                block_path = os.path.join(root, file)
                with open(block_path, 'rb') as f:
                    data = f.read()
                self.blocks[block_path] = data
                self.block_paths.append(block_path)

    def handle_request(self, conn):
        block_path = conn.recv(1024).decode()
        with open(block_path, 'rb') as f:
            data = f.read()
        conn.sendall(data)
        conn.close()