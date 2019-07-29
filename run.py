# -*- coding: utf-8 -*-
"""
Created on Fri May  3 16:04:52 2019

@author: demerss1
"""
import wsgiserver
from myApp.app import app


if __name__ == "__main__":
    server = wsgiserver.WSGIServer(app, port=80, host='0.0.0.0')
    server.start()
