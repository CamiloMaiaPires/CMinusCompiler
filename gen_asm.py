import pandas as pd
import re

filename = 'in'
tbl = pd.read_csv(filename + ".csv")
tbl.set_index("Location", inplace=True)
file_path = filename + '.tm'
commands = []
with open(file_path, 'r') as file:
    for line in file:
        quad = line.strip('(')
        quads = quad[:-2].split(', ')
        commands.append(quads)
# Fix for Call registers ($t28 is return reg)
for i, command in enumerate(commands):
    if command[0] == "CALL":
        aux = command[1]
        command[1] = "$t28"
        for comando in commands[i:]:
            for j in range(1,4):
                if comando[j] == aux:
                    comando[j] = "$t28"
verbose = 0
usedIndexes = []
def fixIndex(line):
    global verbose
    global usedIndexes
    tobeUsed = []
    for command in commands[line + 1:]:
        for i in range(1,len(command)):
            if "$t" in command[i]:
                if  ")" in command[i]:
                    rexesaux = re.search(r'\(\$t\d+\)', command[i][2:])
                    regaux = rexesaux.group()[1:-1]
                    #print(regaux[2:], regaux, command[i])
                    if regaux[2:] in usedIndexes and regaux[2:] not in tobeUsed:
                        print(regaux[2:])
                        tobeUsed.append(regaux[2:])
                elif command[i][2:] in usedIndexes and command[i][2:] not in tobeUsed:
                    tobeUsed.append(command[i][2:])
    usedIndexes = list(set(usedIndexes) - set(set(usedIndexes) - set(tobeUsed)))
    #print(tobeUsed, line)

def getIndex(reg, indice, indice2):
    if indice2 == 4:
        if reg[2:] == 'SP':
            return "$t29"
        else:
            index = int(reg[2:])
        if index == 0:
            return reg
        if index < 29:
            return reg
        for num in range(1, 28):
            if str(num) not in usedIndexes:
                usedIndexes.append(str(num))
                return "$t"+str(num)
    if "$t" in commands[indice][indice2]:
        if reg[2:] == 'SP':
            return "$t29"
        else:
            index = int(reg[2:])
        if index == 0:
            return commands[indice][indice2]
        if index < 29:
            return commands[indice][indice2]
        for num in range(1, 28):
            if str(num) not in usedIndexes:
                for i in range(0,len(commands)):
                    for j in range(1,len(commands[i])):
                        if "$t" in commands[i][j]:
                            if commands[i][j] == reg:
                                commands[i][j] = "$t"+str(num)
                                break
                usedIndexes.remove(str(index))
                usedIndexes.append(str(num))
                return "$t"+str(num)
        print("\n----------------------------\nFATAL ERROR: NOT ENOUGH REGISTERS!!!\n----------------------------\n")
    return "FATAL ERROR"
#addi beq bne bgt blt lw sw j jal (jar) add sub div mult and or
usedVars = {}
Params = []
assembly = open(filename + ".asm", 'w')
scope = " "
Callflag = 0
jump = False
vetload = 0

