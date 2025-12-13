"""
Funções utilitárias para o Web Analyzer CLI
"""

from src.analyzer import verificar_url

def modo_interativo():
    """Modo interativo para testar múltiplos sites"""
    print("""
    🚀 WEB ANALYZER CLI
    -------------------
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

def mostrar_ajuda():
    """Mostra instruções de uso"""
    print("""
    🚀 WEB ANALYZER CLI - Como usar:
    
    Uso básico:
      web-analyzer <url>          Analisa uma URL específica
    
    Modo interativo:
      web-analyzer                Inicia modo interativo
    
    Ler de arquivo:
      web-analyzer --arquivo <arquivo>
      web-analyzer -f <arquivo>
    
    Ajuda:
      web-analyzer --help
      web-analyzer -h
    
    📝 Exemplo de arquivo urls.txt:
    google.com
    github.com
    exemplo.com
    
    ✨ Funcionalidades:
    • Verifica status HTTP
    • Mede tempo de resposta
    • Analisa título da página
    • Conta imagens e links
    • Verifica mobile friendly
    • Detecta charset
    """)
