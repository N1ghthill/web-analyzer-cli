# Web Analyzer CLI

Ferramenta de linha de comando em Python para analisar rapidamente a performance básica de websites.
Python command-line tool to quickly inspect basic website performance signals.

## Recursos | Features
- Status HTTP e tempo de resposta. / HTTP status and response time.
- Título da página e contagem de imagens/links. / Page title and image/link counts.
- Checagem de viewport (mobile friendly). / Viewport check (mobile friendly).
- Modo interativo e leitura de URLs por arquivo. / Interactive mode and file-based batch mode.

## Início rápido | Quick start
```bash
git clone https://github.com/N1ghthill/web-analyzer-cli.git
cd web-analyzer-cli
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py https://ruas.dev.br
```

## Uso | Usage
```bash
# URL direta
python main.py https://example.com

# Modo interativo
python main.py

# Arquivo com URLs
python main.py -f urls.txt

# (Opcional) Instalar localmente e usar o comando
pip install -e .
web-analyzer https://example.com
```

## Documentação | Documentation
- `docs/USAGE.md`

## Licença | License
MIT. Consulte `LICENSE`.
