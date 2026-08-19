#include "globals.h"

#define NO_PARSE FALSE
#define NO_ANALYSE FALSE
#define NO_CODE FALSE

// int TraceScan = TRUE;
// int TraceParse = TRUE;
// int TraceAnalyze = TRUE;

int TraceScan = FALSE;
int TraceParse = FALSE;
int TraceAnalyze = FALSE;

int Error = FALSE;

#if !NO_ANALYZE
#include "analyze.h"
#if !NO_CODE
#include "cgen.h"
#endif
#endif

// // arquivo para armazenar o código intermediário
// FILE *outIntCodeFile;

int main(int argc, char **argv){
    char pgm[120]; /* source code file name */
    TreeNode *arvoreSintatica;
    line_number = 0;

    if (argc != 2)
    {
        printf("Quantidade de entradas incorreta.\n");
        return 1;
    }
    strcpy(pgm, argv[1]);
    if (strchr(pgm, '.') == NULL){
        strcat(pgm, ".cminus");
    }

    char temp[256];
    snprintf(temp, sizeof(temp), "%s%s", "./cminus_code/", pgm);
    strcpy(pgm, temp);
    printf("%s", pgm);

    inputFile = fopen(pgm, "r");

    if (inputFile == NULL)
    {
        printf("Arquivo de input nao encontrado\n");
    }

    printf("Inicio da compilacao.\n");

#if NO_PARSE
    while (getToken() != YYEOF)
        ;
#else
    arvoreSintatica = parse();
    if (TraceParse)
    {
        printf("\nArvore Sintatica:\n");
        printTree(arvoreSintatica);
    }

#if !NO_ANALYZE
    if (!Error)
    {
        if (TraceAnalyze)
            printf("\nCriando tabela de símbolos...\n");
        printf("\n");
        buildSymtab(arvoreSintatica);
        saveSymTabCSV(pgm);
        if (TraceAnalyze)
            printf("\nInício da verificação de tipos...\n");
        typeCheck(arvoreSintatica);
        if (TraceAnalyze)
            printf("\nFim da verificação de tipos\n");
    }

#if !NO_CODE
    if (!Error)
    {
        outIntCodeFile = fopen("./out_files/intermediary.tm", "w");
        codeGen(arvoreSintatica);
        fclose(outIntCodeFile);
    }
#endif
#endif
#endif

    printf("\nFim da compilação.\n");

    fclose(inputFile);
    return 0;
}