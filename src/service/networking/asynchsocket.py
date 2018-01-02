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
from threading import Timer, Lock
from crawler.util.ThreadSafe import List
from crawler.networking.message import IncompleteMessage, Message
import sys


class MessageTCPSocket(object):

    def __init__(self, host, port, logger=None,
                 sock=None, poll_time=.25, is_server=False):
        self._sock = sock
        self._host = host
        self._port = port
        self.logger = logger
        self._is_server = is_server
        if sock is None:
            self._sock = self.get_socket(host, port)
        elif not is_server and sock is not None:
            self._host, self._port = self._sock.getpeername()

        self._sock.setblocking(1)

        self._handlers = {}
        self._current_recv_msg = None
        self._current_send_msg = None
        self._current_send_data = ""
        self._current_recv_data = ""
        self._recv_queue = List()
        self._send_queue = List()
        self._accept_queue = List()

        self._poll_time = poll_time
        self._send_poll = None
        self._recv_poll = None
        self._accept_poll = None
        self._continue_send = False
        self._continue_recv = False
        self._continue_accept = False
        self._adjust_time = Lock()

    def log(self, msg):
        if self.logger is not None:
            self.logger.log(msg)

    def register_handler(self, event, handler):
        '''
        register a handler with this instance.
        event: string event (e.g. accept, send, recv)
        handler: handler for the event which at the very least takes this instance
        '''
        self._handlers[event] = handler

    def sock_check(self):
        try:
            self._sock.send("")
            return True
        except:
            self.shutdown()
            return False

    def getpeername(self):
        return self._sock.getpeername()

    def check_reset_send(self):
        self._adjust_time.acquire()
        try:
            if self._continue_send and self.sock_check():
                self._send_poll = Timer(self._poll_time, self.send)
                self._send_poll.start()
            else:
                self._send_poll = None
        finally:
            self._adjust_time.release()

    def check_reset_accept(self):
        self._adjust_time.acquire()
        try:
            if self._continue_accept:
                self._accept_poll = Timer(self._poll_time, self.accept)
                self._accept_poll.start()
            else:
                self._accept_poll = None
        finally:
            self._adjust_time.release()

    def check_reset_recv(self):
        self._adjust_time.acquire()
        try:
            if self._continue_recv:
                self._recv_poll = Timer(self._poll_time, self.recv)
                self._recv_poll.start()
            else:
                self._recv_poll = None
        finally:
            self._adjust_time.release()

    def start_send(self):
        self._adjust_time.acquire()
        try:
            self._continue_send = True
            if self._send_poll is None:
                self._send_poll = Timer(self._poll_time, self.send)
                self._send_poll.start()
        finally:
            self._adjust_time.release()

    def stop_send(self):
        self._adjust_time.acquire()
        try:
            self._continue_send = False
            if self._send_poll is not None:
                self._send_poll.cancel()
                self._send_poll = None
        finally:
            self._adjust_time.release()

    def start_accept(self):
        self._adjust_time.acquire()
        try:
            self._continue_accept = True
            if self._accept_poll is None:
                self._accept_poll = Timer(self._poll_time, self.accept)
                self._accept_poll.start()
        finally:
            self._adjust_time.release()

    def stop_accept(self):
        self._adjust_time.acquire()
        try:
            self._continue_accept = False
            if not self._accept_poll is None:
                self._accept_poll.cancel()
                self._accept_poll = None
        finally:
            self._adjust_time.release()

    def start_recv(self):
        self._adjust_time.acquire()
        try:
            self._continue_recv = True
            if self._recv_poll is None:
                self._recv_poll = Timer(self._poll_time, self.recv)
                self._recv_poll.start()
        finally:
            self._adjust_time.release()

    def stop_recv(self):
        self._adjust_time.acquire()
        try:
            self._continue_recv = False
            if not self._recv_poll is None:
                self._recv_poll.cancel()
                self._recv_poll = None
        finally:
            self._adjust_time.release()

    def send_msg(self, msg, instance):
        '''
        top layer instances are adding messages to the queue, to be sent by the send consumer thread
        '''
        self._send_queue.append_ts(msg)

    def recv_msg(self, msg):
        '''
        Add the message to the pending messages queue,
        and call the handler up above this instance.
        '''
        self._recv_queue.append_ts(msg)
        if 'recv' in self._handlers:
            self._handlers['recv'](self)

    def next_recv_msg(self):
        return self._recv_queue.pop_ts(0)

    def has_recv_msg(self):
        return len(self._recv_queue) > 0

    def get_socket(self, host, port):
        '''
        get_socket -> socket
        '''
        s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
        s.connect((host, port))
        return s

    def recv(self):
        '''
        Recv messages from the remote host while there is data to be recieved
        Trigger a handler after recieveing a complete message.  If there is no more data to be
        recieved schedule another polling thread.
        '''

        if self._current_recv_msg is None:
            dlen = IncompleteMessage.EXPECTED_INIT_DATA
            ddata = "1"
            try:
                ddata = self._sock.recv(dlen)
                self._current_recv_data += ddata
                if len(ddata) == 0:
                    self.shutdown()
                    return
                if len(self._current_recv_data) < 16:
                    self.check_reset_recv()
                    return

                self._current_recv_msg = IncompleteMessage(self._current_recv_data)
                self._current_recv_data = ""
            except timeout:
                self.check_reset_recv()
                return
            except:
                # TODO recieved a bad message here, probably perform some error handling
                self._current_recv_msg = None
                self.check_reset_recv()
                self.log(sys.exc_info())
                return

        data = '1'
        while data != '' and not self._current_recv_msg.is_complete():
            try:
                dlen = self._current_recv_msg.remaining_data()
                data = self._sock.recv(dlen)
                self._current_recv_msg.append(data)
            except timeout:
                data = ''

        msg = None

        if self._current_recv_msg.is_complete():
            msg = Message.fromIncompleteMsg(self._current_recv_msg)
            self._current_recv_msg = None
            self.check_reset_recv()
            try:
                self.recv_msg(msg)
            except:
                self.log(sys.exc_info())
            return

        self.check_reset_recv()

    def accept(self):
        '''
        Accept sockets, and if a socket is recieved pass it up to the
        socket owner with this instance.
        '''
        sock, peer = self._sock.accept()
        if "accept" in self.handlers:
            self._accept_queue.append_ts((sock, peer))
            if self._continue_accept:
                self.handlers["accept"](sock, peer, self)
        else:
            # No handler just close the socket
            sock.shutdown()
        if self._continue_accept:
            self.check_reset_accept()

    def send(self):
        '''
        Send messages to the remote host while there are messages enqueued to be
        sent.  Trigger a handler after sending.  If there are no more messages
        schedule another polling thread.
        '''
        while True:
            if len(self._send_queue) > 0 and\
              self._current_send_msg is None:
                msg = self._send_queue.pop_ts(0)
                self._current_send_data = msg.serialize()
            elif len(self._send_queue) == 0 and \
               (self._current_send_data is None or len(self._current_send_data) == 0 ):
                break

            try:
                dlen = self._sock.send(self._current_send_data)
                self._current_send_data = self._current_send_data[dlen:]
                if len(self._current_send_data) == 0:
                    if "send" in self._handlers:
                        msg = self._current_send_msg
                        self._handlers["send"](msg, self)
                    self._current_send_data = ""
                    self._current_send_msg = None
            except timeout:
                self.log("Send method timed out")

        self.check_reset_send()

    def shutdown(self):
        '''
        Stop all the polling threads (e.g. accept, recv, send), and
        if there is an accepting socket, coerce it out of an accept
        state after the polling is terminated.
        Also close down the connection.
        '''

        self.stop_accept()
        self.stop_recv()
        self.stop_send()
        self.log("Stopped all the polling threads")
        self.log("Stopping the socket for %s %d" % (self._host, self._port))
        if self._sock is not None:
            self._sock.shutdown(SHUT_RDWR)
            self._sock.close()
        # stop listening if i am a server trapped in accept
        if self._is_server:
            try:
                self.log("Shutting down the server")
                c = socket(AF_INET, SOCK_STREAM)
                c.connect((self._host, self._port))
                c.send("0")
                c.shutdown(socket.SHUT_RDWR)
                c.close()
                c = None
            except:
                self.log("failed to open the accept")

        self.log("Done shutting down all async sockets")
        self._sock = None


