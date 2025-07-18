j main
LAB main
addi $t30 $t30 32
addi $t29 $t30 0
addi $t30 $t30 1
addi $t30 $t30 1
input $t28
add $t1 $t0 $t28
sw $t1 $t29 1
input $t28
add $t2 $t0 $t28
sw $t2 $t29 2
lw $t3 $t29 1
lw $t4 $t29 2
gt $t5 $t3 $t4
beq $t5 $t0 L0
lw $t6 $t29 1
output $t6
j L1
LAB L0
lw $t7 $t29 2
output $t7
LAB L1
halt
