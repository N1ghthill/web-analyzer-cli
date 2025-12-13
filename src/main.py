#!/usr/bin/env python3
"""
Ponto de entrada dentro de src/ - Para uso com pip install
"""
from .analyzer import verificar_url
from .utils import modo_interativo, modo_arquivo, mostrar_ajuda

def main():
    """Função principal"""
    import sys
    
    if len(sys.argv) > 1:
        comando = sys.argv[1]
        
        if comando in ['--help', '-h']:
            mostrar_ajuda()
        elif comando in ['--arquivo', '-f']:
            if len(sys.argv) > 2:
                modo_arquivo(sys.argv[2])
            else:
                print("❌ Especifique um arquivo: web-analyzer --arquivo urls.txt")
        else:
            url = comando
            if not url.startswith('http'):
                url = 'https://' + url
            verificar_url(url)
    else:
        modo_interativo()

if __name__ == "__main__":
    main()
