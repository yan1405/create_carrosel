# Gerador de Carrossel para Instagram

Automação que gera carrosséis profissionais para Instagram a partir de um tema,
buscando dados reais via Apify e imagens via Unsplash.

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

```bash
python main.py "tema do carrossel" [fonte]
```

Fontes disponíveis: instagram, twitter, google, linkedin
Fonte padrão: google

## Exemplos

```bash
python main.py "Inteligência Artificial"
python main.py "Marketing Digital" instagram
python main.py "Python para iniciantes" twitter
```

## Estrutura

- `template/spec.json` → especificação imutável do design
- `template/slides/`   → prints de referência do template
- `src/`               → módulos do sistema
- `fonts/`             → fontes BricolageGrotesque
- `output/`            → slides gerados (uma pasta por execução)

## Fluxo

```
Tema → Apify (dados reais) → Agente (gera textos) →
Unsplash (imagens) → Pillow (renderiza) → PNG
```
