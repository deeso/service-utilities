'''
 Copyright 2011 Adam Pridgen <adam.pridgen@thecoverofnight.com>

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at
      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.

@author: Adam Pridgen <adam.pridgen@thecoverofnight.com>
'''
from socket import *
from time import sleep
import struct
import sys
import traceback


HEX = set([i for i in 'abcdef1234567890'])
ishexdigit = lambda x : sum([i in HEX for i in x.lower()]) == len(x)


class Socks5Socket(object):
    REASONS = {0: 'succeeded',
               1: 'general SOCKS server failure',
               2: 'connection not allowed by ruleset',
               3: 'Network unreachable',
               4: 'Host unreachable',
               5: 'Connection refused',
               6: 'TTL expired',
               7: 'Command not supported',
               8: 'Address type not supported'}

    def __init__(self, host, port, timeout=2):
        '''
        Socks5 proxy requires a host and port
        the timeout is used by the socket to timeout if no data
        is sent or recieved
        '''
        self._host = host
        self._port = port
        self._timeout = timeout

    def open_socks5_connection(self):
        '''
        create and return a Socks5 connection to the
        caller.  This method performs the handshake to establish
        the connection to the socks5 proxy
        '''
        s = None
        try:
            s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
        except:
            sleep(4)
            s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)

        s.connect((self.host, self.port))
        # send socks5 auth negotiation
        s.send("\x05\x01\x00")
        r = s.recv(3)
        if r[0] != "\x05":
            print("Fail")
            raise Exception("Bad Socks Proxy Value: %02x" % ord(r))
        if r[1] != "\x00":
            print("Fail")
            raise Exception("Bad Socks Proxy Auth Value: %02x" % ord(r))
        return s

    @classmethod
    def get_host_port(cls, host, port):
        '''
        Klass method that will create the string for the host & port
        that  will be used to connect to a remote host through the
        socks5 proxy
        '''
        if cls.check_if_ip(host):
            return '\x01'+inet_aton(host) + struct.pack('>H', port)
        nlen = struct.pack('>B', len(host))
        return '\x03' + nlen + host + struct.pack('>H', port)

    @classmethod
    def get_ip_resolution_req(cls, ipaddr):
        '''
        create an IP resolution request
        '''
        # [SOCKS5 | PTR_RESOLVE | RESERVED | IPV4 | IPV4_BYTES | PORT]
        req = "\x05\xF1\x00" + cls.get_host_port(ipaddr, 0)
        ip = inet_aton(ipaddr)
        req = req + (ip + "\x00\x00")
        return req

    @classmethod
    def get_name_resolution_req(cls, name):
        '''
        create the name string for a DNS resolution through the socks5
        proxy
        '''
        # [SOCKS5 | NAME_LOOKUP | RESERVED | NAME_USED | LEN | NAME | PORT]
        req = "\x05\xF0\x00" + cls.get_host_port(name, 0)
        return req

    def connect(self, host, port=80):
        '''
        establish a socket connection to the specified host and
        port through the socks proxy.  return the proxy  socket
        prepared for data so be sent.
        '''
        # [SOCKS5 | PTR_RESOLVE | RESERVED | REVERSE_LOOKUP]
        req = "\x05\x01\x00" + self.get_host_port(host, port)
        s = self.open_socks5_connection()
        s.send(req)
        data = s.recv(1024)
        return (data, s)

    def resolve_ip(self, ipaddr, timeout=3):
        '''
        resolve an ip address through the proxy.  I am not
        sure what the point of this is, but I wrote a while ago
        '''
        sock = self.open_socks5_connection()
        req = self.build_socks5_ip_resolution_req(ipaddr)
        sock.send(req)
        resp = sock.recv(1024)
        if resp[1] == "\x00":
            nlen = ord(resp[4])
            name = resp[5:5+nlen]
            return 0, name
        else:
            return ord(resp[1]), None

    def resolve_name(self, name):
        '''
        resolve the DNS name of a host through the
        tor proxy
        '''
        sock = self.open_socks5_connection()
        req = self.get_name_resolution_req(name)
        sock.send(req)
        resp = sock.recv(1024)
        if resp[1] == "\x00":
            ip = inet_ntoa(resp[4:-2])
            return 0, ip
        else:
            return ord(resp[1]), None

    @classmethod
    def check_if_ip(cls, ip):
        '''
        hackish way to see if something is an ip address,
        by seeing if inet_aton will throw an exception on the call
        '''
        try:
            inet_aton(ip)
            return True
        except:
            return False

    def send_recv_http_request(self, host, port, data):
        '''
        Opens up a socks5 connection through the proxy, and then
        sends the HTTP request and then recieve the http response.
        The method will handle Responses with a specified Content-Length
        and responses that use chunked transfer encoding
        on an error, the data returned is the exception that occurrrd
        '''
        result, sock = None, None
        try:
            result, sock = self.connect(host, port)
        except:
            tb = traceback.format_exc(sys.exc_info())
            resp = "FAILED: "+tb
            return (-1, resp)

        if len(result) < 1 or result[1] != '\x00':
            resp = "FAILED: Socks5 proxy failed for unknown reason"
            return (-1, resp)

        # sock.settimeout(self._timeout)
        sock.send(data)
        resp = ''
        transfer_encoding = False
        transfer_encoding_cnt = 0
        content_length_specified = False
        completed_response_header = False
        content_length_cnt = 0
        default_read = 1024
        buffer = ''
        while True:
            try:
                t = sock.recv(default_read)
                if t == '':
                    break
                # has the response header been fully read yet?
                if not completed_response_header and t.find('\r\n\r\n') == -1:
                    resp = resp + t
                    t = ''
                    continue
                elif not completed_response_header:
                    # once we encounter a complete header, we need to append the previously
                    # seen data and parse it because it might have valuable information in there
                    t = resp + t
                    resp = ''
                    completed_response_header = True

                if not content_length_specified and not transfer_encoding:
                    if (t.find('Transfer-Encoding:') > -1 and \
                        t.find('chunked') > -1) and \
                        not transfer_encoding:
                        transfer_encoding = True
                        d = t.split("\r\n\r\n")
                        resp = resp + d[0] + "\r\n\r\n"
                        if d > 1:
                            t = "\r\n\r\n".join(d[1:])
                        else:
                            t = ''
                            continue
                elif t.find('Content-Length:') > -1 and \
                     not content_length_specified and \
                     not transfer_encoding:
                        content_length_specified = True
                        d = t.split("\r\n\r\n")
                        resp = resp + d[0] + "\r\n\r\n"
                        content_length_cnt = int(t.split('Content-Length: ')[1].split('\r\n')[0])
                        t = d[1]

                if transfer_encoding:
                    transfer_encoding_cnt, return_data, complete, buffer = self.parse_transfer_encoding(transfer_encoding_cnt, buffer + t)
                    resp = resp + return_data
                    if transfer_encoding_cnt <= 0:
                        default_read = 1024
                    else:
                        default_read = transfer_encoding_cnt

                    if complete:
                        break
                elif content_length_specified:
                    content_length_cnt, return_data, complete = self.parse_content_length(content_length_cnt, t)
                    resp = resp + return_data
                    default_read = content_length_cnt
                    if complete:
                        break
                    if default_read == 0:
                        default_read = 1024
                else:
                    resp = resp + t

                if not transfer_encoding and t.find("\r\n\r\n") > -1:
                    break
                t = ""
            except:
                # explicitly indicate error in the proxy
                tb = traceback.format_exc(sys.exc_info())
                resp = "FAILED: "+tb
                break
        sock.close()
        return (0, resp)

    def parse_transfer_encoding(self, pending_data_cnt, data):
        '''
        parse a transfer encoded HTTP response message.
        Basically split on the \r\n (not sure if thats legal) and then
        either parse the payload length or accumulate return data with \r\n

        pending_data_cnt:  amount of data that is still pending between requests
        data: data from HTTP server to be parsed

        '''

        return_data = ''
        complete = False

        while True:
            if data.find('0\r\n') == 0:
                return_data = return_data + data
                data = ''
                complete = True
                break
            elif pending_data_cnt == 0 and (data.find('\r\n') > -1):
                p = data.split('\r\n')[0]

                if len(data.split('\r\n')) > 1:
                    data = data[len(p)+2:]
                    return_data = return_data + p + '\r\n'
                else:
                    data = data[len(p):]
                    return_data = return_data + p
                # p could be in the middle of the request header
                if (ishexdigit(p)):
                    pending_data_cnt = int(p, 16)
                else:
                    continue

                # this is necessary because 0 can be represented
                # as 00000000, and the above will not catch it
                # that is just used as an easy at times out
                if pending_data_cnt == 0:
                    complete = True
                    break

            if  pending_data_cnt > 0 and pending_data_cnt < len(data) +2:
                return_data =  return_data + data[:pending_data_cnt+2]
                pending_data_cnt = pending_data_cnt - len(data)
                data = data[pending_data_cnt+2:]
                if pending_data_cnt < 0:
                    pending_data_cnt = 0
            else:
                break

        return pending_data_cnt, return_data, complete, data

    def parse_content_length(self, pending_data_cnt, data):
        '''
        parse a content length HTTP response message.
        Basically split on the \r\n (not sure if thats legal) and then
        either parse the payload length or accumulate return data with \r\n

        pending_data_cnt:  amount of data that is still pending between requests
        data: data from HTTP server to be parsed

        '''

        return_data = ''
        complete = False
        pending_data_cnt -= len(data)
        return_data =  return_data + data
        complete = pending_data_cnt <= 0
        return pending_data_cnt, return_data, complete
