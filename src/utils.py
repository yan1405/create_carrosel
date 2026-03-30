import os
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path


def carregar_env(caminho: str) -> None:
    """Lê o arquivo .env e seta as variáveis de ambiente."""
    env_path = Path(caminho)
    if not env_path.exists():
        raise FileNotFoundError(f"Arquivo .env não encontrado em: {caminho}")

    with open(env_path, "r", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            if "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            os.environ[chave.strip()] = valor.strip()


def criar_pasta_saida(tema: str) -> str:
    """
    Cria e retorna o caminho da pasta de saída no formato:
    output/YYYY-MM-DD_tema-slug/
    Ex: output/2026-03-29_inteligencia-artificial/
    """
    data = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(tema)
    pasta = Path("output") / f"{data}_{slug}"
    pasta.mkdir(parents=True, exist_ok=True)
    return str(pasta)


def slugify(texto: str) -> str:
    """Converte texto para slug: lowercase, sem acentos, espaços viram hífen."""
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = texto.lower().strip()
    texto = re.sub(r"[^\w\s-]", "", texto)
    texto = re.sub(r"[\s_]+", "-", texto)
    texto = re.sub(r"-+", "-", texto)
    texto = texto.strip("-")
    return texto


def log(mensagem: str, nivel: str = "INFO") -> None:
    """Imprime log formatado: [NIVEL] HH:MM:SS mensagem"""
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"[{nivel}] {hora} {mensagem}")


def carregar_spec() -> dict:
    """Lê e retorna o conteúdo de template/spec.json como dicionário."""
    spec_path = Path("template") / "spec.json"
    if not spec_path.exists():
        raise FileNotFoundError(f"spec.json não encontrado em: {spec_path}")

    with open(spec_path, "r", encoding="utf-8") as f:
        return json.load(f)
