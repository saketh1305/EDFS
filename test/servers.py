import socket
import json

class MetadataServer:
    def __init__(self, metadata_file):
        self.metadata_file = metadata_file
        try:
            with open(metadata_file, 'r') as f:
                self.metadata = json.load(f)
        except FileNotFoundError:
            self.metadata = {}

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
            'size': sum(os.path.getsize(bp) for bp in block_paths),
            'blocks': block_paths
        }
        for bp in block_paths:
            if bp not in self.metadata:
                self.metadata[bp] = {'locations': []}
            self.metadata[bp]['locations'].append('')
        self.save_metadata()

    def remove_file(self, file_path):
        if file_path in self.metadata:
            for bp in self.metadata[file_path]['blocks']:
                self.metadata[bp]['locations'].remove('')
                if not self.metadata[bp]['locations']:
                    del self.metadata[bp]
            del self.metadata[file_path]
            self.save_metadata()

    # def set_block_location(self, block_path, location):
    #     self.metadata[block_path]['locations'].append(location)
    #     self.save_metadata()

class DataServer:
    def __init__(self, port):
        self.port = port

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', self.port))
            s.listen()
            print(f'Data server listening on port {self.port}...')
            while True:
                conn, addr = s.accept()
                print(f'Connection from {addr} received')
                threading.Thread(target=self.handle_request, args=(conn,)).start()

    def handle_request(self, conn):
        block_path = conn.recv(1024).decode()
        with open(block_path, 'rb') as f:
            data = f.read()
        conn.sendall(data)
        conn.close()