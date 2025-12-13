"""
Módulo principal de análise de websites
"""

import requests
import time
from datetime import datetime
from bs4 import BeautifulSoup

def verificar_url(url):
    """Verifica uma URL e retorna informações básicas"""
    
    print(f"\n{'='*50}")
    print(f"🔍 ANALISANDO: {url}")
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print('='*50)
    
    try:
        inicio = time.time()
        resposta = requests.get(url, timeout=10, headers={
            'User-Agent': 'WebAnalyzerCLI/1.0'
        })
        tempo_resposta = time.time() - inicio
        
        status = resposta.status_code
        
        print(f"📡 Status HTTP: {status} {'✅' if status == 200 else '⚠️'}")
        print(f"⚡ Tempo de resposta: {tempo_resposta:.2f} segundos")
        
        if status == 200:
            soup = BeautifulSoup(resposta.text, 'html.parser')
            
            titulo = soup.title.string if soup.title else "Sem título"
            print(f"📝 Título: {titulo}")
            
            imagens = len(soup.find_all('img'))
            links = len(soup.find_all('a'))
            print(f"🖼️  Imagens encontradas: {imagens}")
            print(f"🔗 Links encontradas: {links}")
            
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            if viewport:
                print("📱 Mobile Friendly: ✅ Sim")
            else:
                print("📱 Mobile Friendly: ⚠️  Pode melhorar")
                
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
    
    # Retornar dados para possível uso futuro
    return {
        'url': url,
        'status': status,
        'tempo_resposta': tempo_resposta,
        'titulo': titulo if 'titulo' in locals() else None
    }
