from addressingModes import *

gOps = {
    'op_nop'    : { IMPLIED: 0x00 }, # don't do anything
    'op_load'   : { ABS:     0x01 }, # load ACC from address
    'op_store'  : { ABS:     0x02 }, # store ACC to address
    'op_jmp'    : { ABS:     0x03 }, # jump to given address
    'op_jsub'   : { ABS:     0x04 }, # jump to subroutine
    'op_ret'    : { IMPLIED: 0x05 }, # return from subroutine
    'op_yield'  : { IMPLIED: 0x05 }, # alias of OP_RET
    'op_set_sp' : { IMPLIED: 0x06 }, # copy ACC to SP
}

gAddressWidth = 1 # Byte
