#include "globals.h"
#include "symtab.h"
#include "cgen.h"

static int tmpOffset = 0;

static void cGen (TreeNode * arvoreSintatica, StatementKind type);

int count = 0;
int label = 0;

static void printOp( TokenType token, const char* tokenString )
{ switch (token){
    case SUM: fprintf(outIntCodeFile,"SUM"); break;
    case SUB: fprintf(outIntCodeFile,"SUB"); break;
    case MULT: fprintf(outIntCodeFile,"MULT"); break;
    case DIV: fprintf(outIntCodeFile,"DIV"); break;
    case LT: fprintf(outIntCodeFile,"LT"); break;
    case LET: fprintf(outIntCodeFile,"LET"); break;
    case GT: fprintf(outIntCodeFile,"GT"); break;
    case GET: fprintf(outIntCodeFile,"GET"); break;
    case NEQ: fprintf(outIntCodeFile,"NEQ"); break;
    case EQ: fprintf(outIntCodeFile,"EQ"); break;
    default:
      fprintf(outIntCodeFile,"Unknown token: %d",token);
  }
}

static int indexCounter(){
  count = ++count;
  return count;
}
static int labelCounter(){
  label++;
  return label;
}

static int paramCounter(TreeNode * tree){
  TreeNode *t = tree->child[0];
  int counter = 0;
  while(t != NULL){
    t = t->sibling;
    counter++;
  }
  return counter;
}

/* Procedure genStmt generates code at a statement node */
static void genStmt(TreeNode * tree){
  int labelfalse, labelend, labelloop;
  switch (tree->kind.stmt) {
      case ifK:
        cGen(tree->child[0], -1);
        labelfalse = label;
        labelend = label + 1;        
        label += 2;
        fprintf(outIntCodeFile, "(IFF, $t%d, L%d, -)\n", count, labelfalse);
        cGen(tree->child[1], -1); 
        fprintf(outIntCodeFile, "(GOTO, L%d, -, -)\n", labelend);
        fprintf(outIntCodeFile, "(LAB, L%d, -, -)\n", labelfalse);
        cGen(tree->child[2], -1); 
        fprintf(outIntCodeFile, "(LAB, L%d, -, -)\n", labelend);
        break;
      case whileK:
        labelloop = label;
        fprintf(outIntCodeFile, "(LAB, L%d, -, -)\n", labelloop);
        cGen(tree->child[0], -1);
        labelend = label + 1;        
        label += 2;
        fprintf(outIntCodeFile, "(WHILE, $t%d, L%d, -)\n", count, labelend);
        cGen(tree->child[1], -1); 
        fprintf(outIntCodeFile, "(GOTO, L%d, -, -)\n", labelloop);
        fprintf(outIntCodeFile, "(LAB, L%d, -, -)\n", labelend);
        break;
      case returnK:
        cGen(tree->child[0], -1);
        fprintf(outIntCodeFile, "(RET, $t%d, -, -)\n", count);
        break;
      case functionK: {
        
        if(tree->type == voidK){
          fprintf(outIntCodeFile, "(FUNC, void, %s, -)\n", tree->attr.name);
        }
        if(tree->type == integerK){
          fprintf(outIntCodeFile, "(FUNC, integer, %s, -)\n", tree->attr.name);
        }
        TreeNode *arg1 = tree->child[0];
        //caso a funcao tenha parametros, chama cGen para gerar as quadruplas ARG
        if (arg1->type != voidK){
          cGen(arg1, functionK);
        }
        //gerar quadruplas do conteudo da funcao
        cGen(tree->child[1], -1);
        //gera quadrupla END
        fprintf(outIntCodeFile, "(END, %s, -, -)\n", tree->attr.name);
        break;
      }
    
      case callK:
        cGen(tree->child[0], callK);
        fprintf(outIntCodeFile, "(CALL, $t28, %s, %d)\n", tree->attr.name, paramCounter(tree));
        break;

      case variableK:
        if (tree->attr.len == 0)
          fprintf(outIntCodeFile, "(ALLOC, %s, %s, -)\n", tree->attr.name, tree->attr.scope);
        else
          fprintf(outIntCodeFile, "(ALLOC, %s(%d), %s, -)\n", tree->attr.name, tree->attr.len, tree->attr.scope);
        break;

      case assignK: {
        cGen(tree->child[1], -1);
        int reg_exp = count;        
        if (tree->child[0]->kind.exp == vectorK) {
          cGen(tree->child[0]->child[0], -1);
          int reg_index = count;
          fprintf(outIntCodeFile, "(ADD, $t%d, $t%d, $tSP)\n", indexCounter(), reg_index);
          fprintf(outIntCodeFile, "(ADDI, $t%d, $t%d, %d)\n", indexCounter(), count,
                  st_lookup(tree->child[0]->attr.name, tree->child[0]->attr.scope));
          fprintf(outIntCodeFile, "(STORE, %s($t%d), ", tree->child[0]->attr.name, count);
        } else {
          fprintf(outIntCodeFile, "(STORE, %s, ", tree->child[0]->attr.name);
        }

        if (tree->child[1]->kind.exp == vectorK && tree->child[0]->kind.exp == vectorK)
          fprintf(outIntCodeFile, "$t%d, -)\n", reg_exp);
        else if (tree->child[1]->kind.exp == vectorK)
          fprintf(outIntCodeFile, "$t%d, -)\n", count);
        else
          fprintf(outIntCodeFile, "$t%d, -)\n", reg_exp);
        break;
      }
      default:
        break;
  }
}

