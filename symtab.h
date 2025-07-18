#ifndef _SYMTAB_H_
#define _SYMTAB_H_

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

void st_insert( char * name, int lineno, int loc, char * scope, char * typeId, char *typeData, int len );

int st_lookup( char * name, char * scope );

void printSymTab();

char* findFunType (char* name, char* scope);

void saveSymTabCSV(const char *filename);

#endif
