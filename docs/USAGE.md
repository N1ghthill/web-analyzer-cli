# USAGE

## Instalacao como pacote (recomendado)

```bash
pipx install git+https://github.com/N1ghthill/web-analyzer-cli.git
```

Comandos instalados:

- `wa` (modo normal)
- `waf` (full audit)
- `wab` (lote por arquivo, ja em full)

## Basico

```bash
wa https://example.com
```

## Full audit

```bash
waf https://example.com
```

## Full audit em JSON

```bash
waf https://example.com -j
```

## Sem Lighthouse

```bash
waf https://example.com -n
```

## Timeout customizado

```bash
waf https://example.com -t 20
```

## Lote por arquivo

```bash
wab urls.txt -j -r ./reports
```

`urls.txt`:

```txt
https://example.com
ruas.dev.br
github.com/N1ghthill
```

## Score final

A nota final e ponderada pelos pesos abaixo:

- Performance: 25%
- Seguranca: 30%
- SEO: 20%
- Acessibilidade: 15%
- Boas praticas: 10%

## Observacoes

- Lighthouse e opcional.
- Sem Lighthouse, as notas continuam sendo calculadas com checks locais.
- Com Lighthouse, as notas ficam mais proximas de um teste real de navegador.
- Se preferir, ainda pode usar `web-analyzer` ou `python main.py`.
