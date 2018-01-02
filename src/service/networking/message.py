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


import struct
import base64


class BaseMessage(object):
    def __init__(self):
        self._msg_type = 0
        self._msg_id = -1
        self._msg_ts = -1
        self._data = ''
        self._data_len = -1

    def msg_type(self, value=None):
        '''
        get/set the named field.  If a value is provided (other than None),
        the field gets set with this value
        '''
        if value is not None:
            self._msg_type = value
        return self._msg_type

    def msg_id(self, value=None):
        '''
        get/set the named field.  If a value is provided (other than None),
        the field gets set with this value
        '''
        if value is not None:
            self._msg_id = value
        return self._msg_id

    def msg_ts(self, value=None):
        '''
        get/set the named field.  If a value is provided (other than None),
        the field gets set with this value
        '''
        if value is not None:
            self._msg_ts = value
        return self._msg_ts

    def data_len(self):
        '''
        get/set the named field.  If a value is provided (other than None),
        the field gets set with this value
        '''
        return len(self._data)

    def data(self, value=None):
        '''
        get/set the named field.  If a value is provided (other than None),
        the field gets set with this value
        '''
        if value is not None:
            self._data = value
        return self._data

    def append(self, value=''):
        '''
        get/set the named field.  If a value is provided (other than None),
        the field gets set with this value
        '''
        self._data += value

    def is_complete(self):
        # Note: self_data_len will only be -1 if this message is
        # constructed as a complete message
        return self._data_len == -1 or self.data_len() == self._data_len

    def remaining_data(self):
        if self._data_len == -1:
            return 0
        return self._data_len - len(self._data)


class Message(BaseMessage):
    def __init__(self, msg_type, msg_id, msg_ts, data):
        '''
        msg_type: message network type code
        msg_id: message identifier
        data: message data

        Standard message format:

        | 4B | 4B | 4B | 4B | data|
        |    |    |    |    \ Data payload for the message (base64 Encoded)
        |    |    |    \ Len. of Base64 encoded data
        |    |    \ Message Time stamp (4-byte Big Endian)
        |    \ Message ID (4-byte Big Endian)
        \  Message Type (4-byte Big Endian)
        '''

        BaseMessage.__init__(self)
        self._msg_type = msg_type
        self._msg_id = msg_id
        self._msg_ts = msg_ts
        self._data = data

    def serialize(self):
        '''
        Turnd the message into a string
        '''
        d = base64.encodestring(self._data)
        data = ''
        data += struct.pack(">I", self._msg_id)
        data += struct.pack(">I", self._msg_ts)

        data += struct.pack(">I", self._msg_type)
        data += struct.pack(">I", len(d))
        data += d
        return data

    @classmethod
    def deserialize(cls, data_str):
        '''
        Extract the message from a string
        '''
        msg_id = struct.unpack(">I", data_str[0:4])[0]
        msg_ts = struct.unpack(">I", data_str[4:8])[0]
        msg_type = struct.unpack(">I", data_str[8:12])[0]
        data_len = struct.unpack(">I", data_str[12:16])[0]
        data = data_str[16:16+data_len]
        return Message(msg_type, msg_id, msg_ts, data)

    @classmethod
    def fromIncompleteMsg(cls, msg):
        '''
        Create the messsage from an Incomplete message
        '''
        msg_id = msg.msg_id()
        msg_ts = msg.msg_ts()
        msg_type = msg.msg_type()
        data = base64.decodestring(msg.data())
        return Message(msg_type, msg_id, msg_ts, data)


class IncompleteMessage(BaseMessage):
    EXPECTED_INIT_DATA = 16

    def __init__(self, data):
        '''
        Class is used to build up a message in a stateful fashion.  At a minimum,
        the initial size of the string should be at least 16 bytes long (4 * 4B) to
        accomodate parsing the following message format:

        Standard message format:

        | 4B | 4B | 4B | 4B | data|
        |    |    |    |    \ Data payload for the message (base64 Encoded)
        |    |    |    \ Len. of Base64 encoded data
        |    |    \ Message Time stamp (4-byte Big Endian)
        |    \ Message ID (4-byte Big Endian)
        \  Message Type (4-byte Big Endian)

        '''
        BaseMessage.__init__(self)
        if len(data) < self.EXPECTED_INIT_DATA:
            raise Exception("Expected the initial data string to be 16 byte long, but got %d" % len(data))
        self.handle_initial_data(data)

    def handle_initial_data(self, data_str):
        self._msg_id = struct.unpack(">I", data_str[0:4])[0]
        self._msg_ts = struct.unpack(">I", data_str[4:8])[0]
        self._msg_type = struct.unpack(">I", data_str[8:12])[0]
        self._data_len = struct.unpack(">I", data_str[12:16])[0]
        if len(data_str) > self.EXPECTED_INIT_DATA:
            self._data = data_str[self.EXPECTED_INIT_DATA:]
