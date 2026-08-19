def regToBinary(reg):
    return format(int(reg.strip("$t")), '05b')

def convert_instruction_to_binary(instruction):
    opcode_table = {
        'add':   '000000',
        'sub':   '000000',
        'and':   '000000',
        'or':    '000000',
        'mult':  '000000',
        'div':   '000000',
        'gt':    '000000',
        'eq':    '000000',
        'let':   '000000',
        'neq':   '000000',
        'lt':   '000000',

        'addi':  '010000',
        'subi':  '010001',
        'andi':  '010010',
        'lw':    '100011',
        'sw':    '101011',
        'beq':   '001000',
        'bne':   '001001',
        'bgt':   '001010',
        'bge':   '001011',
        'ble':   '001100',

        'j':     '000001',
        'jal':   '000010',
        'jr' :   '000011',
        'jalr' : '000100',
        'input': '100000',
        'output':'100001',
        'SetLCD':'110000',
        'LoadInstruction':'110001',
        'SetQuantum':'110010',
        'halt':  '111111'
    }
    funct_table = {
        'add':  '100000',
        'sub':  '100010',
        'mult': '011000',
        'div':  '011010',
        'and':  '100100',
        'or':   '100101',
        'nor':  '100111',
        'xor':  '100110',
        'gt':   '010000',
        'eq':   '010001',
        'let':  '010010',
        'neq':  '010011',
        'lt':  '010100'

    }
    instr_parts = instruction.split()
    instr_type = instr_parts[0]

    opcode = opcode_table[instr_type]
    if instr_type in ['addi', 'subi', 'lw', 'sw','beq']:
        
        rs = regToBinary(instr_parts[2])
        rt = regToBinary(instr_parts[1])
        immediate = format(int(instr_parts[3].strip("$t")), '016b')
        binary_instr = f'{opcode}{rs}{rt}{immediate}'

    elif instr_type in ['jr', 'jalr']:
        rs = regToBinary(instr_parts[1])
        immediate = format(0, '021b')
        binary_instr = f'{opcode}{rs}{immediate}'

    elif instr_type in ['j', 'jal']:
        address = format(int(instr_parts[1].strip("$t")), '026b')
        binary_instr = f'{opcode}{address}'
    elif instr_type in ['halt']:
        address = "0"*21
        rs = "11010"
        binary_instr = f'{opcode}{rs}{address}'
    elif instr_type in ['input']:
        rs = regToBinary(instr_parts[1])
        immediate = format(2**16 - 1, '016b')
        binary_instr = f'{opcode}00000{rs}{immediate}'
    elif instr_type in ['output']:
        rs = regToBinary(instr_parts[1])
        immediate = format(2**21 - 1, '021b')
        binary_instr = f'{opcode}{rs}{immediate}'
    elif instr_type in ['SetLCD']:
        rs = regToBinary(instr_parts[1])
        immediate = format(2**21 - 1, '021b')
        binary_instr = f'{opcode}{rs}{immediate}'
    elif instr_type in ['LoadInstruction']:
        rs1 = regToBinary(instr_parts[1])
        rs2 = regToBinary(instr_parts[2])
        immediate = format(2**16 - 1, '016b')
        binary_instr = f'{opcode}{rs1}{rs2}{immediate}'
    elif instr_type in ['SetQuantum']:
        immediate = format((1 << 26) - 1, '026b')
        binary_instr = f'{opcode}{immediate}'
    else:
        funct = funct_table[instr_type]
        rs = regToBinary(instr_parts[2])
        rt = regToBinary(instr_parts[3])
        rd = regToBinary(instr_parts[1])
        shamt = '00000'
        binary_instr = f'{opcode}{rs}{rt}{rd}{shamt}{funct}'

    return binary_instr
    
asm = open("./out_files/assembly.asm","r")
commands = []
for line in asm:
    line = line.replace("\n","")
    commands.append(line)

binary = open("./out_files/rom.txt","w")
for command in commands:
    binario = convert_instruction_to_binary(command)
    binary.write(str(binario)+"\n")
binary.close()