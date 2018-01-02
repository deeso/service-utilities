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
from queue import PriorityQueue as _PriorityQueue
from threading import Lock


class List(list):
    '''
    This List class is merely an extension of the list class that guarantees
    locking when ever a write or modification is going to take place on the
    list.  Locks are also placed where critical reads should be considered,
    like in the case of 'count'
    '''

    def __init__(self):
        list.__init__(self)
        self.wlock = Lock()

    def push(self, item):
        self.wlock.acquire()
        try:
            self.append(item)
        finally:
            self.wlock.release()

    def insert_ts(self, item, idx=0):
        self.wlock.acquire()
        try:
            self.insert(idx, item)
        finally:
            self.wlock.release()

    def pop_ts(self, idx=0):
        self.wlock.acquire()
        try:
            return self.pop(idx)
        finally:
            self.wlock.release()

    def append_ts(self, item):
        self.wlock.acquire()
        try:
            self.append(item)
        finally:
            self.wlock.release()

    def remove_ts(self, item):
        self.wlock.acquire()
        try:
            self.remove(item)
        finally:
            self.wlock.release()

    def index_ts(self, item, *args):
        self.wlock.acquire()
        try:
            return self.index(item, *args)
        finally:
            self.wlock.release()

    def reverse_ts(self):
        self.wlock.acquire()
        try:
            self.reverse()
        finally:
            self.wlock.release()

    def sort_ts(self, cmp=None, key=None, reverse=False):
        self.wlock.acquire()
        try:
            self.sort(cmp, key, reverse)
        finally:
            self.wlock.release()

    def count_ts(self, item):
        self.wlock.acquire()
        try:
            return self.count(item)
        finally:
            self.wlock.release()

    def extend_ts(self, iterable):
        self.wlock.acquire()
        try:
            self.extend(iterable)
        finally:
            self.wlock.release()

    def __getitem__(self, *args, **kwargs):
        self.wlock.acquire()
        try:
            return list.__getitem__(self, *args, **kwargs)
        finally:
            self.wlock.release()

    def __getslice__(self, *args, **kwargs):
        self.wlock.acquire()
        try:
            return list.__getslice__(self, *args, **kwargs)
        finally:
            self.wlock.release()

    #def __setitem__(self, *args, **kwargs):
    #    self.wlock.acquire()
    #    try:
    #        return list.__setitem__(self, *args, **kwargs)
    #    finally:
    #        self.wlock.release()

    def __setslice__(self, *args, **kwargs):
        self.wlock.acquire()
        try:
            return list.__setslice__(self, *args, **kwargs)
        finally:
            self.wlock.release()

    def __len__(self, *args, **kwargs):
        self.wlock.acquire()
        try:
            return list.__len__(self, *args, **kwargs)
        finally:
            self.wlock.release()


class PriorityQueue(_PriorityQueue):
    '''
    This PriorityQueue class is merely an extension of the list class that guarantees 
    locking when ever a write or modification is going to take place on the
    list.  Locks are also placed where critical reads should be considered,
    like in the case of 'qsize'
    '''

    def __init__(self, maxsize = 0):
        _PriorityQueue.__init__(self, maxsize)
        self.wlock = Lock()

    def get_ts(self, block=True, timeout=None):
        self.wlock.acquire()
        try:
            return _PriorityQueue.get(self, block=block, timeout=timeout)
        finally:
            self.wlock.release()

    def get_nowait_ts(self):
        self.wlock.acquire()
        try:
            return _PriorityQueue.get_nowait(self)
        finally:
            pass
            self.wlock.release()

    def put_ts(self, item, block=True, timeout=None):
        self.wlock.acquire()
        try:
            _PriorityQueue.put(self, item, block=block, timeout=timeout)
        finally:
            self.wlock.release()

    def put_nowait_ts(self, item):
        self.wlock.acquire()
        try:
            return _PriorityQueue.put_nowait(self, item)
        finally:
            self.wlock.release()

    def qsize_ts(self):
        self.wlock.acquire()
        try:
            return _PriorityQueue.qsize(self)
        finally:
            self.wlock.release()
