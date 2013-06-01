
#### Purpose:
# Utilities for binary parsing.
#

import struct

class SeqBuffer:  #------------------------------
    def __init__(self,src, is_little_endian=False):
        self.buf = buffer(src)
        self.offset = 0
        self.is_little_endian = is_little_endian

    def readTag(self):
        tag = self.readBytes(4)
        if self.is_little_endian:
            tag = rev(tag)
        return tag

    def unpack(self,be_fmt, le_fmt=None):
        if le_fmt==None: le_fmt = be_fmt
        if self.is_little_endian:
            fmt = le_fmt
        else:
            fmt = be_fmt
        if isinstance(fmt,str): fmt=struct.Struct(fmt) # sic
        res = fmt.unpack_from(self.buf, self.offset)
        self.offset += fmt.size
        return res

    def unpackString8(self):
        [len] = self.unpack('B')
        str = self.buf[self.offset:self.offset+len]
        self.offset += len
        return str

    def unpackVarint(self):
        d = ord(self.buf[self.offset])
        #print "DB| unpackVarint: %d" % d
        self.offset += 1
        if d<128:
            return d
        else:
            return ((d-128)<<7) | self.unpackVarint()

    def readBytes(self, len):
        bytes = self.buf[self.offset:self.offset+len]
        self.offset += len
        return bytes

    def seek(self,new_offset):
        self.offset = new_offset

    def bytes_left(self):
        return len(self.buf) - self.offset

    def peek_bytes_left(self):
        return self.buf[self.offset:]

    def at_eof(self):
        return self.offset >= len(self.buf)
#--------------------------------------------------

def rev(s):
     return s[::-1]