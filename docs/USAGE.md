# USAGE

## Instalar como pacote

```bash
pipx install git+https://github.com/N1ghthill/web-analyzer-cli.git
```

Comandos instalados:

- `wa` (modo basico)
- `waf` (full audit)
- `wab` (lote por arquivo em full)
- `web-analyzer` (comando completo)

## CLI

### Basico

```bash
wa https://example.com
```

### Full audit

```bash
waf https://example.com
```

### JSON

```bash
waf https://example.com -j
```

### Sem Lighthouse

```bash
waf https://example.com -n
```

### Timeout

```bash
waf https://example.com -t 20
```

### Lote

```bash
wab urls.txt -j -r ./reports
```

`urls.txt`:

```txt
https://example.com
ruas.dev.br
github.com/N1ghthill
```

## API local

Subir servidor:

```bash
export WEB_ANALYZER_API_KEY="troque-por-uma-chave-forte"
uvicorn app:app --reload
```

Rate limit (opcional):

```bash
export WEB_ANALYZER_RATE_LIMIT_REQUESTS="20"
export WEB_ANALYZER_RATE_LIMIT_WINDOW_SECONDS="60"
```

Tuning de Lighthouse (opcional):

```bash
export WEB_ANALYZER_LIGHTHOUSE_FORM_FACTOR="desktop"
export WEB_ANALYZER_LIGHTHOUSE_THROTTLING_METHOD="provided"
export WEB_ANALYZER_LIGHTHOUSE_MAX_WAIT_MS="30000"
export WEB_ANALYZER_LIGHTHOUSE_CACHE_SECONDS="1800"
```

Healthcheck:

```bash
curl http://127.0.0.1:8000/api/health
```

Analise:

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

Analise pesada em fila (Lighthouse):

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

Consultar status de job:

```bash
curl -H 'x-api-key: troque-por-uma-chave-forte' \
  http://127.0.0.1:8000/api/jobs/<job_id>
```

Campos do payload:

- `url` (string)
- `mode` (`basic` ou `full`)
- `timeout` (2-60)
- `use_lighthouse` (boolean)

Headers obrigatorios:

- `x-api-key`

## WebApp local

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

## Deploy Vercel

```bash
npm i -g vercel
vercel
```

## Score final

A nota final e ponderada:

- Performance: 25%
- Seguranca: 30%
- SEO: 20%
- Acessibilidade: 15%
- Boas praticas: 10%

## Observacoes

- Lighthouse e opcional.
- Sem Lighthouse, as notas continuam sendo calculadas com checks locais.
- Com Lighthouse, as notas ficam mais proximas de um teste de navegador real.
