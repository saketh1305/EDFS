import socket
import platform
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.box import ROUNDED

console = Console()

def welcome():
    welcome_message = r"""
      _______    _____     _____    _____ 
     |  _____|  |  __ \   |  ___|  / ____|  
     | |___     | |  | |  | |__   | (___
     |  ___|    | |  | |  |  __|   \___ \
     | |_____   | |__| |  | |      ____) |
     |_______|  |_____/   |_|     |_____/     Emulating HDFS version 1.0.0

    Using Python version {python_version}
    """.format(python_version=platform.python_version())
    print(welcome_message)

def print_welcome_message():
    welcome_message = '''
Welcome to your EDFS Client!

Type 'help' to see available commands.
'''
    console.print(welcome_message, style='bold yellow')

def show_help():
    table = Table(title='Available Commands', box=ROUNDED)
    table.add_column('Command', style='bold cyan')
    table.add_column('Syntax')
    table.add_column('Description')

    table.add_row('ls', 'ls {dfs_path}','List directory')
    table.add_row('mkdir', 'mkdir {dfs_folder_path}','Make directory')
    table.add_row('cat','cat {dfs_file_path}','Concatenate')
    table.add_row('rmdir', 'rmdir {dfs_folder_path}' ,'Remove directory')
    table.add_row('rm', 'rm {dfs_file_path}','Remove (file)')
    table.add_row('put', 'put {local_source_path} {dfs_destination_path}','Upload file to server')
    table.add_row('get', 'get {dfs_source_path} {local_destination_path}','Download file from server')


    table.add_row('help', 'help','Show this help message')
    table.add_row('exit', 'exit','Exit the server')

    console.print(table)


class DFSClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def execute_command(self, command):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.sendall(command.encode())
            response = s.recv(1024*1024).decode()
            return response


if __name__ == '__main__':
    welcome()
    print_welcome_message()
    client = DFSClient('localhost', 6000)
    while True:
        command = input('> ')
        if not command:
            continue
        elif command == 'help':
            show_help()
        elif command == 'exit':
            console.print('Goodbye!', style='bold green')
            break
        else:
            response = client.execute_command(command)
            console.print(response, style = "bold yellow")

