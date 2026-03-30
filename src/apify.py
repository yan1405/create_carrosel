import os
import requests
from src.utils import log


ACTORS = {
    "instagram": "apify/instagram-scraper",
    "twitter": "apify/twitter-scraper",
    "google": "apify/google-search-scraper",
    "linkedin": "apify/linkedin-scraper",
}


def buscar_dados(tema: str, fonte: str = "google") -> dict:
    """
    Chama o Actor da Apify correspondente à fonte informada.
    Retorna os dados brutos do Actor.

    Parâmetros:
        tema: assunto a pesquisar (ex: "Inteligência Artificial")
        fonte: uma das chaves de ACTORS (instagram, twitter, google, linkedin)

    Retorna:
        dict com os dados brutos retornados pelo Actor
    """
    if fonte not in ACTORS:
        raise ValueError(f"Fonte '{fonte}' não suportada. Use: {list(ACTORS.keys())}")

    actor_id = ACTORS[fonte]
    log(f"Buscando dados sobre '{tema}' via {fonte} (Actor: {actor_id})")

    input_payload = _montar_payload(tema, fonte)
    resultados = _executar_actor(actor_id, input_payload)

    log(f"Recebidos {len(resultados) if isinstance(resultados, list) else 1} itens do Apify")
    return {"fonte": fonte, "tema": tema, "resultados": resultados}


def _montar_payload(tema: str, fonte: str) -> dict:
    """
    Monta o payload de entrada específico para cada tipo de Actor.
    """
    if fonte == "google":
        return {"queries": tema, "maxPagesPerQuery": 3, "languageCode": "pt-BR"}
    elif fonte == "instagram":
        return {"search": tema, "resultsLimit": 20}
    elif fonte == "twitter":
        return {"searchTerms": [tema], "maxTweets": 20}
    elif fonte == "linkedin":
        return {"searchTerms": tema, "limitPerQuery": 20}
    return {"query": tema}


def _executar_actor(actor_id: str, input_payload: dict) -> dict:
    """
    Executa um Actor na Apify via API REST e aguarda o resultado.
    Endpoint: POST https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items
    Header: Authorization Bearer {APIFY_API_TOKEN}
    """
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        raise EnvironmentError("APIFY_API_TOKEN não encontrado nas variáveis de ambiente")

    # A API exige o formato "user~actor" (til) em vez de "user/actor" na URL
    actor_id_url = actor_id.replace("/", "~")
    url = f"https://api.apify.com/v2/acts/{actor_id_url}/run-sync-get-dataset-items"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    log(f"Executando Actor: {actor_id}")
    response = requests.post(url, json=input_payload, headers=headers, timeout=120)
    response.raise_for_status()

    return response.json()
