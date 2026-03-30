#!/usr/bin/env python3
"""
Gerador de Carrossel para Instagram
Uso: python main.py "tema do carrossel" [fonte]
Exemplo: python main.py "Inteligência Artificial" google
Fontes disponíveis: instagram, twitter, google, linkedin
"""

import sys
import json
import os
from pathlib import Path

# Adiciona o diretório raiz ao path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.utils import carregar_env, carregar_spec, criar_pasta_saida, log
from src.apify import buscar_dados
from src.normalizer import normalizar
from src.unsplash import buscar_imagem_com_fallback
from src.gerador import gerar_carrossel


def main():
    # 1. Validar argumentos (tema obrigatório, fonte opcional com default "google")
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    tema = sys.argv[1]
    fonte = sys.argv[2] if len(sys.argv) > 2 else "google"
    fontes_validas = ["instagram", "twitter", "google", "linkedin"]

    if fonte not in fontes_validas:
        log(f"Fonte '{fonte}' inválida. Use: {fontes_validas}", "ERRO")
        sys.exit(1)

    # Carregar variáveis de ambiente
    carregar_env(str(ROOT / ".env"))
    log(f"Tema: '{tema}' | Fonte: {fonte}")

    # 2. Carregar spec.json e exibir confirmação
    spec = carregar_spec()
    log(f"Spec carregado: canvas {spec['canvas']['largura']}x{spec['canvas']['altura']}, "
        f"{len(spec['tipos_de_slide'])} tipos de slide")

    # 3. Buscar dados reais via Apify
    log("Buscando dados via Apify...")
    dados_brutos = buscar_dados(tema, fonte)
    total = len(dados_brutos.get("resultados", []))
    log(f"Total de itens encontrados: {total}")

    # 4. Normalizar dados - gerar textos dos slides com base nos dados e regras do spec
    log("Normalizando dados e gerando textos dos slides...")
    conteudo = normalizar(dados_brutos, tema, fonte)
    log(f"Slides planejados: {len(conteudo['slides'])}")

    # 5. Buscar imagens no Unsplash
    log("Buscando imagens no Unsplash...")

    # Query genérica do tema para fallback
    query_tema = conteudo.get("query_imagem", tema)

    for i, slide in enumerate(conteudo["slides"]):
        if slide["tipo"] == "capa":
            # CORREÇÃO 1: buscar imagem de fundo para capa
            query_capa = slide.get("query_imagem_capa", "corporate technology future")
            queries_capa = [query_capa, query_tema, "technology business professional", "abstract dark background"]
            url = buscar_imagem_com_fallback(queries_capa, index=0)
            slide["url_imagem"] = url

        elif slide["tipo"] == "corpo":
            # CORREÇÃO 2: fallback em cascata com 4 queries
            query_especifica = slide.get("query_imagem", tema)
            queries = [
                query_especifica,
                query_tema,
                "technology business professional",
                "abstract dark background",
            ]
            url = buscar_imagem_com_fallback(queries, index=i % 10)
            slide["url_imagem"] = url

    # 6. Criar pasta de saída
    pasta_saida = criar_pasta_saida(tema)
    log(f"Pasta de saída: {pasta_saida}")

    # 7. Salvar conteudo.json na pasta de saída
    caminho_json = Path(pasta_saida) / "conteudo.json"
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(conteudo, f, ensure_ascii=False, indent=2)
    log(f"Conteúdo salvo em: {caminho_json}")

    # 8. Gerar os slides como imagens PNG
    log("Gerando slides...")
    caminhos = gerar_carrossel(conteudo, pasta_saida)

    # 9. Exibir resumo
    log("=" * 50)
    log(f"CONCLUÍDO: {len(caminhos)} slides gerados")
    log(f"Pasta: {pasta_saida}")
    for c in caminhos:
        log(f"  > {c}")
    log("=" * 50)


if __name__ == "__main__":
    main()
