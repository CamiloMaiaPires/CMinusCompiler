import pandas as pd
import re


usedIndexes = []
def fixIndex(line):
    global usedIndexes
    tobeUsed = []
    for command in commands[line + 1:]:
        for i in range(1,len(command)):
            if "$t" in command[i]:
                #caso seja de vetor limpa para obter o número do registrador, e depois adicionar em tobeUsed
                if  ")" in command[i]:
                    rexesaux = re.search(r'\(\$t\d+\)', command[i][2:])
                    regaux = rexesaux.group()[1:-1]
                    if regaux[2:] in usedIndexes and regaux[2:] not in tobeUsed:
                        tobeUsed.append(regaux[2:])
                #caso seja comum adiciona o número em tobeUsed
                elif command[i][2:] in usedIndexes and command[i][2:] not in tobeUsed:
                    tobeUsed.append(command[i][2:])
    #subtrai as duas listas para remover os registradores que não serão mais usados
    usedIndexes = list(set(usedIndexes) - set(set(usedIndexes) - set(tobeUsed)))

def findFreeIndex():
    for num in range(1, 25):
        if str(num) not in usedIndexes:
            usedIndexes.append(str(num))
            return "$t"+str(num)

def getIndex(reg, linha_quad, pos_quad):

    if reg[2:] == 'FP':
        return "$t29"
    elif reg[2:] == 'RET':
        return "$t28"
    else:
        index = int(reg[2:])
        
    # caso do store
    if pos_quad == 4:
        #se for 0 continua com o mesmo número
        if index == 0:
            return reg
        #se for menor que 25 continua com o mesmo número
        if index < 25:
            return reg
        #escolhe um número não utilizado entre 1 e 24
        for num in range(1, 25):
            if str(num) not in usedIndexes:
                usedIndexes.append(str(num))
                return "$t"+str(num)

    if "$t" in commands[linha_quad][pos_quad]:

        #se for 0 continua com o mesmo número
        if index == 0:
            return commands[linha_quad][pos_quad]
        #se for menor que 25 continua com o mesmo número
        if index < 25:
            return commands[linha_quad][pos_quad]
        #escolhe um número não utilizado entre 1 e 24
        for num in range(1, 25):
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
        #caso não seja atribuido nenhum número, o limite de registradores foi atingido
        print("\n===============ERRO: LIMITE DE REGISTRADORES ATINGIDO===============\n")
    return "FATAL ERROR"

