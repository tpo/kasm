#
#   Opcodes and addressing modes
#
#       (empty)     impl
#       #n          immed
#       nn          abs
#       n           zp
#       nn,x        absx
#       nn,y        absy
#       a           implied
#       (nn)        ind
#       expr        rel
#       n,x         zpx
#       n,y         zpy
#       (n,x)       indx
#       (n),y       indy
#
#   optimize, whenever possible
#       ABS to ZP
#       ABSX to ZPX
#       ABSY to ZPY
#

IMPLIED = 0
IMMED = 1
ABS = 2
ZP = 3
ABSX = 4
ABSY = 5
IND = 6
REL = 7
ZPX = 8
ZPY = 9
INDX = 10
INDY = 11

#   without actual values, these are ambiguous
UNDECIDED_X = 12        # ABSX / ZPX
UNDECIDED_Y = 13        # ABSY / ZPY
UNDECIDED = 14          # ABS / ZP / REL
