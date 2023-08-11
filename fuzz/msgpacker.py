import struct

class BadEncodingException(Exception):
    pass

class UnsupportedValueException(Exception):
    pass

class encoder:
    def __init__(self):
        self.buf = bytearray()

    def encode_int(self, x):
        if x >= 0:
            if x <= 2**7:
                self.buf.append(x)
            elif x <= 2**8:
                self.buf.append(0xcc)
                self.buf.extend(struct.pack('>B', x))
            elif x <= 2**16:
                self.buf.append(0xcd)
                self.buf.extend(struct.pack('>H', x))
            elif x <= 2**32:
                self.buf.append(0xce)
                self.buf.extend(struct.pack('>L', x))
            elif x <= 2**64:
                self.buf.append(0xcf)
                self.buf.extend(struct.pack('>Q', x))
            else:
                raise UnsupportedValueException(x)
        else:
            if x > -2**5:
                self.buf.extend(struct.pack('>b', x))
            elif x > -2**7:
                self.buf.append(0xd0)
                self.buf.extend(struct.pack('>b', x))
            elif x > -2**15:
                self.buf.append(0xd1)
                self.buf.extend(struct.pack('>h', x))
            elif x > -2**31:
                self.buf.append(0xd2)
                self.buf.extend(struct.pack('>l', x))
            elif x > -2**63:
                self.buf.append(0xd3)
                self.buf.extend(struct.pack('>q', x))
            else:
                raise UnsupportedValueException(x)

    def encode_bool(self, x):
        if x:
            self.buf.append(0xc2)
        else:
            self.buf.append(0xc3)

    def encode_str(self, x):
        sbytes = x.encode('utf-8')
        n = len(sbytes)
        if n <= 2**5:
            self.buf.append(0xa0 + n)
        elif n <= 2**8:
            self.buf.append(0xda)
            self.buf.extend(struct.pack('>B', n))
        elif n <= 2**16:
            self.buf.append(0xd9)
            self.buf.extend(struct.pack('>H', n))
        elif n <= 2**32:
            self.buf.append(0xdb)
            self.buf.extend(struct.pack('>L', len(sbytes)))
        else:
            raise UnsupportedValueException(x)
        self.buf.extend(sbytes)

    def encode_bytes(self, x):
        n = len(x)
        if n <= 2**8:
            self.buf.append(0xc4)
            self.buf.extend(struct.pack('>B', n))
        elif n <= 2**16:
            self.buf.append(0xc5)
            self.buf.extend(struct.pack('>H', n))
        elif n <= 2**32:
            self.buf.append(0xc6)
            self.buf.extend(struct.pack('>L', n))
        else:
            raise UnsupportedValueException(x)
        self.buf.extend(x)

    def encode_dict(self, x):
        n = len(x)
        if n <= 2**4:
            self.buf.append(0x80 + n)
        elif n <= 2**16:
            self.buf.append(0xde)
            self.buf.append(struct.pack('>H', n))
        elif n <= 2**32:
            self.buf.append(0xdf)
            self.buf.extend(struct.pack('>L', n))
        else:
            raise UnsupportedValueException(x)
        for k, v in x.items():
            self.encode(k)
            self.encode(v)

    def encode_none(self, x):
        self.buf.append(0xc0)

    def encode_array(self, x):
        n = len(x)
        if n <= 2**4:
            self.buf.append(0x90 + n)
        elif n <= 2**16:
            self.buf.append(0xdc)
            self.buf.extend(struct.pack('>H', n))
        elif n <= 2**32:
            self.buf.append(0xdd)
            self.buf.extend(struct.pack('>L', n))
        else:
            raise UnsupportedValueException(x)
        for v in x:
            self.encode(v)

    def encode(self, x):
        nonetype = type(None)
        match x:
            case nonetype():
                self.encode_none(x)
            case str():
                self.encode_str(x)
            case bytes():
                self.encode_bytes(x)
            case list() | tuple():
                self.encode_array(x)
            case dict():
                self.encode_dict(x)
            case bool():
                self.encode_bool(x)
            case int():
                self.encode_int(x)
            case _:
                raise UnsupportedValueException(x)

    def get_buf(self):
        return bytes(self.buf)