/* Procedure genExp generates code at an expression node */
static void genExp(TreeNode * tree){
  
  switch (tree->kind.exp) {
    case typeK:
      cGen(tree->child[0], -1);
      break;
    case constantK:
      fprintf(outIntCodeFile, "(ADDI, $t%d, $t0, %d)\n", indexCounter(), tree->attr.val);
      break;
    case idK:
      fprintf(outIntCodeFile, "(LOAD, $t%d, %s, -)\n", indexCounter(), tree->attr.name);
      break;
    case vectorK:
      // processa o indice do vetor e armazena o numero do registrador em reg_index
      cGen(tree->child[0], -1);
      int reg_index = count;
      //obtem a posição da pilha de execução
      fprintf(outIntCodeFile, "(ADD, $t%d, $t%d, $tSP)\n", indexCounter(), reg_index);
      //soma o endereço com um offset da posição na tabela
      fprintf(outIntCodeFile, "(ADDI, $t%d, $t%d, %d)\n", indexCounter(), count,st_lookup(tree->attr.name, tree->attr.scope));
      // carrega o valor do vetor na posição calculada
      fprintf(outIntCodeFile, "(LOAD, $t%d, %s($t%d), -)\n", indexCounter(), tree->attr.name, count);
      break;
    case operationK:
      char rg1[10], rg2[10];
      // processa o primeiro operando e armazena o numero do registrador em reg_op1
      cGen(tree->child[0], -1);
      int reg_op1 = count;
      sprintf(rg1, "$t%d", reg_op1);

      //processa o segundo operando e armazena o numero do registrador em reg_op2
      cGen(tree->child[1], -1);
      int reg_op2 = count;
      sprintf(rg2, "$t%d", reg_op2);
      //gera a quadrupla de acordo com o operador
      fprintf(outIntCodeFile, "(");
      printOp(tree->attr.op, "");
      fprintf(outIntCodeFile, ", $t%d, %s, %s)\n", indexCounter(), rg1, rg2);
      break;
    default:
      break;
  }
}

/* Procedure cGen recursively generates code by
 * tree traversal
 */
static void cGen(TreeNode * tree, StatementKind type){
  if (tree != NULL){
    switch (tree->nodekind) {
      case statementK:
        genStmt(tree);
        break;
      case expressionK:
        if (type != functionK) genExp(tree);
        break;
      default:
        break;
    }

    if (type == functionK) {
      fprintf(outIntCodeFile, "(ARG, %s, %s, %s)\n", tree->attr.name, tree->child[0]->attr.name, tree->attr.scope);
    }
    if (type == callK) {
      fprintf(outIntCodeFile, "(PARAM, $t%d, -, -)\n", count);
    }

    cGen(tree->sibling, type);
  }
}

void codeGen(TreeNode * syntaxTree){
    cGen(syntaxTree, -1);
}