initsp:        op_load stackaddr
               op_set_sp
               op_jmp dispatcher

stackaddr:     db stack ; stack addr
padding:       db 0

dispatcher:    op_jsub process1
dispatcher2:   op_jsub process2
               op_jmp dispatcher

process1:      op_load data1
               op_store data2
               op_yield  
data1:         db 11
data2:         db 111

process2:      op_load data3
               op_store data4
               op_yield
data3:         db 22
data4:         db 222

stack:         db 0,0,0,0,0,0,0

