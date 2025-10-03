import sys
from lexer import lexer

def main():
    # Verifica argumentos da linha de comando
    if len(sys.argv) != 2:
        print("Uso: python main.py <arquivo.rascal>")
        sys.exit(1)

    # Nome do arquivo recebido
    filename = sys.argv[1]

    try:
        # Lê o conteúdo do arquivo
        with open(filename, "r", encoding="utf-8") as f:
            code = f.read()
    except FileNotFoundError:
        print(f"Erro: Arquivo '{filename}' não encontrado.")
        sys.exit(1)

    # Envia o código para o lexer
    lexer.input(code)

    # Imprime os tokens encontrados
    print(f"=== Tokens do arquivo '{filename}' ===\n")
    for tok in lexer:
        print(tok)

if __name__ == "__main__":
    main()
