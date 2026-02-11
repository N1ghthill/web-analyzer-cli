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

Opcao 1 (recomendada, instala comando global com isolamento):

```bash
pipx install git+https://github.com/N1ghthill/web-analyzer-cli.git
```

Opcao 2 (local no repositorio):

```bash
git clone https://github.com/N1ghthill/web-analyzer-cli.git
cd web-analyzer-cli
python -m venv .venv
source .venv/bin/activate  # no Windows: .venv\Scripts\activate
pip install -e .
```

Opcional para auditoria mais completa de performance/SEO/acessibilidade:

```bash
npm install -g lighthouse
```

## Uso rapido

```bash
# Comandos curtos (apos instalar)
wa https://example.com

# Full audit com score por criterio + score geral
waf https://example.com

# Full audit em JSON
waf https://example.com -j

# Salvar relatorio
waf https://example.com -j -r ./report.json

# Ler varias URLs de um arquivo
wab urls.txt -j -r ./reports
```

Tambem funciona com comando completo:

```bash
web-analyzer https://example.com --full --format json --report ./report.json
```

## Formato de saida (modo full)

- `overall_score`
- `criteria.performance.score`
- `criteria.security.score`
- `criteria.seo.score`
- `criteria.accessibility.score`
- `criteria.best_practices.score`
- `lighthouse.available` (true/false)

## Rodar sem instalar

```bash
python main.py https://example.com --full
```

## Documentacao

- `docs/USAGE.md`

## Licenca

MIT (consulte `LICENSE`).