def parse_tm_to_asm(commands, tbl, filename):

    usedVars = {}
    Params = []
    scope = " "
    vetload = 0
    jump = False
    assembly = open(filename, 'w')

    ### adiciona offset no endereço da memória de dados, de acordo com o processo do S.O. ###
    pid = 0
    end_inicio = pid*150
    assembly.write("addi $t30 $t0 "+ str(end_inicio) + "\n")

    for i, command in enumerate(commands):

        #adiciona os indices utilizados pela quadrupla atual na lista usedIndexes
        for reg in command[1:]:
            #Para vetores, obtem o indice de dentro do parenteses
            if  ")" in reg and "$t" in reg:
                rexesaux = re.search(r'\(\$t\d+\)', reg)
                regaux = rexesaux.group()[1:-1]
                if regaux[2:] not in usedIndexes:
                    usedIndexes.append(regaux[2:])
            elif "$t" in reg and reg[2:] not in usedIndexes:
                usedIndexes.append(reg[2:])

        #tratamento para cada comando
        match command[0]:
            case 'FUNC':
                if not jump:
                    assembly.write("j "+"main""\n")
                    jump = True
                    
                assembly.write("LAB "+command[2]+"\n")
                scope = command[2]
                if command[2] != "main":
                    # caso não seja main, irá armazenar o endereço de retorno no segundo endereço do frame
                    assembly.write("addi $t30 $t30 1\n")
                    assembly.write("sw $t31 $t29 1"+"\n")  

                    fpImmediate = 2
                else:
                    #caso seja main, aloca memória para variáveis globais
                    assembly.write("addi $t30 $t30 32\n")
                    # atualiza valor do sp
                    assembly.write("addi $t29 $t30 0\n")
                    fpImmediate = 0
                    
            case 'END':
                if command[1] != 'main':
                    #caso não seja main, marca o fim da função
                    assembly.write("LAB FIM:"+command[1] +"\n")
                    #busca o endereço de retorno
                    assembly.write("lw $t31 $t29 1\n")
                    #pula para a linha do endereço de retorno
                    assembly.write("jr $t31"+"\n")

                else:
                    #Modifica flag na RAM para indicar que o processo foi executado
                    assembly.write("addi " +"$t27 " + "$t0 " + "107"+"\n")
                    assembly.write("lw $t27 $t27 0"+"\n")
                    assembly.write("sw $t0 $t27 107"+"\n")
                    assembly.write("halt"+"\n")

            case 'ARG':
                # Mapeia a posição do imediato na stack, a ordem das instruções ARGS deve seguir a mesma ordem das instruções PARAM antes da chamada da função
                tbl.loc[(tbl['Name'] == command[2]) & (tbl['Scope'] == scope), 'Location'] = fpImmediate
                fpImmediate += 1
                

            case 'LOAD':
                #FALTA VERIFICAR SE É VETOR
                reg = getIndex(command[1],i,1)
                if command[2] not in usedVars:
                    usedVars[command[2]] = reg

                if(command[2] == 'KERNELpidbuffer'):
                    assembly.write("addi " +"$t27 " + "$t0 " + "107"+"\n")
                    assembly.write("lw "+reg+" "+"$t27 0"+"\n")
                elif(command[2] == 'KERNELpreempt'):
                    assembly.write("addi " +"$t27 " + "$t0 " + "106"+"\n")
                    assembly.write("lw "+reg+" "+"$t27 0"+"\n")
                else:
                    assembly.write("lw "+reg+" "+"$t29 "+str(int(tbl.loc[(tbl['Name'] == command[2]) & (tbl['Scope'] == scope), 'Location'].values[0]))+"\n")
            case 'GOTO':
                assembly.write("j "+command[1]+"\n")
            case 'LAB':
                assembly.write("LAB "+command[1]+"\n")
            case 'IFF':
                assembly.write("beq "+command[1]+" "+"$t0 "+command[2]+"\n")
                usedIndexes.remove(str(command[1][2:]))
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
                if command[2] == "input":
                    assembly.write("input " +"$t28"+"\n")
                elif command[2] == "output":
                    assembly.write("output " +Params[0]+"\n")
                    Params = []
                elif command[2] == "SetLCD":
                    assembly.write("SetLCD " +Params[0]+"\n")
                    Params = []
                elif command[2] == "LoadInstruction":
                    assembly.write("LoadInstruction " +Params[0]+ " " +Params[1]+"\n")
                    Params = []
                elif command[2] == "RestoreContext":
                    #calculo do endereço base (cada bloco tem 150 endereços na RAM, os ultimos 32 ficam para a troca de contexto)
                    assembly.write("addi " + "$t27 " + "$t0 " + "150"+"\n")
                    assembly.write("mult " + "$t27 " + Params[0] + " $t27"+"\n")
                    assembly.write("addi " +"$t27 " + "$t27 " + "118"+"\n")
                    for load_index in range(0, 32):
                        if load_index in [26]:
                            continue
                        assembly.write("lw " +"$t" + str(load_index) + " $t27 " + str(load_index) +"\n")
                    Params = []
                elif command[2] == "SaveContext":
                    #calculo do endereço base 
                    assembly.write("addi " + "$t27 " + "$t0 " + "150"+"\n")
                    assembly.write("mult " + "$t27 " + Params[0] + " $t27"+"\n")
                    assembly.write("addi " +"$t27 " + "$t27 " + "118"+"\n")
                    for load_index in range(0, 32):
                        if load_index in [26]:
                            continue
                        assembly.write("sw " +"$t" + str(load_index) + " $t27 " + str(load_index) +"\n")
                    Params = []
                elif command[2] == "ClearContext":
                    #calculo do endereço base (cada bloco tem 150 endereços na RAM, os ultimos 32 ficam para a troca de contexto)
                    assembly.write("addi " + "$t27 " + "$t0 " + "150"+"\n")
                    assembly.write("mult " + "$t27 " + Params[0] + " $t27"+"\n")
                    assembly.write("addi " +"$t27 " + "$t27 " + "118"+"\n")
                    for load_index in range(0, 32):
                        assembly.write("sw $t0 $t27 " + str(load_index) +"\n")
                    Params = []
                elif command[2] == "Run":
                    assembly.write("jalr $t25\n")
                elif command[2] == "EnableProcess":
                    # habilita a flag de execução do processo 
                    assembly.write("addi $t27 $t0 1\n")
                    assembly.write("sw $t27 " + Params[0] +" 107\n")
                    # salva o endereço de inicio no registrador $t25 do processo em questão
                    assembly.write("addi " + "$t27 " + "$t0 " + "150"+"\n")
                    assembly.write("mult " + "$t27 " + Params[0] + " $t27"+"\n")
                    assembly.write("addi " +"$t27 " + "$t27 " + "118"+"\n")
                    indexf = findFreeIndex()
                    assembly.write("addi " + indexf + " $t0 4096\n")
                    assembly.write("sw " + indexf + " $t27 25\n")
                    Params = []
                    usedIndexes.remove(str(indexf[2:]))
                elif command[2] == "isEnabled":
                    assembly.write("lw $t28 "+ Params[0] +" 107\n") 
                    Params = []
                elif command[2] == "SetQuantum":
                    assembly.write("SetQuantum\n") 
                    Params = []
                else:
                    # Armazena na primeira posição da nova stack, o valor da primeira posição da stack anterior
                    assembly.write("sw " +"$t29 " +"$t30 "+ "0"+"\n")
                    # Atualiza o valor do sp para a primeira posição do novo frame
                    assembly.write("addi " +"$t29 " +"$t30 "+ "0"+"\n")
                    # Sobe o ponteiro do fp devido a posição ocupada
                    assembly.write("addi " +"$t30 " +"$t30 "+ "1"+"\n")
                    # Armazena os parâmetros a partir da terceira posição do stack, que serão buscados na quádrupla ARG
                    Mem = 2
                    for param in Params:
                        assembly.write("addi $t30 $t30 1\n")
                        assembly.write("sw "+param+" $t29 "+str(Mem)+"\n")
                        Mem += 1
                    Params = []
                    
                    #pula para a label da função
                    assembly.write("jal " +command[2]+"\n")

                    # Volta o sp para o sp anterior
                    assembly.write("lw " +"$t29 " +"$t29 "+ "0"+"\n")
            case 'ADDI':
                assembly.write("addi "+getIndex(command[1],i,1)+" "+getIndex(command[2],i,2)+" "+command[3]+"\n")
            case 'ALLOC':
                if (command[1] != 'KERNELpidbuffer' and command[1] != 'KERNELpreempt'):
                    # Falta vetor
                    assembly.write("addi $t30 $t30 1\n")
                    #salva na tabela o deslocamento do inicio do frame
                    tbl.loc[(tbl['Name'] == command[1]) & (tbl['Scope'] == scope), 'Location'] = fpImmediate
                    fpImmediate += 1
            case 'STORE':
                if "(" in command[1]:
                    if "$" in command[1]:
                        regex = re.search(r'\(\$t\d+\)', command[1])
                        reg = command[2]

                        regtemp = regex.group()[1:-1]
                        
                        reg2 = getIndex(regtemp,i,4)
                        assembly.write("sw " +reg+ " " + reg2+ " 0"+"\n")
                    else:
                        #actually will never happen
                        regex = re.search(r'\((\d+)\)', command[1])
                        assembly.write("addi $t30 $t30 "+regex.group()[1:-1]+"\n")
                else:
                    if vetload:
                        assembly.write("sw "+reg2 +" $t29 "+str(tbl[(tbl['Name'] == command[1]) & (tbl['Scope'] == scope)].index[0])+"\n")
                        print(tbl[(tbl['Name'] == command[1]) & (tbl['Scope'] == scope)].index[0])
                        vetload = 0
                    else:
                        # salva na memória de dados
                        if(command[1] == 'KERNELpidbuffer'):
                            assembly.write("addi " +"$t27 " + "$t0 " + "107"+"\n")
                            assembly.write("sw "+getIndex(command[2],i,2) +" $t27 0"+"\n")
                        elif(command[1] == 'KERNELpreempt'):
                            assembly.write("addi " +"$t27 " + "$t0 " + "106"+"\n")
                            assembly.write("sw "+getIndex(command[2],i,2) +" $t27 0"+"\n")
                        else:
                            assembly.write("sw "+getIndex(command[2],i,2) +" $t29 "+str(int(tbl.loc[(tbl['Name'] == command[1]) & (tbl['Scope'] == scope), 'Location'].values[0]))+"\n")
                            usedIndexes.remove(str(getIndex(command[2],i,2)[2:]))

            case 'PARAM':
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
                usedIndexes.remove(str(getIndex(command[2],i,2)[2:]))
                usedIndexes.remove(str(getIndex(command[3],i,3)[2:]))
            case 'LET':
                assembly.write("let "+getIndex(command[1],i,1)+" "+getIndex(command[2],i,2)+" "+getIndex(command[3],i,3)+"\n")
                usedIndexes.remove(str(getIndex(command[2],i,2)[2:]))
                usedIndexes.remove(str(getIndex(command[3],i,3)[2:]))
            case 'GT':
                assembly.write("gt "+getIndex(command[1],i,1)+" "+getIndex(command[2],i,2)+" "+getIndex(command[3],i,3)+"\n")
                usedIndexes.remove(str(getIndex(command[2],i,2)[2:]))
                usedIndexes.remove(str(getIndex(command[3],i,3)[2:]))
            case 'GET':
                assembly.write("get "+getIndex(command[1],i,1)+" "+getIndex(command[2],i,2)+" "+getIndex(command[3],i,3)+"\n")
                usedIndexes.remove(str(getIndex(command[2],i,2)[2:]))
                usedIndexes.remove(str(getIndex(command[3],i,3)[2:]))
            case 'EQ':
                assembly.write("eq "+getIndex(command[1],i,1)+" "+getIndex(command[2],i,2)+" "+getIndex(command[3],i,3)+"\n")
                usedIndexes.remove(str(getIndex(command[2],i,2)[2:]))
                usedIndexes.remove(str(getIndex(command[3],i,3)[2:]))
            case 'NEQ':
                assembly.write("neq "+getIndex(command[1],i,1)+" "+getIndex(command[2],i,2)+" "+getIndex(command[3],i,3)+"\n")
                usedIndexes.remove(str(getIndex(command[2],i,2)[2:]))
                usedIndexes.remove(str(getIndex(command[3],i,3)[2:]))
        #fixIndex(i)

    assembly.close()