class MessageUDPSocket(MessageTCPSocket):

    def sock_check(self):
        try:
            if self._sock is not None:
                return True
        except:
            return False

    def getpeername(self):
        return None

    def shutdown(self):
        '''
        Stop all the polling threads (e.g. accept, recv, send), and
        if there is an accepting socket, coerce it out of an accept
        state after the polling is terminated.
        Also close down the connection.
        '''

        self.stop_accept()
        self.stop_recv()
        self.stop_send()
        self.log("Stopped all the polling threads")
        self.log("Stopping the socket for %s %d" % (self._host, self._port))
        self.log("Done shutting down all async sockets")
        self._sock = None

    def send(self):
        return self.sendto()

    def sendto(self):
        '''
        Send messages to the remote host while there are messages enqueued to be
        sent.  Trigger a handler after sending.  If there are no more messages
        schedule another polling thread.
        '''
        addr_to = None
        while True:
            if len(self._send_queue) > 0 and\
              self._current_send_msg is None:
                msg, addr_to = self._send_queue.pop_ts(0)
                self._current_send_data = msg.serialize()
            elif len(self._send_queue) == 0 and \
               (self._current_send_data is None or len(self._current_send_data) == 0 ):
                break

            try:
                dlen = self._sock.sendto(self._current_send_data, addr)
                self._current_send_data = self._current_send_data[dlen:]
                if len(self._current_send_data) == 0:
                    if "sendto" in self._handlers:
                        msg = self._current_send_msg
                        self._handlers["sendto"](msg, addr_to, self)
                    self._current_send_data = ""
                    self._current_send_msg = None
            except timeout:
                self.log("Send method timed out")

        self.check_reset_send()

    def accept(self):
        raise Exception("Not implemented")

    def get_socket(self, host, port):
        '''
        get_socket -> socket
        '''
        s = socket(AF_INET, SOCK_DGRAM, IPPROTO_TCP)
        return s

    def recv(self):
        '''
        Recv messages from the remote host while there is data to be recieved
        Trigger a handler after recieveing a complete message.  If there is no more data to be
        recieved schedule another polling thread.
        '''
        if self._current_recv_msg is None:
            dlen = IncompleteMessage.EXPECTED_INIT_DATA
            ddata = "1"
            try:
                ddata = self._sock.recvfrom(dlen)
                self._current_recv_data += ddata
                if len(ddata) == 0:
                    self.shutdown()
                    return
                if len(self._current_recv_data) < 16:
                    self.check_reset_recv()
                    return

                self._current_recv_msg = IncompleteMessage(self._current_recv_data)
                self._current_recv_data = ""
            except timeout:
                self.check_reset_recv()
                return
            except:
                # TODO recieved a bad message here, probably perform some error handling
                self._current_recv_msg = None
                self.check_reset_recv()
                self.log(sys.exc_info())
                return

        data = '1'
        while data != '' and not self._current_recv_msg.is_complete():
            try:
                dlen = self._current_recv_msg.remaining_data()
                data = self._sock.recvfrom(dlen)
                self._current_recv_msg.append(data)
            except timeout:
                data = ''

        msg = None

        if self._current_recv_msg.is_complete():
            msg = Message.fromIncompleteMsg(self._current_recv_msg)
            self._current_recv_msg = None
            self.check_reset_recv()
            try:
                self.recv_msg(msg)
            except:
                self.log(sys.exc_info())
            return

        self.check_reset_recv()
