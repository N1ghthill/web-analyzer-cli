# USAGE

## Basico

```bash
python main.py https://example.com
```

## Full audit

```bash
python main.py https://example.com --full
```

## Full audit em JSON

```bash
python main.py https://example.com --full --format json
```

## Sem Lighthouse

```bash
python main.py https://example.com --full --no-lighthouse
```

## Timeout customizado

```bash
python main.py https://example.com --full --timeout 20
```

## Lote por arquivo

```bash
python main.py --arquivo urls.txt --full --report ./reports
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
