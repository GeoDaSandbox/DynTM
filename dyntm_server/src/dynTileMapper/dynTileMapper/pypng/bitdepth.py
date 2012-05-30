def Btoii(byte):
    """
        1001 0101
        0000 1111
       &=========
        0000 0101

        1001 0101
        1111 0000
       &=========
        1001 0000
       >> 4 =====
        0000 1001
    """
    left = (byte & 0xF0) >> 4
    right = byte & 0x0F
    return left, right
def Btoiiii(byte):
    """
    A
        1001 0101
        0000 0011
       &=========
        0000 0001
    B
        1001 0101
        0000 1100
       &=========
        0000 0100
       >> 2 =====
               01
    C
        1001 0101
        0011 0000
       &=========
        0001 0000
       >> 4 =====
               01
    D
        1001 0101
        1100 0000
       &=========
        1000 0000
       >> 6 =====
               10
    """
    A = (byte & 0x03)
    B = (byte & 0x0c) >> 2
    C = (byte & 0x30) >> 4
    D = (byte & 0xc0) >> 6
    return D,C,B,A
def Bto8i(byte):
    A = bool(byte & 0x01)
    B = bool(byte & 0x02)
    C = bool(byte & 0x04)
    D = bool(byte & 0x08)
    E = bool(byte & 0x10)
    F = bool(byte & 0x20)
    G = bool(byte & 0x40)
    H = bool(byte & 0x80)
    return map(int,[H,G,F,E,D,C,B,A])

    

if __name__ == '__main__':
    print '>>> Btoii(0x95)'
    print Btoii(0x95)
    print '>>> Btoiiii(0x95)'
    print Btoiiii(0x95)
    print '>>> Bto8i(0x95)'
    print Bto8i(0x95)
