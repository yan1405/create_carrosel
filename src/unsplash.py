import os
import requests
from pathlib import Path
from src.utils import log


def buscar_imagem(query: str, index: int = 0) -> str | None:
    """
    Busca imagem no Unsplash pelo endpoint GET /search/photos.
    Parâmetros: query, per_page=10, orientation=portrait.
    Retorna a URL do campo results[index].urls.regular (1080px).
    Header: Authorization Client-ID {UNSPLASH_ACCESS_KEY}
    """
    access_key = os.environ.get("UNSPLASH_ACCESS_KEY")
    if not access_key:
        raise EnvironmentError("UNSPLASH_ACCESS_KEY não encontrado nas variáveis de ambiente")

    url = "https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {access_key}"}
    params = {"query": query, "per_page": 10, "orientation": "portrait"}

    log(f"Buscando imagem no Unsplash: '{query}'")
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()

    dados = response.json()
    resultados = dados.get("results", [])

    if not resultados or index >= len(resultados):
        log(f"Nenhuma imagem encontrada para '{query}'", "WARN")
        return None

    image_url = resultados[index]["urls"]["regular"]
    log(f"Imagem encontrada: {image_url[:80]}...")
    return image_url


def buscar_imagem_com_fallback(queries: list[str], index: int = 0) -> str | None:
    """Tenta cada query na lista até encontrar resultado."""
    for query in queries:
        url = buscar_imagem(query, index)
        if url:
            return url
    return None


def baixar_imagem(url: str, caminho_destino: str) -> bool:
    """
    Baixa a imagem da URL e salva no caminho informado.
    Retorna True se bem-sucedido, False se falhar.
    """
    try:
        log(f"Baixando imagem para: {caminho_destino}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        Path(caminho_destino).parent.mkdir(parents=True, exist_ok=True)
        with open(caminho_destino, "wb") as f:
            f.write(response.content)

        log(f"Imagem salva: {caminho_destino}")
        return True
    except Exception as e:
        log(f"Erro ao baixar imagem: {e}", "ERRO")
        return False
