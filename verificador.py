#!/usr/bin/env python3
"""
VERIFICADOR DE WEBSITES
Um script simples para verificar a saúde de websites
"""

import requests
import time
import sys
from datetime import datetime
from bs4 import BeautifulSoup

def verificar_url(url):
    """Verifica uma URL e retorna informações básicas"""
    
    print(f"\n{'='*50}")
    print(f"🔍 ANALISANDO: {url}")
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print('='*50)
    
    try:
        # Medir tempo de resposta
        inicio = time.time()
        resposta = requests.get(url, timeout=10)
        tempo_resposta = time.time() - inicio
        
        # Status da resposta
        status = resposta.status_code
        
        print(f"📡 Status HTTP: {status} {'✅' if status == 200 else '⚠️'}")
        print(f"⚡ Tempo de resposta: {tempo_resposta:.2f} segundos")
        
        if status == 200:
            # Analisar conteúdo HTML
            soup = BeautifulSoup(resposta.text, 'html.parser')
            
            # Informações básicas
            titulo = soup.title.string if soup.title else "Sem título"
            print(f"📝 Título: {titulo}")
            
            # Contar elementos
            imagens = len(soup.find_all('img'))
            links = len(soup.find_all('a'))
            print(f"🖼️  Imagens encontradas: {imagens}")
            print(f"🔗 Links encontradas: {links}")
            
            # Verificar viewport mobile (básico)
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            if viewport:
                print("📱 Mobile Friendly: ✅ Sim")
            else:
                print("📱 Mobile Friendly: ⚠️  Pode melhorar")
                
            # Verificar charset
            charset = soup.find('meta', attrs={'charset': True})
            if charset:
                print(f"🔤 Charset: {charset.get('charset')}")
            
        else:
            print("❌ Site não está respondendo corretamente")
            
    except requests.exceptions.Timeout:
        print("⏰ ERRO: O site demorou muito para responder (timeout)")
    except requests.exceptions.ConnectionError:
        print("🔌 ERRO: Não foi possível conectar ao site")
    except Exception as e:
        print(f"⚠️  ERRO: {e}")
    
    print(f"{'='*50}\n")

def modo_interativo():
    """Modo interativo para testar múltiplos sites"""
    print("""
    🚀 VERIFICADOR DE WEBSITES
    --------------------------
    Digite as URLs para verificar (uma por linha)
    Digite 'sair' para terminar
    """)
    
    while True:
        url = input("🌐 URL: ").strip()
        
        if url.lower() in ['sair', 'exit', 'quit']:
            print("\n👋 Até logo!")
            break
        
        if url:
            if not url.startswith('http'):
                url = 'https://' + url
            
            verificar_url(url)

def modo_arquivo(arquivo):
    """Lê URLs de um arquivo"""
    try:
        with open(arquivo, 'r') as f:
            urls = [linha.strip() for linha in f if linha.strip()]
        
        print(f"📁 Verificando {len(urls)} URLs do arquivo {arquivo}")
        
        for url in urls:
            if not url.startswith('http'):
                url = 'https://' + url
            verificar_url(url)
            
    except FileNotFoundError:
        print(f"❌ Arquivo '{arquivo}' não encontrado")
    except Exception as e:
        print(f"⚠️  Erro: {e}")

def main():
    """Função principal"""
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        comando = sys.argv[1]
        
        if comando == '--help' or comando == '-h':
            mostrar_ajuda()
        elif comando == '--arquivo' or comando == '-f':
            if len(sys.argv) > 2:
                modo_arquivo(sys.argv[2])
            else:
                print("❌ Especifique um arquivo: python verificador.py --arquivo urls.txt")
        else:
            # Se passar uma URL direto
            url = comando
            if not url.startswith('http'):
                url = 'https://' + url
            verificar_url(url)
    else:
        modo_interativo()

def mostrar_ajuda():
    """Mostra instruções de uso"""
    print("""
    🚀 COMO USAR O VERIFICADOR DE WEBSITES:
    
    1. Verificar um site específico:
       python verificador.py https://exemplo.com
    
    2. Modo interativo (para vários sites):
       python verificador.py
    
    3. Ler URLs de um arquivo:
       python verificador.py --arquivo lista.txt
       
    4. Mostrar esta ajuda:
       python verificador.py --help
    
    📝 Exemplo de arquivo lista.txt:
    google.com
    github.com
    exemplo.com
    """)

if __name__ == "__main__":
    # Tentar importar dependências
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("📦 Algumas dependências não estão instaladas.")
        print("📦 Execute no terminal: pip install requests beautifulsoup4")
        sys.exit(1)
    
    main()
