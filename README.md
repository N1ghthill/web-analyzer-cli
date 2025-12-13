🌐 Web Analyzer CLI

[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub Stars](https://img.shields.io/github/stars/N1ghthill/web-analyzer-cli.svg)](https://github.com/N1ghthill/web-analyzer-cli/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/N1ghthill/web-analyzer-cli.svg)](https://github.com/N1ghthill/web-analyzer-cli/network)

Uma ferramenta de linha de comando desenvolvida em Python para análise rápida e eficiente de websites. Ideal para desenvolvedores, analistas de SEO e profissionais de marketing digital.

*✨ Destaques:*

- ⚡ *Rápido*: Análise completa em menos de 1 segundo
- 🎯 *Preciso*: Métricas reais de performance
- 📱 *Moderno*: Verificação mobile-first
- 🐍 *Python 3.6+*: Compatível com versões recentes

⚡ Uso Rápido - Escolha seu método:

| Método | Comando | Ideal para |
|--------|---------|------------|
| *Direto* | `python main.py <url>` | Testes rápidos |
| *Interativo* | `python main.py` | Múltiplos sites |
| *Arquivo* | `python main.py -f urls.txt` | Batch processing |
| *Global* | `web-analyzer <url>` | Uso frequente |

🏗️ Estrutura do Projeto:

web-analyzer-cli/ <br>
├── main.py               # ✅ Ponto de entrada principal<br>
├── README.md             # ✅ Documentação<br>
├── requirements.txt      # ✅ Dependências<br>
├── setup.py              # ✅ Para pip install<br>
├── .gitignore            # ✅ Ignorar arquivos desnecessários<br>
├── LICENSE               # ✅ Licença MIT<br>
├── src/                  # ✅ Código fonte<br>
│   ├── __init__.py<br>
│   ├── analyzer.py<br>
│   ├── main.py           # ✅ Para uso com pip install<br>
│   └── utils.py<br>
├── tests/                # ✅ Testes<br>
│   ├── __init__.py<br>
│   └── test_analyzer.py<br>
└── docs/                 # ✅ Documentação extra<br>
    └── USAGE.md<br>
    
🎯 Próximas Funcionalidades (Roadmap)

- Exportação para JSON/CSV
- Análise de SEO básica
- Verificação de SSL/TLS
- Gráficos de performance
- Suporte a proxy
- Cache de resultados

🎯 Demonstração Rápida

```bash
# Clone e teste em 30 segundos
git clone https://github.com/N1ghthill/web-analyzer-cli.git
cd web-analyzer-cli
python main.py https://ruas.dev.br

