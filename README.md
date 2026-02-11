# Web Analyzer

Ferramenta em Python com dois modos de uso:

- CLI (`wa`, `waf`, `wab`, `web-analyzer`)
- WebApp + API (`FastAPI`, pronta para Vercel)

## O que a ferramenta faz

- `modo basico`: status HTTP, tempo de resposta, titulo, links, imagens e viewport.
- `modo full`: auditoria com nota de `0-100` por criterio e nota geral ponderada.

Pesos da nota geral (modo full):
- Performance (`25%`)
- Seguranca (`30%`)
- SEO (`20%`)
- Acessibilidade (`15%`)
- Boas praticas (`10%`)

## Compatibilidade

- Funciona em Linux, macOS e Windows (Python).
- Integracao com Lighthouse e opcional.
- Sem Lighthouse: usa metricas locais (HTTP/HTML/headers).
- Com Lighthouse: combina score local + score browser-level.

## Instalacao

Opcao 1 (recomendada):

```bash
pipx install git+https://github.com/N1ghthill/web-analyzer-cli.git
```

Opcao 2 (local no repositorio):

```bash
git clone https://github.com/N1ghthill/web-analyzer-cli.git
cd web-analyzer-cli
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

Opcional para auditoria mais completa:

```bash
npm install -g lighthouse
```

## CLI rapido

```bash
# Basico
wa https://example.com

# Full audit
waf https://example.com

# Full audit em JSON
waf https://example.com -j

# Salvar relatorio
waf https://example.com -j -r ./report.json

# Lote por arquivo
wab urls.txt -j -r ./reports
```

Tambem funciona com comando completo:

```bash
web-analyzer https://example.com --full --format json --report ./report.json
```

## WebApp + API local

Suba o servidor local:

```bash
uvicorn app:app --reload
```

Acesse no navegador:

- `http://127.0.0.1:8000/` (WebApp)
- `http://127.0.0.1:8000/docs` (Swagger)

Endpoints principais:

- `GET /api/health`
- `POST /api/analyze`
- `GET /api/jobs/{job_id}` (para jobs em fila)

Configuracao obrigatoria para uso da API:

```bash
export WEB_ANALYZER_API_KEY="troque-por-uma-chave-forte"
```

Rate limit (opcional):

```bash
export WEB_ANALYZER_RATE_LIMIT_REQUESTS="20"
export WEB_ANALYZER_RATE_LIMIT_WINDOW_SECONDS="60"
```

Tuning de Lighthouse (opcional, recomendado no Vercel para mais velocidade):

```bash
export WEB_ANALYZER_LIGHTHOUSE_FORM_FACTOR="desktop"          # mobile|desktop
export WEB_ANALYZER_LIGHTHOUSE_THROTTLING_METHOD="provided"   # simulate|provided|devtools
export WEB_ANALYZER_LIGHTHOUSE_MAX_WAIT_MS="30000"
export WEB_ANALYZER_LIGHTHOUSE_CACHE_SECONDS="1800"
```

Exemplo API com `curl`:

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H 'x-api-key: troque-por-uma-chave-forte' \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://example.com",
    "mode": "full",
    "timeout": 10,
    "use_lighthouse": false
  }'
```

Exemplo de request pesada (Lighthouse em fila):

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H 'x-api-key: troque-por-uma-chave-forte' \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://example.com",
    "mode": "full",
    "timeout": 20,
    "use_lighthouse": true
  }'
```

Se a resposta vier com `queued: true`, consulte:

```bash
curl -H 'x-api-key: troque-por-uma-chave-forte' \
  http://127.0.0.1:8000/api/jobs/<job_id>
```

## Deploy no Vercel

Este repo ja inclui `app.py` como entrypoint ASGI.

```bash
npm i -g vercel
vercel
```

Depois do deploy:

- `https://seu-projeto.vercel.app/` (WebApp)
- `https://seu-projeto.vercel.app/api/health`
- `https://seu-projeto.vercel.app/api/analyze`
- `https://seu-projeto.vercel.app/api/jobs/{job_id}`

No Vercel, configure as variaveis de ambiente:

- `WEB_ANALYZER_API_KEY` (obrigatoria)
- `WEB_ANALYZER_RATE_LIMIT_REQUESTS` (opcional)
- `WEB_ANALYZER_RATE_LIMIT_WINDOW_SECONDS` (opcional)
- `WEB_ANALYZER_LIGHTHOUSE_FORM_FACTOR` (opcional)
- `WEB_ANALYZER_LIGHTHOUSE_THROTTLING_METHOD` (opcional)
- `WEB_ANALYZER_LIGHTHOUSE_MAX_WAIT_MS` (opcional)
- `WEB_ANALYZER_LIGHTHOUSE_CACHE_SECONDS` (opcional)

## Seguranca da API

A API aplica validacoes para reduzir SSRF:

- bloqueia `localhost`, `.local`, IPs privados/loopback/link-local
- bloqueia hosts que resolvem DNS para IP interno
- permite apenas `http` e `https`
- bloqueia URL com credenciais embutidas

## Formato de saida (modo full)

- `overall_score`
- `criteria.performance.score`
- `criteria.security.score`
- `criteria.seo.score`
- `criteria.accessibility.score`
- `criteria.best_practices.score`
- `lighthouse.available`

## Documentacao

- `docs/USAGE.md`

## Licenca

MIT (consulte `LICENSE`).
