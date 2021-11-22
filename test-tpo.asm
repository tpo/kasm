init:             op_load scheduler_addr
                  op_set_int
                  op_load int_stack_addr
                  op_set_int
init_end:         op_jmp init_end ; wait for first interrupt into scheduler

scheduler_addr:   db scheduler
int_stack_addr:   db int_stack; interrupt stack addr
scheduler:        op_xxx
int_stack:        db 0,0,0,0,0,0,0 ; interrupt stack




init:           op_load scheduleraddr
                op_load stackaddr
                op_set_sp

stackaddr:      db stack ; stack addr
schedulerad r:  db scheduler; stack addr
padding:        db 0

scheduler:      op_jsub process1
dispatcher2 :   op_jsub process2
                op_jmp dispatcher

process1:       op_load data1
                op_store data2
                op_yield
data1:          db 11
data2:          db 111

process2:       op_load data3
                op_store data4
                op_yield
data3:          db 22
data4:          db 222

stack:          db 0,0,0,0,0,0,0

