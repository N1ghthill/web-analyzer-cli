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
    "timeout": 10
  }'
```

Campos do payload:

- `url` (string)
- `mode` (`basic` ou `full`)
- `timeout` (2-60)

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
