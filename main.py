#!/usr/bin/env python3
"""
Web Analyzer CLI - Ponto de entrada principal
"""

import sys
import os

# Adiciona o diretório atual ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Agora podemos importar src
from src.analyzer import verificar_url
from src.utils import modo_interativo, modo_arquivo, mostrar_ajuda

def main():
    """Função principal"""
    
    if len(sys.argv) > 1:
        comando = sys.argv[1]
        
        if comando in ['--help', '-h']:
            mostrar_ajuda()
        elif comando in ['--arquivo', '-f']:
            if len(sys.argv) > 2:
                modo_arquivo(sys.argv[2])
            else:
                print("❌ Especifique um arquivo: python main.py --arquivo urls.txt")
        else:
            url = comando
            if not url.startswith('http'):
                url = 'https://' + url
            verificar_url(url)
    else:
        modo_interativo()

if __name__ == "__main__":
    main()
