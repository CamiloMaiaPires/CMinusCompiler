#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SIZE 211 //número primo para melhorar a distribuição e reduzir colisões

#define SHIFT 4

int hash(char * key, char* scope)
{
  int temp = 0;
  int i = 0;
  while (key[i] != '\0')
  {
    temp = ((temp << SHIFT) + key[i]) % SIZE;
        // O perador << faz deslocamentos de bits para a esquerda
        // no valor de temp (4 bits).
        // Este recurso está sendo usado para evitar sobrecarga
        // em temp.
    ++i;
  }
  i = 0;
    while (scope[i] != '\0')
    { 
        temp = ((temp << SHIFT) + scope[i]) % SIZE;
        ++i;
    }
  return temp;
}

typedef struct LineListRec
   { int lineno;
     struct LineListRec * next;
   } * LineList;

typedef struct BucketListRec
   { char * name;
     LineList lines;
     char * scope;
     char * typeId;
     char * typeData;
     int len;
     int memloc ; /* memory location for variable */
     struct BucketListRec * next; //para tratar colisões
   } * BucketList;

/* the hash table */
static BucketList hashTable[SIZE];

//insere novo registro na tabela
void st_insert( char * name, int lineno, int loc, char * scope, char * typeId, char *typeData, int len ){
  int h = hash(name, scope);
  BucketList l = hashTable[h];

  //procura na tabela se já existe registro igual
  while ((l != NULL) && (strcmp(name,l->name) != 0))
    l = l->next;  
  if (l == NULL) /* variable not yet in table */{ 
    l = (BucketList) malloc(sizeof(struct BucketListRec));
    l->name = name;
    l->lines = (LineList) malloc(sizeof(struct LineListRec));
    l->lines->lineno = lineno;
    l->memloc = loc;
    l->scope = scope;
    l->len = len;
    l->typeId = typeId;
    l->typeData = typeData;
    l->lines->next = NULL;
    l->next = hashTable[h];
    hashTable[h] = l; 
  } else /* found in table, so just add line number */
  { LineList t = l->lines;
    while (t->next != NULL) t = t->next;
    t->next = (LineList) malloc(sizeof(struct LineListRec));
    t->next->lineno = lineno;
    t->next->next = NULL;
  }
}

//posição na memória de uma variável, retorna -1 caso nao encontre na tabela
int st_lookup ( char * name, char * scope )
{ int h = hash(name, scope);
  BucketList l =  hashTable[h];
  while ((l != NULL) && (strcmp(name,l->name) != 0) && (strcmp(scope,l->scope) != 0))
    l = l->next;
  if (l == NULL) return -1;
  else return l->memloc;
}

char* findFunType (char* name, char* scope)
{ 
  int h = hash(name, scope);	
  BucketList l =  hashTable[h];
  while ((l != NULL) && (strcmp(name,l->name) != 0) && (strcmp(scope,l->scope) != 0))
        l = l->next;
  if (l == NULL) 
      return "null";
  else 
      return l->typeData;
}

void printSymTab(){ 
  int i;
  printf("Variable Name  Location  TypeId      TypeData   Scope      Line Numbers\n");
  printf("-------------  --------  ---------   --------   -----      ------------\n");
  for (i=0;i<SIZE;++i)
  { if (hashTable[i] != NULL)
    { BucketList l = hashTable[i];
      while (l != NULL)
      { LineList t = l->lines;
        printf("%-14s ",l->name);
        printf("%-8d  ",l->memloc);
        printf("%-10s  ",l->typeId);
        printf("%-9s  ",l->typeData);
        printf("%-8s  ",l->scope);
        while (t != NULL)
        { printf("%4d ",t->lineno);
          t = t->next;
        }
        printf("\n");
        l = l->next;
      }
    }
  }
}
void saveSymTabCSV(char *pgm) {
  char filename[256];  // Buffer para o nome final

  const char *dot = strchr(pgm, '.');
  if (dot != NULL) {
    size_t prefixLen = dot - pgm;
    strncpy(filename, pgm, prefixLen);
    filename[prefixLen] = '\0';
  } else {
    strcpy(filename, pgm);
  }
  strcat(filename, ".csv");

  FILE *fp = fopen(filename, "w");
  if (!fp) {
      fprintf(stderr, "Erro ao abrir %s para escrita da symtab\n", pgm);
      return;
  }

  fprintf(fp, "Name,Location,TypeId,TypeData,Scope,LineNumbers\n");

  for (int i = 0; i < SIZE; ++i) {
      if (hashTable[i] != NULL) {
          BucketList l = hashTable[i];
          while (l != NULL) {
              fprintf(fp, "%s,%d,%s,%s,%s,", 
                      l->name,
                      l->memloc,
                      l->typeId,
                      l->typeData,
                      l->scope);

              LineList t = l->lines;
              while (t != NULL) {
                  fprintf(fp, "%d", t->lineno);
                  if (t->next != NULL) fprintf(fp, " ");
                  t = t->next;
              }
              fprintf(fp, "\n");

              l = l->next;
          }
      }
  }

  fclose(fp);
}