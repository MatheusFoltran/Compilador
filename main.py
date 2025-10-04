import sys
from lexer import lexer
from parser import parser
from ply import yacc

def main():
    # Verifica argumentos da linha de comando
    if len(sys.argv) != 2:
        print("Uso: python main.py <arquivo.rascal>")
        sys.exit(1)

    filename = sys.argv[1]

    # Lê o conteúdo do arquivo
    try:
        with open(filename, "r", encoding="utf-8") as f:
            code = f.read()
    except FileNotFoundError:
        print(f"Erro: Arquivo '{filename}' não encontrado.")
        sys.exit(1)

    # === Fase léxica ===
    lexer.input(code)
    print(f"\n=== Tokens do arquivo '{filename}' ===\n")
    for tok in lexer:
        print(f"{tok.type:<12} {tok.value!r:<12} (linha {tok.lineno}, pos {tok.lexpos})")

    # === Fase sintática ===
    print(f"\n=== Analisando sintaticamente ===\n")
    try:
        ast = parser.parse(code, lexer=lexer)
        if ast is None:
            print("Erro: Parsing falhou, nenhum AST foi gerado.")
        else:
            print("=== AST gerada com sucesso ===\n")
            # Se você tiver uma função para imprimir AST bonita, use aqui:
            print(ast)
    except yacc.YaccError as e:
        print("Erro durante a construção do parser:", e)
    except Exception as e:
        print("Erro de parsing:", e)

if __name__ == "__main__":
    main()