def relabel(file_path):
    
    commands_asm = []
    with open(file_path, 'r') as file:
        for line in file:
            quads = line.split(' ')
            commands_asm.append(quads)

    asmfinal = open(file_path, 'w')
    linha = 0
    # linha = 1024
    # encontra LAB, e vasculha as quadruplas até encontrar a label correspondente
    for command in commands_asm:
        if command[0] == "LAB":
            for comando in commands_asm:
                for j in range(0,len(comando)):
                    if command[1] == comando[j] and command != comando:
                        comando[j] = str(linha) + "\n"
                        break
        else:
            linha +=1
    # faz o mesmo para o caso do beq
    linha = 0
    # linha = 1024
    for command in commands_asm:
        if command[0] != "LAB":
            linha += 1
            if command[0] == "beq":
                command[3] = str((int(command[3]) - linha)) + "\n"
            asmfinal.write(" ".join(command))

    asmfinal.close()



if __name__ == "__main__":

    #carregando a tabela de simbolos
    tbl = pd.read_csv("./out_files/symtab.csv")
    tbl.set_index("Location", inplace=True)

    #abrindo arquivo do codigo intermediário
    commands = []
    with open('./out_files/intermediary.tm', 'r') as file:
        for line in file:
            quad = line.strip('(')
            quads = quad[:-2].split(', ')
            commands.append(quads)

    parse_tm_to_asm(commands, tbl, './out_files/assembly.asm')
    # Substituição de rótulos e ajustes finais
    relabel('./out_files/assembly.asm')