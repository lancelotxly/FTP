# -*- coding: utf-8 -*-
__author__ = 'xzq'

import socketserver
import json
import configparser
import os
from config import settings

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

class ServerHandler(socketserver.BaseRequestHandler):
    def handle(self):
        while True:
            data = self.request.recv(1024).strip()
            data = json.loads(data.decode('utf8'))
            '''
            'action':'auth'
            'username':'xzq'
            'password':'123'
            '''
            # 反射分发任务
            if data.get('action'):
                if hasattr(self,data.get('action')):
                    func = getattr(self,data.get('action'))
                    func(**data)
                else:
                    print('Can\'t find cmd')
            else:
                print('Invalid cmd')

    # 登录验证
    def auth(self,**data):
        username = data['username']
        password = data['password']
        username = self._authenticate(username,password)
        if username:
            self._send_response(254)
        else:
            self._send_response(253)

    def _authenticate(self, username, password):
        cfg = configparser.ConfigParser()
        cfg.read(settings.ACCOUNT_PATH)

        if username in cfg.sections():
            if cfg[username]['Password'] == password:
                self.username = username
                self.mainPath = os.path.join(settings.BASE_DIR, 'home', self.username)
                print('Pass authentication')
                return username

    def _send_response(self,state_code):
        response = {
            'status_code':state_code
        }
        self.request.sendall(json.dumps(response).encode('utf-8'))

    def put(self,**data):
        filename = data.get('filename')
        filesize = data.get('filesize')
        target_path = data.get('target_path')
        has_received = 0

        abs_path = os.path.join(self.mainPath,target_path,filename)
        ###########################################################
        if os.path.exists(abs_path):
            has_file_size = os.stat(abs_path).st_size

            if has_file_size < filesize:
                # 断点续传
                self.request.sendall('800'.encode('utf-8'))
                choice = self.request.recv(1024).decode('utf-8')
                if choice == 'Y':
                    self.request.sendall(str(has_file_size).encode('utf-8'))
                    has_received += has_file_size

                    f = open(abs_path,'ab')
                else:
                    f = open(abs_path,'wb')

            else:
                # 文件完整
                self.request.sendall('801'.encode('utf-8'))
                return

        else:
            self.request.sendall('802'.encode('utf-8'))
            f = open(abs_path, 'wb')


        while has_received < filesize:
            try:
                data = self.request.recv(1024)
                f.write(data)
                has_received += len(data)

            except Exception as e:
                print(e)
                break
        f.close()

    def ls(self,**data):
        file_list = os.listdir(self.mainPath)
        file_str = '\n'.join(file_list)
        if not len(file_list):
            file_str = '<empty dir>'
        self.request.sendall(file_str.encode('utf-8'))

    def cd(self, **data):
        dirname =data.get('dirname')
        if dirname == '..':
            self.mainPath = os.path.dirname(self.mainPath)
        else:
            self.mainPath = os.path.join(self.mainPath,dirname)

        self.request.sendall(self.mainPath.encode('utf-8'))

    def mkdir(self,**data):
        dirname = data.get('dirname')
        path = os.path.join(self.mainPath,dirname)
        if not os.path.exists(path):
            if '\\' in dirname:
                os.makedirs(path)
            else:
                os.mkdir(path)
            self.request.sendall('create success'.encode('utf-8'))
        else:
            self.request.sendall('dirname exist'.encode('utf-8'))