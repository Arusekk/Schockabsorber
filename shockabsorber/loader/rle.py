import pyglet.image

def bytes_to_image(image_data, clut=None):
    if image_data==None: return None
    (width, height, fullwidth, bpp, pixdata) = image_data
    pixdata = bytearray(pixdata)
    if len(pixdata) < fullwidth*height:
        print(len(pixdata), fullwidth*height, width*height*bpp//8)
        print("Warning: too short pixel data (%d%%)" % (100*len(pixdata)//(fullwidth*height)))
        pixdata += b'\0'*(fullwidth*height-len(pixdata))
    if clut:
        return make_clut_image(width, height, fullwidth, pixdata, clut, bpp)
    elif bpp == 8:
        return make_8bit_rbg_image(width, height, fullwidth, pixdata)
    elif bpp == 16:
        return make_16bit_rbg_image(width, height, fullwidth, pixdata)
    elif bpp == 32:
        return make_32bit_rbg_image(width, height, fullwidth, pixdata)
    else:
        print("Warning: RLE: Unknown bpp: %d" % bpp)
        return make_greyscale_image(width, height, fullwidth, pixdata)

def bytes_and_mask_to_image(image_data, mask_data):
    if image_data==None: return None
    (width, height, fullwidth, bpp, pixdata) = image_data
    (width2, height2, fullwidth2, bpp2, pixdata2) = mask_data
    #if bpp == 8:
    #    return make_8bit_rbg_image(width, height, fullwidth, pixdata)
    #el
    if bpp == 16 and bpp2 == 8:
        return make_16bit_rbg_masked_image(width,height,fullwidth, width2,height2,fullwidth2, pixdata, pixdata2)
    elif bpp == 32 and bpp2 == 8:
        return make_32bit_rbg_masked_image(width,height,fullwidth, width2,height2,fullwidth2, pixdata, pixdata2)
    else:
        print("Warning: RLE: Unknown bpp: %d / %d" % (bpp,bpp2))
        return make_greyscale_image(width, height, fullwidth, pixdata) # TODO

def make_greyscale_image(width, height, fullwidth, data):
    return pyglet.image.ImageData(width, height, 'I', data, -fullwidth)

clut = bytearray()
# WARNING: this is the windows system palette (code: -101)
# The palette is kinda strange:
# 0..6 is 3-bit reversed BGR
r2, r6 = range(1,-1,-1), range(5,-1,-1)
for b in r2:
    for g in r2:
        for r in r2:
            clut.extend([255*r, 255*g, 255*b])
# 7..10 is: #808080, #a0a0a4, #fffbf0, #fffffe
clut[-3:] = [128]*3 + [160,160,164, 255,251,240]
# 11..225 is a reversed 6x6x6 RGB cube (216-2 colors)
for r in r6:
    for g in r6:
        for b in r6:
            clut.extend([51*r, 51*g, 51*b])
clut[32] -= 1
# 226..245 are all #000001
# 246..249 are #ddd, #a6caf0, #c0dcc0, #c0c0c0
clut[-3:] = [0,0,1]*20 + [221]*3 + [166,202,240, 192,220,192]
# 250..255 is 3-bit reversed half BGR
for b in r2:
    for g in r2:
        for r in r2:
            clut.extend([128*r, 128*g, 128*b])
clut[-24:-21] = [192]*3
clut = bytes(clut)

def make_8bit_rbg_image(width, height, fullwidth, data, clut=clut):
    color_data = b""
    for c in data: # outer white is transparent
        nr = c*3
        color_data += clut[nr:nr+3]
    return pyglet.image.ImageData(width, height, 'RGB', color_data, -3*fullwidth)

def bit_iterator(data):
    for c in data:
        for i in range(7,-1,-1):
            yield (c>>i)&1

def bpp_iterator(data, width, fullwidth, bpp):
    while data:
        no = b = 0
        yc = 0
        for bit in bit_iterator(data[:fullwidth]):
            b=b<<1|bit
            no += 1
            if no != bpp: continue

            yield b
            b = 0
            no = 0
            yc += 1
            if yc == width:
                break
        data = data[fullwidth:]

def make_clut_image(width, height, fullwidth, data, clut, bpp):
    if bpp == 8:
        return make_8bit_rbg_image(width, height, fullwidth, data, clut)
    else:
        return make_8bit_rbg_image(width, height, width, bpp_iterator(data, width, fullwidth, bpp), clut)

scale_table_31_to_255 = map(lambda v: (v*255)//31 , range(32))

def make_16bit_rbg_image(width, height, fullwidth, data):
    color_res = bytearray(3*width*height)
    pos = 0
    for y in range(height):
        row_start = y*fullwidth
        for x in range(width):
            pix_start = row_start + x
            highbits = data[pix_start]
            lowbits  = data[pix_start + width]
            bits = (highbits << 8) | lowbits
            a = bits >> 15
            r = (bits >> 10) & 31
            g = (bits >> 5) & 31
            b = bits & 31
            if a>0: r=31; g=31; b=0
            color_res[pos]   = scale_table_31_to_255[r]
            color_res[pos+1] = scale_table_31_to_255[g]
            color_res[pos+2] = scale_table_31_to_255[b]
            pos += 3
    color_res = str(color_res)
    return pyglet.image.ImageData(width, height, 'RGB', color_res, -3*width)

def make_16bit_rbg_masked_image(width, height, fullwidth, width2,height2,fullwidth2, data, mask):
    color_res = bytearray(4*width*height)
    pos = 0
    for y in range(height):
        row_start = y*fullwidth
        for x in range(width):
            pix_start = row_start + x
            highbits = data[pix_start]
            lowbits  = data[pix_start + width]
            bits = (highbits << 8) | lowbits
            a = bits >> 15
            r = (bits >> 10) & 31
            g = (bits >> 5) & 31
            b = bits & 31
            if a>0: r=31; g=31; b=0
            color_res[pos]   = scale_table_31_to_255[r]
            color_res[pos+1] = scale_table_31_to_255[g]
            color_res[pos+2] = scale_table_31_to_255[b]
            pos += 4

    for y in range(min(height,height2)):
        pos = y*4*width
        row_start = y*fullwidth2
        for x in range(min(width,width2)):
            color_res[pos+3] = mask[row_start + x]
            pos += 4

    color_res = str(color_res)
    return pyglet.image.ImageData(width, height, 'RGBA', color_res, -4*width)

def make_32bit_rbg_image(width, height, fullwidth, data):
    color_res = bytearray(4*width*height)
    pos = 0
    for y in range(height):
        for x in range(width):
            r = data[y*fullwidth + x]
            g = data[y*fullwidth + x + width]
            b = data[y*fullwidth + x + 2*width]
            a = data[y*fullwidth + x + 3*width]
            color_res[pos]   = r
            color_res[pos+1] = g
            color_res[pos+2] = b
            color_res[pos+3] = a
            pos += 4
    color_res = str(color_res)
    return pyglet.image.ImageData(width, height, 'RGBA', color_res, -4*width)

def make_32bit_rbg_masked_image(width, height, fullwidth, width2,height2,fullwidth2, data, mask):
    color_res = bytearray(4*width*height)
    pos = 0
    for y in range(height):
        for x in range(width):
            r = data[y*fullwidth + x]
            g = data[y*fullwidth + x + width]
            b = data[y*fullwidth + x + 2*width]
            a = data[y*fullwidth + x + 3*width]
            color_res[pos]   = r
            color_res[pos+1] = g
            color_res[pos+2] = b
            pos += 4

    for y in range(min(height,height2)):
        pos = y*4*width
        row_start = y*fullwidth2
        for x in range(min(width,width2)):
            color_res[pos+3] = mask[row_start + x] # Or multiply?
            pos += 4

    color_res = str(color_res)
    return pyglet.image.ImageData(width, height, 'RGBA', color_res, -4*width)


