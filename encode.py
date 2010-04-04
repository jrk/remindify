# Base32 encode into a shuffled alphabet
_i2a = [ 's', '5', 'u', 'x', 'n', 'q', '2', 'j', 't', 'y', '4', 'p', 'l',
         'g', 'e', 'r', 'k', '1', 'z', 'a', 'f', 'w', 'h', '3', 'v', 'i',
         '0', 'o', 'b', 'd', 'm', 'c' ]
_a2i = dict( zip( _i2a, range( len( _i2a ) ) ) )

def _encode( x ):
    assert( x > 0 )
    s = ''
    while x:
        s = _i2a[ x & 0b11111 ] + s
        x = x >> 5
    return s

def _decode( s ):
    x = 0
    started = False
    for i in range( len( s ) ):
        if i > 0:
            x = x << 5
        x = x | _a2i[ s[i] ]
    return x


_address_prefix = 'r.'

def address_to_id( addr ):
    assert addr.startswith( _address_prefix )
    return _decode( addr.split( _address_prefix )[-1] )

def id_to_address( id ):
    return _address_prefix + _encode( id )
