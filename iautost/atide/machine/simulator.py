import asyncore
import json
import six
import struct
import base64
import time

HEADER_SIZE = 4

class CPort(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket()
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accepted(self, sock, addr):
        print('Incoming connection from %s' % repr(addr))
        session = CSession(sock)

class CSession(asyncore.dispatcher_with_send):
    def handle_read(self):
        msg = self.recv(8192)
        if msg:
            length, msg = self.unpack(msg)
            print('receive msg:')
            print(msg)
            response = CHandler.handle(msg)
            self.send(response)
    
    def send(self, msg):
        print('send msg:')
        if len(msg) < 100:
            print(msg)
        else:
            print(msg[:100], '...')
        msg = self.pack(msg)
        super(CSession, self).send(msg)
    
    @staticmethod
    def pack(content):
        """ content should be str
        """
        if isinstance(content, six.text_type):
            content = content.encode("utf-8")
        return struct.pack('i', len(content)) + content

    @staticmethod
    def unpack(data):
        """ return length, content
        """
        length = struct.unpack('i', data[0:HEADER_SIZE])
        return length[0], data[HEADER_SIZE:]

class CHandler:
    @staticmethod
    def handle(msg):
        try:
            if isinstance(msg, six.binary_type):
                msg = msg.decode('utf8')
            data = json.loads(msg)
            
            method = data.get('method')
            if method:
                result = CHandler.handle_method(method)
                if method == 'snapshot':
                    time.sleep(0.033)
            else:
                result = 'default response content.'
            response = {
                        "id": data["id"],
                        "result": result
                        }
            
            return json.dumps(response)
        except:
            import traceback
            print(traceback.format_exc())
    
    @staticmethod
    def handle_method(method):
        screen = r'resource/17cy_sketch_t0.jpg'
        widget = r'resource/17cy_sketch_t0.json'
        method_mapping = {
                          'hello': 'welcome',
                          'snapshot': str(base64.b64encode(open(screen, 'rb').read()), encoding='utf8'),
                          'dump': json.loads(open(widget, 'r').read(), encoding='utf8'),
                          'dump1': {
                                   'payload': {
                                               'name': 'Root',
                                               'visible': True,
                                               },
                                   'children': [
                                                {
                                                'payload': {
                                                            'name': 'Audio',
                                                            'text': 'Audio',
                                                            'visible': True,
                                                            'pos': (0.5, 0.5),
                                                            'size': (400, 240),
                                                            'anchorPoint': (0.5, 0.5),
                                                            },
                                                },
                                                ],
                                   },
                          'dump2': {
                                   'payload': {
                                               'name': 'Root',
                                               'visible': True,
                                               'type': 1,
                                               },
                                   'children': [
                                                {
                                                'payload': {
                                                            'name': 'Audio',
                                                            'text': [{'text':'AM'}],
                                                            'visible': True,
                                                            'type': 63,
                                                            'x': 100,
                                                            'y': 100,
                                                            'width': 400,
                                                            'height': 240,
                                                            },
                                                },
                                                ],
                                   },
                          }
        return method_mapping.get(method.lower())

class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return str(obj);
        return json.JSONEncoder.default(self, obj)

print('Listenning...')
server = CPort('0.0.0.0', 5391)
asyncore.loop()
