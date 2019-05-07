# -*- coding: utf-8 -*-
__author__ = 'xzq'

import optparse,socketserver
from config import settings
from core import server

class AgrvHandler(object):

    def __init__(self):
        self.op  = optparse.OptionParser()
        options, args = self.op.parse_args()     # options = {}, args = []
        self._verify_args(options,args)


    def _verify_args(self,options,args):
        cmd = args[0]
        if hasattr(self,cmd):
            func = getattr(self,cmd)
            func()

    def start(self):
        IP_PORT = settings.IP_PORT
        s = socketserver.ThreadingTCPServer(IP_PORT,server.ServerHandler)
        s.serve_forever()