class decoder:
    def __init__(self, data):
        self.buf = data

    def get(self, n):
        if len(self.buf) < n:
            raise BadEncodingException('not enough data: need', n)
        d = self.buf[:n]
        self.buf = self.buf[n:]
        return d

    def unpack(self, fmt):
        n = struct.calcsize(fmt)
        return struct.unpack(fmt, self.get(n))

    def unpack_one(self, fmt):
        return self.unpack(fmt)[0]

    def decode_uint(self, b, fmt):
        return self.unpack_one(fmt)

    def decode_int(self, b, fmt):
        return self.unpack_one(fmt)

    def decode_bool(self, b):
        if b == 0xc2:
            return True
        else:
            return False

    def decode_str(self, b):
        if 0xa0 <= b < 0xbf:
            strlen = b - 0xa0
        elif b == 0xda:
            strlen = self.unpack_one('>B')
        elif b == 0xd9:
            strlen = self.unpack_one('>H')
        elif b == 0xdb:
            strlen = self.unpack_one('>L')
        else:
            raise BadEncodingException(b)
        sbytes = self.get(strlen)
        try:
            return sbytes.decode('utf-8')
        except UnicodeDecodeError as e:
            raise BadEncodingException(e)

    def decode_bytes(self, b):
        if b == 0xc4:
            blen = self.unpack_one('>B')
        elif b == 0xc5:
            blen = self.unpack_one('>H')
        elif b == 0xc6:
            blen = self.unpack_one('>L')
        else:
            raise BadEncodingException(b)
        return self.get(blen)

    def decode_dict(self, b):
        if 0x80 <= b < 0x8f:
            dlen = b - 0x80
        elif b == 0xde:
            dlen = self.unpack_one('>H')
        elif b == 0xdf:
            dlen = self.unpack_one('>L')
        else:
            raise BadEncodingException(b)
        d = {}
        for _ in range(0, dlen):
            k = self.decode()
            v = self.decode()
            try:
                hash(k)
            except TypeError:
                ## Not a bad encoding, but not representable in Python dict
                raise BadEncodingException('unhashable dict key', k)
            d[k] = v
        return d

    def decode_nil(self, b):
        return None

    def decode_array(self, b):
        if 0x90 <= b < 0x9f:
            alen = b - 0x90
        elif b == 0xdc:
            alen = self.unpack_one('>H')
        elif b == 0xdd:
            alen = self.unpack_one('>L')
        else:
            raise BadEncodingException(b)
        l = []
        for _ in range(0, alen):
            v = self.decode()
            l.append(v)
        return tuple(l)

    def decode_fixint(self, b):
        if b < 0x80:
            return b
        else:
            return b-256

    def decode(self):
        b = self.get(1)[0]
        if 0x00 <= b < 0x7f or 0xe0 <= b < 0xff:
            return self.decode_fixint(b)
        elif b == 0xcc:
            return self.decode_uint(b, '>B')
        elif b == 0xcd:
            return self.decode_uint(b, '>H')
        elif b == 0xce:
            return self.decode_uint(b, '>L')
        elif b == 0xcf:
            return self.decode_uint(b, '>Q')
        elif b == 0xd0:
            return self.decode_int(b, '>b')
        elif b == 0xd1:
            return self.decode_int(b, '>h')
        elif b == 0xd2:
            return self.decode_int(b, '>l')
        elif b == 0xd3:
            return self.decode_int(b, '>q')
        elif b in (0xc2, 0xc3):
            return self.decode_bool(b)
        elif 0xa0 <= b < 0xbf or b in (0xd9, 0xda, 0xdb):
            return self.decode_str(b)
        elif b in (0xc4, 0xc5, 0xc6):
            return self.decode_bytes(b)
        elif 0x80 <= b < 0x8f or b in (0xde, 0xdf):
            return self.decode_dict(b)
        elif 0x90 <= b < 0x9f or b in (0xdc, 0xdd):
            return self.decode_array(b)
        elif b == 0xc0:
            return self.decode_nil(b)
        else:
            raise BadEncodingException('unhandled type', b)
