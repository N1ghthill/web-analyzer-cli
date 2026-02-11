# Web Analyzer CLI

CLI em Python para auditoria de qualidade de websites.

## O que a ferramenta faz

- `modo basico`: status HTTP, tempo de resposta, titulo, links, imagens e viewport.
- `modo full` (`--full`): auditoria com nota de `0-100` por criterio e nota geral ponderada.

Criterios do modo full:
- Performance (`25%`)
- Seguranca (`30%`)
- SEO (`20%`)
- Acessibilidade (`15%`)
- Boas praticas (`10%`)

## Compatibilidade

- Funciona em Linux, macOS e Windows (Python).
- Integracao com Lighthouse e opcional.
- Sem Lighthouse: usa somente metricas locais (HTTP/HTML/headers).
- Com Lighthouse: combina score local + score browser-level.

## Instalacao

```bash
git clone https://github.com/N1ghthill/web-analyzer-cli.git
cd web-analyzer-cli
python -m venv .venv
source .venv/bin/activate  # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Opcional para auditoria mais completa de performance/SEO/acessibilidade:

```bash
npm install -g lighthouse
```

## Uso rapido

```bash
# Basico
python main.py https://example.com

# Full audit com score por criterio + score geral
python main.py https://example.com --full

# Full audit em JSON
python main.py https://example.com --full --format json

# Salvar relatorio
python main.py https://example.com --full --format json --report ./report.json

# Ler varias URLs de um arquivo
python main.py --arquivo urls.txt --full --report ./reports
```

## Formato de saida (modo full)

- `overall_score`
- `criteria.performance.score`
- `criteria.security.score`
- `criteria.seo.score`
- `criteria.accessibility.score`
- `criteria.best_practices.score`
- `lighthouse.available` (true/false)

## Comando instalado via pip

```bash
pip install -e .
web-analyzer https://example.com --full
```

## Documentacao

- `docs/USAGE.md`

## Licenca

MIT (consulte `LICENSE`).
