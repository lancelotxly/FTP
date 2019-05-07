# -*- coding: utf-8 -*-
__author__ = 'xzq'

import socket
import optparse
import re
import json
import os
import sys

STATUS_CODE = {
    250: "Invalid cmd format, e.g: {'action':'get','filename':'test.py','size':344}",
    251: "Invalid cmd",
    252: "Invalid auth data",
    253: "Wrong username or password",
    254: "Passed authentication",
    255: "Filename doesn't provided",
    256: "File doesn't exist on server",
    257: "ready to send file",
    258: "md5 verification",

    800: "the file exist, but not enough, is continue?",
    801: "the file exist",
    802: "ready to receive data",

    900: 'md5 validate success'
}

class Client(object):
    def __init__(self):
        op = optparse.OptionParser()
        op.add_option('-s', '--server', dest='server')
        op.add_option('-P', '--port', dest='port')
        op.add_option('-u', '--username', dest='username')
        op.add_option('-p', '--password', dest='password')

        self.options, self.args = op.parse_args()
        self._verify_args()
        self.client = self._make_connection()
        self.mainPath = os.path.dirname(os.path.abspath(__file__))    # 客户端主地址

    # 验证输入ip和port
    def _verify_args(self):
        self._port_validate()
        self._ip_validate()

    def _port_validate(self):
        port = int(self.options.port)
        if port > 0 and port < 65535:
            return True
        else:
            exit('Port should be between 0-65535')

    def _ip_validate(self):
        server = self.options.server
        ip_re = re.compile(r'((2[0-4]\d|25[0-5]|[01]?\d\d?)\.){3}(2[0-4]\d|25[0-5]|[01]?\d\d?$)')
        if ip_re.match(server):
            return
        else:
            exit('IP address invalid')

    # 建立连接
    def _make_connection(self):
        client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client.connect_ex((self.options.server, int(self.options.port)))
        return client

    def run_client(self):
        print('Client is running...')
        if self._authenticate():
            cmd_info = input('[%s]' % self.current_dir).strip()
            cmd_list = cmd_info.split()
            if hasattr(self, cmd_list[0]):                       # 命令分发
                func = getattr(self, cmd_list[0])
                func(*cmd_list)

    # 登录验证
    def _authenticate(self):
        if self.options.username is None or self.options.password is None:
            username = input('username:')
            password = input('password:')
            return self._get_auth_result(username,password)
        return self._get_auth_result(self.options.username, self.options.password)

    def _get_auth_result(self,username,password):
        data = {
            "action":'auth',
            "username":username,
            "password":password
        }
        self.client.send(json.dumps(data).encode('utf-8'))
        response = self._response()
        if response['status_code'] == 254:
            self.username = username
            self.current_dir = username
            print(STATUS_CODE[254])
            return True
        else:
            print(STATUS_CODE[response['status_code']])

    def _response(self):
        data_json = self.client.recv(1024).decode('utf-8')
        data = json.loads(data_json)
        return data

    # put 上传
    def put(self,*cmd_list):
        # put 12.png images
        action, local_path, target_path = cmd_list
        local_path = os.path.join(self.mainPath, local_path)
        filename = os.path.basename(local_path)
        filesize = os.stat(local_path).st_size

        has_sent = 0
        data = {
            "action":"put",
            "filename":filename,
            "filesize":filesize,
            "target_path":target_path
        }
        self.client.send(json.dumps(data).encode('utf-8'))

        ########################################################
        is_exist = self.sock.recv(1024).decode('utf-8')

        if is_exist == '800':
            # 文件不完整
            choice = input('the file exist, but not enough, is continue?[Y/N]').strip()
            if choice.upper() == 'Y':
                self.client.sendall('Y'.encode('utf-8'))
                continue_position = self.client.recv(1024).decode('utf-8')
                has_sent += int(continue_position)
            else:
                self.client.sendall('N'.encode('utf-8'))

        elif is_exist == '801':
            # 文件完全存在
            print('the file exist')
            return

        f = open(local_path,'rb')
        f.seek(has_sent)
        while has_sent < filesize:
            data = f.read(1024)
            self.client.sendall(data)
            has_sent += len(data)
            self._show_progress(has_sent,filesize)

        f.close()

        print('put success!')

    def _show_progress(self,has,total):
        rate = float(has)/float(total)
        rate_num = int(rate*100)
        if rate_num == 100:
            sys.stdout.write('\n')
        else:
            sys.stdout.write('%s%% %s\r' % (rate_num, '#'*rate_num))

    # ls 列出已有文件
    def ls(self,*cmd_list):
        data = {
            'action':'ls'
        }
        self.client.sendall(json.dumps(data).encode('utf-8'))
        data = self.client.recv(1024).decode('utf-8')
        print(data)

    # cd进入文件
    def cd(self,*cmd_list):
        data ={
            'action':'cd',
            'dirname':cmd_list[1]
        }
        self.client.sendall(json.dumps(data).encode('utf-8'))
        data = self.client.recv(1024).decode('utf-8')
        self.current_dir = os.path.basename(data)

    # 创建文件夹
    def mkdir(self,*cmd_list):
        data ={
            'action':'mkdir',
            'dirname':cmd_list[1]
        }
        self.client.sendall(json.dumps(data).encode('utf-8'))
        data = self.client.recv(1024).decode('utf-8')
        print(data)

if __name__ == '__main__':
    c = Client()
    # c.run_client()