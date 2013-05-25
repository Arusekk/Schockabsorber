#!/usr/bin/python

import sys
import struct

class SeqBuffer:  #------------------------------
    def __init__(self,src):
        self.buf = buffer(src)
        self.offset = 0

    def unpack(self,fmt):
        if isinstance(fmt,str): fmt=struct.Struct(fmt) # sic
        res = fmt.unpack_from(self.buf, self.offset)
        self.offset += fmt.size
        return res

    def at_eof(self):
        return self.offset >= len(self.buf)
#--------------------------------------------------

class MmapEntry:  #------------------------------
    def __init__(self,tag,size,offset):
        self.tag = tag
        self.size = size
        self.offset = offset

    def __repr__(self):
        return('MmapEntry(%s @%d+%d)' % (self.tag,self.offset,self.size))

    def read_from(self,file):
        file.seek(self.offset)
        xheader = file.read(8)
        [tag,size] = struct.unpack('!4si', xheader)
        if tag != self.tag:
            raise ("section header is actually %s, not %s as expected" % (tag, self.tag))
        return file.read(self.size)
#--------------------------------------------------

class MmapSection: #------------------------------
    def __init__(self):
        self.entries = []

    def __repr__(self):
        return repr(self.entries)

    def __getitem__(self,idx):
        return self.entries[idx]

    def find_entry_by_tag(self, tag):
        for e in self.entries:
            if e.tag == tag:
                return e
        return None

    @staticmethod
    def parse(blob):
        buf = SeqBuffer(blob)
        [v1,v2,nElems,nUsed,junkPtr,v3,freePtr] = buf.unpack('>HHiiiii')
        print("mmap header: %s" % [v1,v2,nElems,nUsed,junkPtr,v3,freePtr])

        res = MmapSection()
        while not buf.at_eof():
            [tag, size, offset, w1,w2, link] = buf.unpack('>4sIIhhi')
            #print("mmap entry: %s" % [tag, size, offset, w1,w2, link])
            res.entries.append(MmapEntry(tag, size, offset))
        return res
#--------------------------------------------------


class KeysSection: #------------------------------
    def __init__(self):
        self.entries = []

    def __repr__(self):
        return repr(self.entries)

    @staticmethod
    def parse(blob):
        buf = SeqBuffer(blob)
        [v1,v2,nElems,v3] = buf.unpack('>HHii')
        print("KEY* header: %s" % [v1,v2,nElems,v3])

        res = KeysSection()
        while not buf.at_eof():
            [section_id, cast_id, tag] = buf.unpack('>ii4s')
            res.entries.append(dict(section_id=section_id,
                                    cast_id=cast_id,
                                    tag=tag))
        return res
#--------------------------------------------------

class CastTableSection: #------------------------------
    def __init__(self):
        self.entries = []

    def __repr__(self):
        return repr(self.entries)

    @staticmethod
    def parse(blob):
        buf = SeqBuffer(blob)
        res = CastTableSection()
        while not buf.at_eof():
            (item,) = buf.unpack('>i')
            res.entries.append(item)
        return res
#--------------------------------------------------

class CastMember: #------------------------------
    def __init__(self, section_nr, type):
        self.media = {}
        self.type = type
        self.section_nr = section_nr

    def __repr__(self):
        return "<CastMember (@%d) type=%d media=%s>" % \
            (self.section_nr, self.type, self.media.keys())

    def add_media(self,tag,data):
        self.media[tag] = data

    @staticmethod
    def parse(blob,snr):
        buf = SeqBuffer(blob)
        (typ,) = buf.unpack('>i')
        res = CastMember(snr,typ)
        return res
#--------------------------------------------------


def load_file(filename):
    with open(filename) as f:
        xheader = f.read(12)
        [magic,size,tag] = struct.unpack('!4si4s', xheader)
        if not (magic=="RIFX" and tag=="MV93"): raise "bad file type"
        mmap = find_and_read_section(f, "mmap")
        cast_table = create_cast_table(f,mmap)
        print "cast_table: %s" % cast_table
        print "OK"

def find_and_read_section(f, tag_to_find):
    while True:
        xheader = f.read(8)
        [tag,size] = struct.unpack('!4si', xheader)
        print("  tag=%s" % tag)
        if tag==tag_to_find:
            blob = f.read(size)
            return MmapSection.parse(blob)
        else:
            f.seek(size, 1)

def create_cast_table(f,mmap):
    # Read the relevant table sections:
    keys_e = mmap.find_entry_by_tag("KEY*")
    cast_e = mmap.find_entry_by_tag("CAS*")
    cast_list_section = CastTableSection.parse(cast_e.read_from(f))
    keys_section      = KeysSection.parse(keys_e.read_from(f))

    # Create cast table with basic cast-member info:
    def section_nr_to_cast_member(nr):
        if nr==0: return None
        cast_section = mmap[nr].read_from(f)
        res = CastMember.parse(cast_section,nr)
        return res
    cast_table = map(section_nr_to_cast_member, cast_list_section.entries)

    # Calculate section_nr -> cast-table mapping:
    aux_map = {}
    for cm in cast_table:
        if cm != None:
            aux_map[cm.section_nr] = cm

    # Add media info:
    for e in keys_section.entries:
        cast_id = e["cast_id"]
        if cast_id != 0 and cast_id != 1024:
            # Find the cast member to add media to:
            cast_member = aux_map[cast_id]

            # Read the media:
            media_section_id = e["section_id"]
            media_section_e = mmap[media_section_id]
            media_section = media_section_e.read_from(f)

            # Add it:
            tag = e["tag"]
            #print "DB| adding media %s to cast_id %d" % (tag,cast_id)
            cast_member.add_media(tag, media_section)

    return cast_table

load_file(sys.argv[1])
