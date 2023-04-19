from flask import Flask, render_template, request, jsonify, send_from_directory, make_response
import os
import json
from werkzeug.utils import secure_filename
from DFSclient import DFSClient

app = Flask(__name__)

def process_directory(old_fs, path):
    dir_info = old_fs[path]
    new_fs = {
        "path": path,
        "type": "directory",
        "content": [] 
    }

    for file in dir_info["files"]:
        file_path = f"{path}/{file}" if path != "/" else f"{path}{file}"
        new_fs["content"].append({
            "path": file_path,
            "type": "file",
            "size": old_fs[file_path]["size"],
            "partitions": old_fs[file_path]["blocks"]
        })

    for sub_dir in dir_info["sub_dir"]:
        sub_dir_path = f"{path}/{sub_dir}" if path != "/" else f"{path}{sub_dir}"
        new_fs["content"].append(process_directory(old_fs, sub_dir_path))

    return new_fs


@app.route('/hi')
def index():
    with open("metadata.json") as f:
        metadata_file_structure_ = json.load(f)
    file_structure = process_directory(metadata_file_structure_, "/")
    return render_template('file_explorer.html', file_structure=json.dumps(file_structure))

@app.route('/get_replica_content')
def get_replica_content():
    replica_path = request.args.get('replica_path')
    if not replica_path:
        return 'Error: replica_path not provided', 400

    try:
        with open(replica_path, 'r') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return f'Error: File not found at {replica_path}', 404
    except Exception as e:
        return f'Error: {str(e)}', 500

@app.route('/upload_file', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    filename = secure_filename(file.filename)
    source_path = os.path.join("upload_files",filename)
    destination_path = request.form.get('folder_path')+"/"+filename
    file.save(source_path)
    client = DFSClient('localhost', 6000) 
    command = "put "+ source_path + " " + destination_path
    response = client.execute_command(command)
    return response,200

@app.route('/download_file')
def download_file():
    file_path = request.args.get('path')
    file_name = os.path.basename(file_path)
    directory = os.path.dirname(file_path)
    with open("metadata.json") as f:
        metadata_file_structure = json.load(f)
    block_paths = metadata_file_structure[file_path]["blocks"]
    data = b''
    for block_path in block_paths:
        with open(block_path[0], 'rb') as f:
            block_data = f.read()
        data += block_data
    with open("./download_files/" + file_name , "w") as f:
        f.write(data.decode())
    directory = os.path.join("download_files","")
    response = make_response(send_from_directory(directory, file_name))
    response.headers['Content-Disposition'] = f'attachment; filename={file_name}'
    return response

if __name__ == '__main__':
    app.run(debug=True)

