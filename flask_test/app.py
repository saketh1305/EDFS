from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json

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

with open("metadata.json") as f:
    metadata_file_structure = json.load(f)
file_structure = process_directory(metadata_file_structure, "/")

@app.route('/hi')
def index():
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


if __name__ == '__main__':
    app.run(debug=True)

