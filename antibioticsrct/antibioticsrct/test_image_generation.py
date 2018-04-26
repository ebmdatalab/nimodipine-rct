from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from threading import Thread
import base64
import os
import requests
import socket
import unittest

from django.conf import settings
from django.test import SimpleTestCase

from common import utils


class MockServerRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/page.html':
            self.send_response(requests.codes.ok)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            response_content = b"""
            <html>
             <head>
              <script src='/jquery.min.js'></script>
              <style>
               div {width: 100%; height: 100%}
               #thing1 {background-color:red}
               #thing1 {background-color:green}
              </style>
             </head>
             <div id='thing1'></div>
             <div id='thing2'></div>
            </html>
            """
            self.wfile.write(response_content)
            return
        elif self.path == '/jquery.min.js':
            self.send_response(requests.codes.ok)
            self.send_header('Content-Type', 'text/javascript')
            self.end_headers()
            with open(settings.BASE_DIR + '/antibioticsrct/fixtures/jquery.min.js', 'rb') as f:
                self.wfile.write(f.read())
                return


def get_free_port():
    s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    address, port = s.getsockname()
    s.close()
    return port


def start_mock_server(port):
    mock_server = HTTPServer(('localhost', port), MockServerRequestHandler)
    mock_server_thread = Thread(target=mock_server.serve_forever)
    mock_server_thread.setDaemon(True)
    mock_server_thread.start()


class GenerateImageTestCase(SimpleTestCase):
    def setUp(self):
        port = get_free_port()
        start_mock_server(port)
        self.url = ":%s/page.html" % port
        self.file_path = "/tmp/image.png"
        self.selector = "#thing2"

    def tearDown(self):
        try:
            os.remove(self.file_path)
        except OSError as e:
            import errno
            # We don't care about a "No such file or directory" error
            if e.errno != errno.ENOENT:
                raise

    def test_image_generated(self):
        with self.settings(GRAB_HOST='http://localhost'):
            encoded_image = utils.grab_image(
                self.url, self.file_path, self.selector)
        with open(
                settings.BASE_DIR + '/antibioticsrct/fixtures/'
                'alert-email-image.png', 'rb') as expected:
            self.assertEqual(
                encoded_image,
                base64.b64encode(expected.read()))
