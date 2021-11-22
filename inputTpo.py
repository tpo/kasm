from addressingModes import *

ops = {
    'op_nop'        : { IMPLIED: 0x00 }, # don't do anything
    'op_load'       : { ABS:     0x01 }, # load ACC from address
    'op_store'      : { ABS:     0x02 }, # store ACC to address
    'op_jmp'        : { ABS:     0x03 }, # jump to given address
    'op_jsub'       : { ABS:     0x04 }, # jump to subroutine
    'op_sp_to_acc'  : { IMPLIED: 0x05 }, # copy SP to ACC
    'op_acc_to_sp'  : { IMPLIED: 0x06 }, # copy ACC to SP
    'op_push'       : { IMMED:   0x07 }, # push given register to stack
    'op_pop'        : { IMMED:   0x08 }, # pop register from stack
    'op_ret'        : { IMMED:   0x08 }, # return from subroutine
    'op_yield'      : { IMMED:   0x08 }, # reschedule
    'op_eq'         : { ABS:     0x09 }, # set EQ flag if ACC == value at given address
    'op_jmp_eq'     : { ABS:     0x0a }, # jump to given address if EQ is set
    'op_set_int'    : { IMPLIED: 0x0b }, # copy ACC to interrupt handler pointer
    'op_iret'       : { IMPLIED: 0x0c }, # copy ACC to interrupt handler pointer
}

addressWidth = 1 # Byte
fixedWidthInstructions = 2 # Bytes
