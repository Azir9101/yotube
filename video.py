import requests
import os
import re

from time import clock

class Video(object):
    def __init__(self, url, filename):
        self.url = url
        self.filename = filename

    def download(self, path, chunk_size=8*1024):
        path = os.path.normpath(path)
        if os.path.isdir(path):
            filename = "{0}".format(self.filename)
            path = os.path.join(path, self.filename)
    
        if os.path.isfile(path):
            raise OSError('file is already exist on path')
        if isinstance(self.url, list):
            for i in self.url:
                resp = requests.get(self.url, stream=True)
                if resp.ok:
                    break
        else:
            resp = requests.get(self.url, stream=True)
        if not resp.ok:
            print resp.status_code
            return
        with open(path, 'wb') as d_data:
            for chunk in resp.iter_content(chunk_size):
                d_data.write(chunk)
