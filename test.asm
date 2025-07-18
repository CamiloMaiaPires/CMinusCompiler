j main
LAB main
addi $t30 $t30 32
addi $t29 $t30 0
addi $t30 $t30 1
addi $t30 $t30 1
input $t28
sw $t0 $t29 1
input $t28
sw $t0 $t29 2
lw $t1 $t29 1
lw $t2 $t29 2
gt $t3 $t1 $t2
beq $t3 $t0 L0
lw $t4 $t29 1
output $t4
j L1
LAB L0
lw $t5 $t29 2
output $t5
LAB L1
halt