for i, command in enumerate(commands):
    #print(commands[i])
    for reg in command[1:]:
        if  ")" in reg and "$t" in reg:
            rexesaux = re.search(r'\(\$t\d+\)', reg)
            regaux = rexesaux.group()[1:-1]
            if regaux[2:] not in usedIndexes:
                #print(regaux[2:])
                usedIndexes.append(regaux[2:])
        elif "$t" in reg and reg[2:] not in usedIndexes:
            usedIndexes.append(reg[2:])
    #print(usedIndexes)
    #print(command)
    match command[0]:
        case 'FUNC':
            if not jump:
                assembly.write("j "+"main""\n")
                jump = True
                
            assembly.write("LAB "+command[2]+"\n")
            scope = command[2]
            if command[2] != "main":
                assembly.write("addi $t30 $t30 1\n")
                assembly.write("sw $t31 $t29 1"+"\n")
            else:
                assembly.write("addi $t30 $t30 32\n")
                assembly.write("addi $t29 $t30 0\n")
                
        case 'END':
            if command[1] != 'main':
                assembly.write("LAB FIM:"+command[1] +"\n")
                assembly.write("lw $t31 $t29 1"+"\n")
                assembly.write("jr $t31"+"\n")
            else:
                assembly.write("halt"+"\n")

        case 'ARG':
            assembly.write("addi $t30 $t30 1\n")
        case 'LOAD':
            #add caso do vetor
            if "(" in command[2]:
                if "$" in command[2]:
                    regex = re.search(r'\(\$t\d+\)', command[2])
                    reg = getIndex(command[1],i,1)
                    if command[2] not in usedVars:
                        usedVars[command[2]] = reg
                    regtemp = regex.group()[1:-1]
                    # print(command,regtemp)
                    # print(usedIndexes)
                    reg2 = getIndex(regtemp,i,4)
                    #print(usedIndexes)
                    #assembly.write("add "+reg2+" "+reg2+" "+"$t29"+"\n")
                    assembly.write("lw " +reg2+ " " + reg+ " 0"+"\n")
                    vetload = 1
                else:
                    #actually will never happen :/
                    regex = re.search(r'\((\d+)\)', command[1])
                    assembly.write("addi $t30 $t30 "+regex.group()[1:-1]+"\n")
            else:
                reg = getIndex(command[1],i,1)
                if command[2] not in usedVars:
                    usedVars[command[2]] = reg
                assembly.write("lw "+reg+" "+"$t29 "+str(tbl[(tbl['Name'] == command[2]) & (tbl['Scope'] == scope)].index[0])+"\n")
        case 'GOTO':
            assembly.write("j "+command[1]+"\n")
        case 'LAB':
            assembly.write("LAB "+command[1]+"\n")
        case 'IFF':
            assembly.write("beq "+command[1]+" "+"$t0 "+command[2]+"\n")
        case 'WHILE':
            assembly.write("beq "+command[1]+" "+"$t0 "+command[2]+"\n")
        case 'RET':
            if command[1] == "$t28":
                assembly.write("addi $t28 "+ "$t28 "+"0"+"\n")
            else:
                assembly.write("addi $t28 "+ getIndex(command[1],i,1)+" 0"+"\n")
            assembly.write("j FIM:"+scope+"\n")
            usedVars = {}

        case 'CALL':
            # print(command, Params)
            if command[2] == "input":
                assembly.write("input " +"$t28"+"\n")
            elif command[2] == "output":
                assembly.write("output " +Params[0]+"\n")
                Params = []
            elif command[2] == "sw":
                assembly.write("sw " +  Params[0]+" "+ "$t0"+" "+ command[3]+"\n")
            elif command[2] == "lw":
                assembly.write("lw " + "$t1 $t0 "+command[3]+ "\n")
            else:
                regs = set(list(usedVars.values())+Params)
                backup = regs.copy()
                for r in regs:
                    print(len(regs))
                    assembly.write("sw "+r+" "+"$t30 "+ "0"+"\n")
                    assembly.write("addi " +"$t30 " +"$t30 "+ "1"+"\n")

                assembly.write("sw " +"$t29 " +"$t30 "+ "0"+"\n")
                assembly.write("addi " +"$t29 " +"$t30 "+ "0"+"\n")
                assembly.write("addi " +"$t30 " +"$t30 "+ "1"+"\n")
                Mem = 2
                for param in Params:
                    assembly.write("sw "+param+" $t29 "+str(Mem)+"\n")
                    Mem += 1
                Mem = 2
                Params = []
                
                assembly.write("jal " +command[2]+"\n")
                assembly.write("addi " +"$t30 " +"$t29 "+ "0"+"\n")
                assembly.write("lw " +"$t29 " +"$t29 "+ "0"+"\n")

                for r in regs:
                    assembly.write("subi " +"$t30 " +"$t30 "+ "1"+"\n")
                    assembly.write("lw "+r+" "+"$t30 "+ "0"+"\n")

        case 'ADDI':
            #command[2] is always $t0
            assembly.write("addi "+getIndex(command[1],i,1)+" "+getIndex(command[2],i,2)+" "+command[3]+"\n")
        case 'ALLOC':
            if "(" in command[1]:
                if "$" in command[1]:
                    regex = re.search(r'\(\$t\d+\)', command[1])
                    assembly.write("add $t30 $t30 "+regex.group()[1:-1]+"\n")
                else:
                    regex = re.search(r'\((\d+)\)', command[1])
                    assembly.write("addi $t30 $t30 "+regex.group()[1:-1]+"\n")
            else:
                assembly.write("addi $t30 $t30 1\n")
        case 'STORE':
            if "(" in command[1]:
                if "$" in command[1]:
                    regex = re.search(r'\(\$t\d+\)', command[1])
                    reg = command[2]

                    # print(command)
                    regtemp = regex.group()[1:-1]
                    
                    reg2 = getIndex(regtemp,i,4)
                    #print(command,regtemp,reg2)
                    #print(command[1])
                    #assembly.write("add "+reg2+" "+reg2+" "+"$t29"+"\n")
                    assembly.write("sw " +reg+ " " + reg2+ " 0"+"\n")
                else:
                    #actually will never happen :/
                    regex = re.search(r'\((\d+)\)', command[1])
                    assembly.write("addi $t30 $t30 "+regex.group()[1:-1]+"\n")
            else:
                if vetload:
                    assembly.write("sw "+reg2 +" $t29 "+str(tbl[(tbl['Name'] == command[1]) & (tbl['Scope'] == scope)].index[0])+"\n")
                    vetload = 0
                else:
                    assembly.write("sw "+getIndex(command[2],i,2) +" $t29 "+str(tbl[(tbl['Name'] == command[1]) & (tbl['Scope'] == scope)].index[0])+"\n")
        case 'PARAM':
            #print(command,regtemp,reg,reg2)
            # if vetload == 1:
            #     Params.append(reg2)
            # else:
            print(command, Params)
            reg = getIndex(command[1],i,1)
            Params.append(reg)
        case 'SUM':
            assembly.write("add "+getIndex(command[1],i,1)+" "+getIndex(command[2],i,2)+" "+getIndex(command[3],i,3)+"\n")
        case 'SUB':
            assembly.write("sub "+getIndex(command[1],i,1)+" "+getIndex(command[2],i,2)+" "+getIndex(command[3],i,3)+"\n")
        case 'MULT':
            assembly.write("mult "+getIndex(command[1],i,1)+" "+getIndex(command[2],i,2)+" "+getIndex(command[3],i,3)+"\n")
        case 'DIV':
            assembly.write("div "+getIndex(command[1],i,1)+" "+getIndex(command[2],i,2)+" "+getIndex(command[3],i,3)+"\n")
        case 'LT':
            assembly.write("lt "+getIndex(command[1],i,1)+" "+getIndex(command[2],i,2)+" "+getIndex(command[3],i,3)+"\n")
        case 'LET':
            assembly.write("let "+getIndex(command[1],i,1)+" "+getIndex(command[2],i,2)+" "+getIndex(command[3],i,3)+"\n")
        case 'GT':
            assembly.write("gt "+getIndex(command[1],i,1)+" "+getIndex(command[2],i,2)+" "+getIndex(command[3],i,3)+"\n")
        case 'GET':
            assembly.write("get "+getIndex(command[1],i,1)+" "+getIndex(command[2],i,2)+" "+getIndex(command[3],i,3)+"\n")
        case 'EQ':
            assembly.write("comp "+getIndex(command[1],i,1)+" "+getIndex(command[2],i,2)+" "+getIndex(command[3],i,3)+"\n")
        case 'NEQ':
            assembly.write("neq "+getIndex(command[1],i,1)+" "+getIndex(command[2],i,2)+" "+getIndex(command[3],i,3)+"\n")
    fixIndex(i)


assembly.close()
file_path = filename + '.asm'
commands_asm = []
linha = 0
with open(file_path, 'r') as file:
    for line in file:
        quads = line.split(' ')
        commands_asm.append(quads)
file_path = filename + ".asmfinal"
asmfinal = open(file_path, 'w')
linha = 0
for command in commands_asm:
    if command[0] == "LAB":
        for comando in commands_asm:
            for j in range(0,len(comando)):
                if command[1] == comando[j] and command != comando:
                    comando[j] = str(linha) + "\n"
                    break
    else:
        linha +=1

linha = 0
for command in commands_asm:
    if command[0] != "LAB":
        linha += 1
        if command[0] == "beq":
            command[3] = str((int(command[3]) - linha)) + "\n"
        asmfinal.write(" ".join(command))

asmfinal.close()