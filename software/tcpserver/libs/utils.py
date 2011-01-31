import binascii

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

# Naive implementatation
def hex_encode(input_str):
    return binascii.hexlify(input_str)

def hex_decode(input_str):
    return binascii.unhexlify(input_str)
    try:
        return binascii.unhexlify(input_str)
    except TypeError, e:
        return False

if __name__ == "__main__":
    print hex_encode(create_session_key())


