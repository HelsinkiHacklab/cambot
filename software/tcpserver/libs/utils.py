import binascii, hmac, hashlib

def create_session_key(lenght=16):
    try:
        from random import SystemRandom as Random
    except ImportError, e:
        from random import Random
    r_instance = Random()
    r_instance.jumpahead()
    # According to http://skymind.com/~ocrow/python_string/ list comprehension is the best way to do string concats like this one
    bytes = ''.join([chr(r_instance.randint(0,255)) for num in xrange(lenght)])
    return bytes

def hex_encode(input_str):
    return binascii.hexlify(input_str)

def hex_decode(input_str):
    return binascii.unhexlify(input_str)
    try:
        return binascii.unhexlify(input_str)
    except TypeError, e:
        return False

class hmac_wrapper:
    def __init__(self, hmac_key):
        self.hmac_key = hmac_key
    
    def sign(self, message):
        h = hmac.new(self.hmac_key, message, hashlib.sha1)
        return message + "\t" + h.hexdigest() 

    def verify_data(self, data):
        sent_hash = hex_decode(data[-40:])
        message = data[:-41]
        h = hmac.new(self.hmac_key, message, hashlib.sha1)
        if sent_hash != h.digest():
            return False
        return message

def utcoffset():
    import datetime
    return datetime.datetime.now() - datetime.datetime.utcnow()

def utcstamp():
    """Helper fuction to return current UTC timestamp as datime"""
    import datetime
    return datetime.datetime.utcnow()



if __name__ == "__main__":
    print hex_encode(create_session_key())


