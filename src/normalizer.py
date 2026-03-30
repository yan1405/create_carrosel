import os
import re
import unicodedata
from src.utils import log, carregar_spec


def normalizar(dados_brutos: dict, tema: str, fonte: str) -> dict:
    """
    Recebe dados brutos de qualquer Actor da Apify e retorna
    o formato padrão de slides para o gerador.

    Gera exatamente 7 slides com progressão narrativa:
    1. Capa (gancho)
    2. O Antes (contexto/problema)
    3. A Virada (o que mudou)
    4. A Prova (dado concreto)
    5. A Aplicação (prática)
    6. O Futuro (tendência)
    7. CTA
    """
    carregar_spec()
    handle = os.environ.get("PERFIL_HANDLE", "@yan_guilhermex")

    # Extrair todos os insights brutos
    insights = _extrair_insights(dados_brutos, fonte)
    log(f"Extraidos {len(insights)} insights dos dados brutos")

    # Extrair fatos estruturados dos dados brutos
    fatos = _extrair_fatos(insights, tema)
    log(f"Fatos extraidos: {len(fatos['numeros'])} numeros, "
        f"{len(fatos['problemas'])} problemas, {len(fatos['mudancas'])} mudancas, "
        f"{len(fatos['aplicacoes'])} aplicacoes, {len(fatos['tendencias'])} tendencias, "
        f"{len(fatos['entidades'])} entidades")

    # Montar narrativa progressiva com fatos reais
    slides = _montar_narrativa(tema, fatos, insights)

    conteudo = {
        "tema": tema,
        "fonte": fonte,
        "handle": handle,
        "query_imagem": tema,
        "slides": slides,
    }

    log(f"Conteudo normalizado: {len(slides)} slides gerados")
    return conteudo


# ─────────────────────────────────────────────
# Extração de fatos estruturados
# ─────────────────────────────────────────────

def _extrair_fatos(insights: list[dict], tema: str) -> dict:
    """
    Analisa todos os insights e extrai fatos categorizados:
    - numeros: percentuais, valores, estatísticas
    - problemas: dores, limitações, desafios mencionados
    - mudancas: transformações, inovações, novidades
    - aplicacoes: casos práticos, ferramentas, exemplos reais
    - tendencias: previsões, futuro, próximos passos
    - entidades: nomes de empresas, pessoas, produtos
    - frases_uteis: frases completas extraídas dos dados (>8 palavras)
    """
    fatos = {
        "numeros": [],
        "problemas": [],
        "mudancas": [],
        "aplicacoes": [],
        "tendencias": [],
        "entidades": [],
        "frases_uteis": [],
    }

    for insight in insights:
        titulo = insight.get("titulo", "")
        desc = insight.get("descricao", "")
        texto_completo = f"{titulo}. {desc}".strip()

        # Extrair números e estatísticas (excluir datas)
        nums = re.findall(r"\d[\d.,]*\s*%", texto_completo)
        for n in nums:
            if not _e_data(texto_completo, n):
                fatos["numeros"].append({"valor": n.strip(), "contexto": _frase_em_torno(texto_completo, n)})

        nums_grandes = re.findall(r"\b\d{3,}[\d.,]*\b", texto_completo)
        for n in nums_grandes:
            if not _e_data(texto_completo, n) and n not in [x["valor"] for x in fatos["numeros"]]:
                fatos["numeros"].append({"valor": n, "contexto": _frase_em_torno(texto_completo, n)})

        # Extrair entidades (nomes próprios, empresas)
        entidades = re.findall(r"\b[A-Z][a-záéíóúãõâêîôûç]+(?:\s+[A-Z][a-záéíóúãõâêîôûç]+)*\b", texto_completo)
        stopwords_ent = {"Como", "Qual", "Por", "Que", "Este", "Esta", "Esse", "Essa",
                         "Conheça", "Descubra", "Entenda", "Veja", "Saiba", "Explore",
                         "Neste", "Nesta", "Para", "Pela", "Pelo", "Segundo", "Sobre",
                         "Inteligência", "Artificial", "Tecnologia", "Dados", "Empresas",
                         "Avanço", "Personalização", "Automação", "Eficiência",
                         "Desafios", "Resultados", "Nova", "Novo", "Mais"}
        for ent in entidades:
            if ent not in stopwords_ent and len(ent) > 3:
                fatos["entidades"].append(ent)

        # Classificar frases por categoria
        texto_lower = _remover_acentos(texto_completo.lower())

        palavras_problema = ["antes", "problema", "desafio", "dificuldade", "limitacao",
                             "manual", "lento", "ineficien", "custoso", "falta",
                             "sem tecnologia", "antigamente", "trabalho repetitivo",
                             "erro humano", "gargalo", "burocracia"]
        palavras_mudanca = ["transformou", "revolucion", "mudou", "chegou", "surgiu",
                            "introduziu", "adotou", "implementou", "comecou", "lancou",
                            "inovacao", "disruptiv", "virada", "marco", "generativa"]
        palavras_aplicacao = ["pratica", "exemplo", "caso", "empresa", "automacao",
                              "ferramenta", "processo", "implementacao", "solucao",
                              "workflow", "produtividade", "decisao", "analise", "dados"]
        palavras_tendencia = ["futuro", "tendencia", "previsao", "2025", "2026", "2027",
                              "proximo", "vai", "sera", "crescer", "expandir", "projecao",
                              "estimativa", "esperado", "previsto"]

        if any(p in texto_lower for p in palavras_problema):
            fatos["problemas"].append(_limpar_frase(texto_completo))
        if any(p in texto_lower for p in palavras_mudanca):
            fatos["mudancas"].append(_limpar_frase(texto_completo))
        if any(p in texto_lower for p in palavras_aplicacao):
            fatos["aplicacoes"].append(_limpar_frase(texto_completo))
        if any(p in texto_lower for p in palavras_tendencia):
            fatos["tendencias"].append(_limpar_frase(texto_completo))

        # Guardar frases úteis completas (de descrições com >8 palavras)
        for frase in re.split(r"[.!?]", desc):
            frase = frase.strip()
            if len(frase.split()) >= 8 and len(frase.split()) <= 30:
                fatos["frases_uteis"].append(frase)

    # Deduplicar entidades
    fatos["entidades"] = list(dict.fromkeys(fatos["entidades"]))

    return fatos


def _e_data(texto: str, numero: str) -> bool:
    """Verifica se o número faz parte de uma data (ex: '27 de abr', '2025')."""
    numero = numero.strip()
    # Ano isolado (2020-2029)
    if re.match(r"^20[12]\d$", numero):
        return True
    # Dia seguido de "de mês"
    padrao_data = re.compile(
        r"\b" + re.escape(numero) + r"\s+de\s+(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez|janeiro|fevereiro|"
        r"março|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)",
        re.IGNORECASE
    )
    if padrao_data.search(texto):
        return True
    # "de YYYY" logo após o número
    if re.search(re.escape(numero) + r"\s*de\s*20[12]\d", texto):
        return True
    return False


def _frase_em_torno(texto: str, trecho: str) -> str:
    """Extrai a frase que contém o trecho."""
    frases = re.split(r"[.!?]", texto)
    for frase in frases:
        if trecho in frase:
            return frase.strip()
    return texto[:150]


def _limpar_frase(texto: str) -> str:
    """Limpa e trunca frase para uso como conteúdo."""
    texto = re.sub(r"https?://\S+", "", texto)
    texto = re.sub(r"#\w+", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto[:300]


# ─────────────────────────────────────────────
# Montagem da narrativa progressiva
# ─────────────────────────────────────────────

def _montar_narrativa(tema: str, fatos: dict, insights: list[dict]) -> list[dict]:
    """
    Monta os 7 slides com progressão narrativa obrigatória,
    usando fatos reais extraídos dos dados do Apify.
    """
    slides = []
    queries_usadas = set()
    subtitulos_usados = set()
    titulos_usados = set()

    # ── SLIDE 1: CAPA (gancho) ──
    titulo_capa = _gerar_titulo_capa(tema, fatos)
    engajamento = _gerar_engajamento_capa(tema, fatos)
    query_capa = _gerar_query_imagem_capa(tema)
    slides.append({
        "tipo": "capa",
        "titulo": titulo_capa,
        "categoria": tema.upper(),
        "engajamento": engajamento,
        "subtitulo": None,
        "query_imagem_capa": query_capa,
    })

    papeis = ["antes", "virada", "prova", "aplicacao", "futuro"]
    for papel in papeis:
        titulo = _gerar_titulo_papel(tema, fatos, papel, titulos_usados)
        titulos_usados.add(titulo)
        sub = _gerar_subtitulo_narrativo(fatos, papel, tema, subtitulos_usados, titulo_slide=titulo)
        subtitulos_usados.add(sub)
        query = _gerar_query_imagem_papel(papel, tema, queries_usadas)
        queries_usadas.add(query)
        slides.append({
            "tipo": "corpo",
            "titulo": titulo,
            "subtitulo": sub,
            "query_imagem": query,
        })

    # ── SLIDE 7: CTA ──
    slides.append({
        "tipo": "cta",
        "titulo": "Quer crescer com IA? Siga a Crescitech",
        "subtitulo": "Conteudo diario sobre IA para pessoas e negocios",
    })

    return slides


# ─────────────────────────────────────────────
# Geração de títulos por papel narrativo
# ─────────────────────────────────────────────

def _gerar_titulo_papel(tema: str, fatos: dict, papel: str,
                        titulos_usados: set[str] | None = None) -> str:
    """Gera título específico para cada papel na narrativa. Nunca repete."""
    if titulos_usados is None:
        titulos_usados = set()

    entidade = fatos["entidades"][0] if fatos["entidades"] else ""

    def _escolher(opcoes: list[str]) -> str:
        """Escolhe a primeira opção não usada."""
        for op in opcoes:
            if op not in titulos_usados:
                return op
        return opcoes[0]

    if papel == "antes":
        candidatos = []
        if fatos["problemas"]:
            titulo = _extrair_titulo_de_frase(fatos["problemas"][0])
            if titulo and titulo not in titulos_usados:
                candidatos.append(_limitar_palavras(titulo, 10))
        candidatos.extend([
            "Antes da IA, o mundo corporativo era outro",
            "Processos manuais dominavam as empresas",
            "O que as empresas faziam sem inteligencia artificial",
        ])
        return _escolher(candidatos)

    if papel == "virada":
        candidatos = []
        if fatos["mudancas"]:
            for frase in fatos["mudancas"][:3]:
                titulo = _extrair_titulo_de_frase(frase)
                if titulo and titulo not in titulos_usados:
                    candidatos.append(_limitar_palavras(titulo, 10))
        if entidade:
            candidatos.append(_limitar_palavras(f"Quando {entidade} trouxe a IA para os negocios", 10))
        candidatos.extend([
            "A IA generativa chegou e mudou as regras",
            "O momento em que a tecnologia virou o jogo",
            "A inteligencia artificial entrou nas empresas",
        ])
        return _escolher(candidatos)

    if papel == "prova":
        candidatos = []
        if fatos["numeros"]:
            num = fatos["numeros"][0]
            ctx = num["contexto"]
            titulo = _extrair_titulo_de_frase(ctx)
            if titulo and titulo not in titulos_usados:
                candidatos.append(_limitar_palavras(titulo, 10))
            candidatos.append(_limitar_palavras(f"{num['valor']} de impacto real nos negocios", 10))
        candidatos.extend([
            "Resultados concretos de empresas que adotaram IA",
            "Os dados comprovam a transformacao digital",
            "Numeros reais mostram o impacto da IA",
        ])
        return _escolher(candidatos)

    if papel == "aplicacao":
        candidatos = []
        if fatos["aplicacoes"]:
            for frase in fatos["aplicacoes"][:3]:
                titulo = _extrair_titulo_de_frase(frase)
                if titulo and titulo not in titulos_usados:
                    candidatos.append(_limitar_palavras(titulo, 10))
        candidatos.extend([
            "Automacao, decisoes e dados na pratica",
            "Como a IA funciona no dia a dia corporativo",
            "Da teoria para a realidade das empresas",
        ])
        return _escolher(candidatos)

    if papel == "futuro":
        candidatos = []
        if fatos["tendencias"]:
            for frase in fatos["tendencias"][:3]:
                titulo = _extrair_titulo_de_frase(frase)
                if titulo and titulo not in titulos_usados:
                    candidatos.append(_limitar_palavras(titulo, 10))
        candidatos.extend([
            "O proximo passo da IA nas empresas",
            "Quem nao se adaptar vai ficar para tras",
            "O futuro corporativo ja esta sendo escrito",
        ])
        return _escolher(candidatos)

    return _encurtar_tema(tema)


def _extrair_titulo_de_frase(frase: str) -> str | None:
    """
    Extrai um título curto e impactante de uma frase longa.
    Pega o trecho antes do primeiro ponto/vírgula, limpa sufixos de fonte.
    """
    # Pegar a primeira parte antes de ponto
    partes = re.split(r"[.;!?]", frase)
    texto = partes[0].strip() if partes else frase.strip()

    # Limpar prefixos de data: "27 de abr. de 2025 —", "de 2025 —"
    texto = re.sub(
        r"^(\d{1,2}\s+)?de\s+\w{3,10}\.?\s*(de\s+\d{4})?\s*[-–—]\s*",
        "", texto
    ).strip()
    # Limpar prefixos de tempo relativo: "há 3 dias —"
    texto = re.sub(
        r"^h[aá]\s+\d+\s+\w+\s*[-–—·]\s*",
        "", texto, flags=re.IGNORECASE
    ).strip()

    # Limpar sufixos de fonte
    texto = re.sub(r"\s*[-–—|]\s*[A-Z][\w\s]{0,25}$", "", texto).strip()
    texto = re.sub(r"\s*[-–—|]\s*(Wikip|YouTube|Blog|Forbes|Google|LinkedIn|Medium|Exame|G1|UOL|Folha|Globo)\b.*$",
                   "", texto, flags=re.IGNORECASE).strip()

    # Remover prefixos comuns
    texto = re.sub(r"^(CURSO DE|Aula \d+ [-:])\s*", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"#\w+", "", texto).strip()

    # Traduzir se necessário
    if _parece_ingles(texto):
        texto = _traduzir_titulo(texto)

    # Remover ALL CAPS (converter para title case)
    if texto == texto.upper() and len(texto) > 5:
        texto = texto.title()

    if len(texto.split()) < 3:
        return None

    return _limitar_palavras(texto, 10)


# ─────────────────────────────────────────────
# Geração de subtítulos narrativos
# ─────────────────────────────────────────────

def _gerar_subtitulo_narrativo(fatos: dict, papel: str, tema: str,
                                usados: set[str], titulo_slide: str = "") -> str:
    """
    Gera subtítulo usando dados reais do Apify, específico para cada papel.
    Nunca usa templates genéricos. Garante unicidade.
    Evita sobreposição com o título do mesmo slide.
    """
    candidatos = []

    if papel == "antes":
        for frase in fatos["problemas"]:
            sub = _extrair_subtitulo_de_frase(frase, evitar=titulo_slide)
            if sub and sub not in usados:
                candidatos.append(sub)
        for frase in fatos["frases_uteis"]:
            if any(p in _remover_acentos(frase.lower()) for p in
                   ["antes", "manual", "sem", "antigo", "tradicional", "limitado"]):
                sub = _limpar_subtitulo(frase)
                if sub and sub not in usados:
                    candidatos.append(sub)
        if not candidatos:
            candidatos = _subtitulos_papel_especifico("antes", tema, fatos)

    elif papel == "virada":
        for frase in fatos["mudancas"]:
            sub = _extrair_subtitulo_de_frase(frase, evitar=titulo_slide)
            if sub and sub not in usados:
                candidatos.append(sub)
        for frase in fatos["frases_uteis"]:
            if any(p in _remover_acentos(frase.lower()) for p in
                   ["transformou", "revolucion", "mudou", "chegou", "inovacao", "generativa"]):
                sub = _limpar_subtitulo(frase)
                if sub and sub not in usados:
                    candidatos.append(sub)
        if not candidatos:
            candidatos = _subtitulos_papel_especifico("virada", tema, fatos)

    elif papel == "prova":
        for num in fatos["numeros"]:
            ctx = num["contexto"]
            sub = _extrair_subtitulo_de_frase(ctx, evitar=titulo_slide)
            if sub and sub not in usados:
                candidatos.append(sub)
        for frase in fatos["frases_uteis"]:
            if re.search(r"\d[\d.,]*\s*%?", frase):
                sub = _limpar_subtitulo(frase)
                if sub and sub not in usados:
                    candidatos.append(sub)
        if not candidatos:
            candidatos = _subtitulos_papel_especifico("prova", tema, fatos)

    elif papel == "aplicacao":
        for frase in fatos["aplicacoes"]:
            sub = _extrair_subtitulo_de_frase(frase, evitar=titulo_slide)
            if sub and sub not in usados:
                candidatos.append(sub)
        for frase in fatos["frases_uteis"]:
            if any(p in _remover_acentos(frase.lower()) for p in
                   ["pratica", "exemplo", "empresa", "automacao", "ferramenta", "processo"]):
                sub = _limpar_subtitulo(frase)
                if sub and sub not in usados:
                    candidatos.append(sub)
        if not candidatos:
            candidatos = _subtitulos_papel_especifico("aplicacao", tema, fatos)

    elif papel == "futuro":
        for frase in fatos["tendencias"]:
            sub = _extrair_subtitulo_de_frase(frase, evitar=titulo_slide)
            if sub and sub not in usados:
                candidatos.append(sub)
        for frase in fatos["frases_uteis"]:
            if any(p in _remover_acentos(frase.lower()) for p in
                   ["futuro", "tendencia", "previsao", "2025", "2026", "proximo", "crescer"]):
                sub = _limpar_subtitulo(frase)
                if sub and sub not in usados:
                    candidatos.append(sub)
        if not candidatos:
            candidatos = _subtitulos_papel_especifico("futuro", tema, fatos)

    # Verificar similaridade com o título do slide
    titulo_palavras = set(_remover_acentos(titulo_slide.lower()).split()) if titulo_slide else set()

    # Retornar o primeiro candidato válido que não repete e não é igual ao título
    for sub in candidatos:
        if sub not in usados and len(sub.split()) >= 8:
            sub_palavras = set(_remover_acentos(sub.lower()).split())
            # Rejeitar se >60% de sobreposição com o título
            if titulo_palavras and sub_palavras:
                overlap = len(sub_palavras & titulo_palavras) / len(sub_palavras)
                if overlap > 0.6:
                    continue
            return sub

    # Último recurso: pegar qualquer frase útil não usada e não similar ao título
    for frase in fatos["frases_uteis"]:
        sub = _limpar_subtitulo(frase)
        if sub and sub not in usados and len(sub.split()) >= 8:
            sub_palavras = set(_remover_acentos(sub.lower()).split())
            if titulo_palavras:
                overlap = len(sub_palavras & titulo_palavras) / len(sub_palavras)
                if overlap > 0.6:
                    continue
            return sub

    # Fallback final por papel (nunca o template genérico antigo)
    return _subtitulos_papel_especifico(papel, tema, fatos)[0]


def _extrair_subtitulo_de_frase(texto: str, evitar: str = "") -> str | None:
    """Extrai um subtítulo limpo de uma frase dos dados brutos.
    Prefere frases que não se sobreponham com 'evitar' (tipicamente o título)."""
    partes = re.split(r"[.!?]", texto)
    evitar_palavras = set(_remover_acentos(evitar.lower()).split()) if evitar else set()

    # Tentar frases que NÃO se sobrepõem com o título
    for parte in partes[1:]:
        sub = _limpar_subtitulo(parte.strip())
        if sub and len(sub.split()) >= 8:
            sub_palavras = set(_remover_acentos(sub.lower()).split())
            if not evitar_palavras or len(sub_palavras & evitar_palavras) / max(len(sub_palavras), 1) < 0.5:
                return sub

    # Tentar a primeira frase se não sobrepõe
    if partes:
        sub = _limpar_subtitulo(partes[0].strip())
        if sub and len(sub.split()) >= 8:
            sub_palavras = set(_remover_acentos(sub.lower()).split())
            if not evitar_palavras or len(sub_palavras & evitar_palavras) / max(len(sub_palavras), 1) < 0.5:
                return sub

    # Último recurso: qualquer frase válida
    for parte in partes:
        sub = _limpar_subtitulo(parte.strip())
        if sub and len(sub.split()) >= 8:
            return sub
    return None


def _limpar_subtitulo(texto: str) -> str | None:
    """Limpa e valida texto como subtítulo."""
    texto = re.sub(r"https?://\S+", "", texto)
    texto = re.sub(r"#\w+", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    texto = re.sub(r"^\.{3}\s*", "", texto)
    texto = re.sub(r"\s*\.{3}\s*$", "", texto)
    texto = re.sub(r"…", "", texto)
    # Remover prefixos de data: "de 2025 —", "27 de abr. de 2025 —"
    texto = re.sub(
        r"^(\d{1,2}\s+)?de\s+\w{3,10}\.?\s*(de\s+\d{4})?\s*[-–—]\s*",
        "", texto
    ).strip()
    # Remover prefixos de tempo relativo: "há 3 dias —", "há 1 semana —"
    texto = re.sub(
        r"^h[aá]\s+\d+\s+\w+\s*[-–—·]\s*",
        "", texto, flags=re.IGNORECASE
    ).strip()
    # Remover "· separadores" soltos no meio
    texto = re.sub(r"\s*·\s*", ". ", texto).strip()
    # Remover vírgula ou ponto final solto no fim
    texto = texto.rstrip(".,;:- ")

    if _parece_ingles(texto):
        texto = _traduzir_descricao(texto)

    # Limitar a 30 palavras
    palavras = texto.split()
    if len(palavras) > 30:
        texto = " ".join(palavras[:30])

    # Não terminar em preposição, artigo ou palavra solta
    finais_ruins = {"de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
                    "o", "a", "os", "as", "um", "uma", "e", "ou", "para", "com", "que", "à"}
    while texto.split() and texto.split()[-1].lower() in finais_ruins:
        partes = texto.split()
        if len(partes) <= 8:
            break
        texto = " ".join(partes[:-1])

    texto = texto.rstrip(".,;:- ")

    if len(texto.split()) < 8:
        return None

    if _parece_fragmento(texto):
        return None

    return texto


def _subtitulos_papel_especifico(papel: str, tema: str, fatos: dict) -> list[str]:
    """
    Fallbacks específicos por papel narrativo, usando entidades/números quando possível.
    Nunca usa o padrão 'Entenda como X pode transformar...'.
    """
    entidade = fatos["entidades"][0] if fatos["entidades"] else "grandes empresas"
    numero = fatos["numeros"][0]["valor"] if fatos["numeros"] else ""

    if papel == "antes":
        return [
            f"Relatorios manuais, decisoes por intuicao e processos que levavam semanas para serem concluidos",
            f"Antes da IA, equipes inteiras gastavam horas em tarefas que hoje um algoritmo resolve em minutos",
            f"Planilhas interminaveis e analises lentas eram o padrao no mundo corporativo antes da automacao",
        ]
    if papel == "virada":
        if entidade != "grandes empresas":
            return [
                f"{entidade} e outras empresas comecaram a integrar IA nos seus processos e os resultados surpreenderam",
                f"A chegada da IA generativa permitiu que empresas como {entidade} automatizassem decisoes complexas",
                f"Ferramentas de inteligencia artificial passaram a fazer em segundos o que antes exigia equipes inteiras",
            ]
        return [
            f"A IA generativa chegou ao mercado corporativo e abriu possibilidades que antes pareciam ficao cientifica",
            f"Ferramentas de inteligencia artificial passaram a fazer em segundos o que antes exigia equipes inteiras",
            f"Empresas que adotaram IA primeiro ganharam vantagem competitiva significativa sobre a concorrencia",
        ]
    if papel == "prova":
        if numero:
            return [
                f"Empresas que adotaram IA relatam {numero} de melhoria em eficiencia operacional e reducao de custos",
                f"Os dados mostram {numero} de ganho real, comprovando que a IA nao e apenas tendencia mas necessidade",
                f"Pesquisas indicam que {numero} dos resultados melhoram quando IA e aplicada de forma estrategica",
            ]
        return [
            f"Empresas que implementaram IA relatam reducao significativa de custos e aumento de produtividade",
            f"Estudos mostram que a automacao inteligente reduz erros operacionais e acelera a tomada de decisao",
            f"Organizacoes com IA integrada entregam resultados ate tres vezes mais rapido que concorrentes tradicionais",
        ]
    if papel == "aplicacao":
        return [
            f"Automacao de processos, analise preditiva e atendimento inteligente ja sao realidade nas empresas",
            f"Na pratica a IA analisa dados em tempo real, antecipa demandas e otimiza operacoes sem intervencao manual",
            f"Do RH ao financeiro, cada departamento corporativo ja tem ferramentas de IA que simplificam rotinas",
        ]
    if papel == "futuro":
        return [
            f"Ate 2027, empresas sem IA integrada terao dificuldade de competir no mercado corporativo",
            f"A proxima onda sera agentes autonomos de IA tomando decisoes operacionais em tempo real",
            f"Quem nao comecar a adaptar seus processos agora vai perder espaco para concorrentes mais ageis",
        ]
    return [f"A transformacao digital continua acelerando e as oportunidades sao reais para quem se posiciona agora"]


# ─────────────────────────────────────────────
# Geração de queries de imagem por papel
# ─────────────────────────────────────────────

def _gerar_query_imagem_papel(papel: str, tema: str, queries_usadas: set[str]) -> str:
    """Gera query de imagem específica para cada papel narrativo."""
    mapa = {
        "antes": ["corporate office paperwork", "business meeting traditional", "manual work office desk",
                   "old office bureaucracy files"],
        "virada": ["AI technology innovation", "digital transformation corporate", "artificial intelligence business",
                    "tech revolution modern office"],
        "prova": ["business analytics dashboard", "data results chart growth", "corporate success metrics",
                   "statistics performance screen"],
        "aplicacao": ["automation technology robot", "AI practical workplace", "smart office technology",
                      "corporate digital tools modern"],
        "futuro": ["future technology city", "innovation forward futuristic", "next generation AI",
                    "tomorrow business vision"],
    }

    opcoes = mapa.get(papel, ["corporate technology modern", "business professional workspace"])
    for query in opcoes:
        if query not in queries_usadas:
            return query
    return opcoes[0]


# ─────────────────────────────────────────────
# Título da capa e engajamento
# ─────────────────────────────────────────────

def _gerar_titulo_capa(tema: str, fatos: dict) -> str:
    """
    Gera o título da capa: impactante, máximo 10 palavras.
    Tenta usar dado concreto dos fatos extraídos.
    """
    # Tentar com número real
    if fatos["numeros"]:
        num = fatos["numeros"][0]
        valor = num["valor"]
        # Construir título com o número
        return _limitar_palavras(f"IA no mundo corporativo: {valor} de mudanca real", 10)

    # Tentar com entidade real
    if fatos["entidades"]:
        ent = fatos["entidades"][0]
        return _limitar_palavras(f"De {ent} ao seu negocio: a IA mudou tudo", 10)

    return _limitar_palavras(tema, 10)


def _gerar_engajamento_capa(tema: str, fatos: dict) -> str:
    """Gera frase curta de engajamento para a capa."""
    tema_lower = _remover_acentos(tema.lower())

    if fatos["numeros"]:
        return "Os numeros que ninguem esta te contando"

    if any(p in tema_lower for p in ["guerra", "conflito", "crise", "ataque"]):
        return "O que voce precisa saber agora"
    if any(p in tema_lower for p in ["marketing", "vendas", "negocio"]):
        return "Estrategias que estao mudando o jogo"
    if any(p in tema_lower for p in ["ia", "inteligencia artificial", "tecnologia", "corporativo"]):
        return "O futuro ja comecou e voce precisa acompanhar"

    return f"Tudo que voce precisa saber sobre {_encurtar_tema(tema)}"


def _gerar_query_imagem_capa(tema: str) -> str:
    """Gera query de imagem para o fundo da capa, em inglês."""
    tema_lower = _remover_acentos(tema.lower())
    mapa = {
        "ia": "corporate technology future AI",
        "inteligencia artificial": "corporate technology future AI",
        "marketing": "digital marketing strategy office",
        "guerra": "geopolitics world crisis dramatic",
        "tecnologia": "futuristic technology city lights",
        "empreendedorismo": "entrepreneur startup modern office",
        "programacao": "coding software developer dark",
        "vendas": "business sales corporate meeting",
        "lideranca": "leadership corporate executive",
        "corporativo": "corporate technology future AI",
    }
    for chave, query in mapa.items():
        if chave in tema_lower:
            return query
    palavras = _extrair_palavras_chave(tema)
    if palavras:
        return " ".join(palavras[:2]) + " professional modern"
    return "corporate technology future"


# ─────────────────────────────────────────────
# Utilitários de texto
# ─────────────────────────────────────────────

def _encurtar_tema(tema: str) -> str:
    """Encurta o tema para no máximo 5 palavras."""
    palavras = tema.split()
    if len(palavras) <= 5:
        return tema
    return " ".join(palavras[:5])


def _limitar_palavras(texto: str, maximo: int) -> str:
    """Limita texto a N palavras sem cortar no meio."""
    palavras = texto.split()
    if len(palavras) <= maximo:
        return texto.rstrip(".,;:-")

    texto = " ".join(palavras[:maximo])
    # Não terminar em preposição ou artigo
    finais_ruins = {"de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
                    "o", "a", "os", "as", "um", "uma", "e", "ou", "para", "com", "que"}
    while texto.split() and texto.split()[-1].lower() in finais_ruins:
        palavras_cortadas = texto.split()
        if len(palavras_cortadas) <= 3:
            break
        texto = " ".join(palavras_cortadas[:-1])

    return texto.rstrip(".,;:-")


def _parece_fragmento(texto: str) -> bool:
    """Detecta fragmentos inválidos."""
    if re.match(r"^\d{1,2}\s+de\s+\w{3,10}(\s+de\s+\d{4})?$", texto, re.IGNORECASE):
        return True
    if re.match(r"^[\d.,/%\s]+$", texto.strip()):
        return True
    return False


# ─────────────────────────────────────────────
# Extração de insights por fonte
# ─────────────────────────────────────────────

def _extrair_insights(dados_brutos: dict, fonte: str) -> list[dict]:
    """Extrai pares {titulo, descricao} dos dados brutos."""
    resultados = dados_brutos.get("resultados", [])
    insights = []
    if not isinstance(resultados, list):
        return insights

    if fonte == "google":
        insights = _extrair_google(resultados)
    elif fonte == "instagram":
        insights = _extrair_instagram(resultados)
    elif fonte == "twitter":
        insights = _extrair_twitter(resultados)
    elif fonte == "linkedin":
        insights = _extrair_linkedin(resultados)

    return insights


def _extrair_google(resultados: list) -> list[dict]:
    """Extrai insights dos organicResults do Google Search Scraper."""
    insights = []
    for pagina in resultados:
        if not isinstance(pagina, dict):
            continue
        organicos = pagina.get("organicResults", [])
        for item in organicos:
            titulo = item.get("title", "")
            descricao = item.get("description", "")
            if titulo:
                insights.append({"titulo": titulo, "descricao": descricao})
    return insights


def _extrair_instagram(resultados: list) -> list[dict]:
    insights = []
    for item in resultados:
        if not isinstance(item, dict):
            continue
        caption = item.get("caption", "")
        if caption:
            partes = caption.split(".", 1)
            titulo = partes[0].strip()[:150]
            descricao = partes[1].strip()[:300] if len(partes) > 1 else ""
            insights.append({"titulo": titulo, "descricao": descricao})
    return insights


def _extrair_twitter(resultados: list) -> list[dict]:
    insights = []
    for item in resultados:
        if not isinstance(item, dict):
            continue
        text = item.get("full_text") or item.get("text", "")
        if text:
            partes = text.split(".", 1)
            titulo = partes[0].strip()[:150]
            descricao = partes[1].strip()[:300] if len(partes) > 1 else ""
            insights.append({"titulo": titulo, "descricao": descricao})
    return insights


def _extrair_linkedin(resultados: list) -> list[dict]:
    insights = []
    for item in resultados:
        if not isinstance(item, dict):
            continue
        titulo = item.get("title") or item.get("text", "")
        descricao = item.get("text", "")
        if titulo:
            insights.append({"titulo": titulo[:150], "descricao": descricao[:300]})
    return insights


# ─────────────────────────────────────────────
# Detecção e tradução de idioma
# ─────────────────────────────────────────────

def _parece_ingles(texto: str) -> bool:
    """Heurística simples para detectar texto em inglês."""
    palavras_en = {"the", "is", "are", "was", "were", "for", "and", "with",
                   "you", "your", "how", "what", "why", "this", "that",
                   "from", "about", "into", "have", "has", "can", "will",
                   "not", "but", "all", "been", "their", "which", "when",
                   "just", "like", "more", "than", "them", "its",
                   "beginners", "guide", "learn", "everything", "need",
                   "know", "digital", "marketing", "online", "business",
                   "basics", "beginner", "strategy", "tips"}
    palavras = texto.lower().split()
    if not palavras:
        return False
    contagem_en = sum(1 for p in palavras if p in palavras_en)
    return contagem_en / len(palavras) > 0.3


def _traduzir_titulo(titulo: str) -> str:
    """Traduz padrões comuns de títulos em inglês para português."""
    traducoes = [
        (r"(?i)^how to\b", "Como"),
        (r"(?i)^what is\b", "O que e"),
        (r"(?i)^why\b", "Por que"),
        (r"(?i)^the basics of\b", "O basico de"),
        (r"(?i)^the best\b", "Os melhores"),
        (r"(?i)^top (\d+)\b", r"Top \1"),
        (r"(?i)\bfor beginners\b", "para iniciantes"),
        (r"(?i)\beverything you need to know\b", "tudo que voce precisa saber"),
        (r"(?i)\bbeginner'?s? guide\b", "guia para iniciantes"),
        (r"(?i)\bdigital marketing\b", "Marketing Digital"),
        (r"(?i)\bartificial intelligence\b", "Inteligencia Artificial"),
        (r"(?i)\bmachine learning\b", "Aprendizado de Maquina"),
        (r"(?i)\bsocial media\b", "redes sociais"),
        (r"(?i)\bonline business\b", "negocio online"),
        (r"(?i)\bcontent creation\b", "criacao de conteudo"),
        (r"(?i)\blearn about\b", "aprenda sobre"),
        (r"(?i)\b101\b", "do zero"),
    ]
    texto = titulo
    for padrao, substituto in traducoes:
        texto = re.sub(padrao, substituto, texto)
    return texto


def _traduzir_descricao(descricao: str) -> str:
    """Traduz padrões comuns de descrições em inglês para português."""
    traducoes = [
        (r"(?i)\blearn how to\b", "aprenda como"),
        (r"(?i)\beverything you need to know about\b", "tudo que voce precisa saber sobre"),
        (r"(?i)\bin this video\b", "neste conteudo"),
        (r"(?i)\bin this article\b", "neste conteudo"),
        (r"(?i)\bdigital marketing\b", "marketing digital"),
        (r"(?i)\bartificial intelligence\b", "inteligencia artificial"),
        (r"(?i)\bsocial media\b", "redes sociais"),
        (r"(?i)\bonline business\b", "negocio online"),
        (r"(?i)\byou will learn\b", "voce vai aprender"),
        (r"(?i)\byou can\b", "voce pode"),
        (r"(?i)\bhow to\b", "como"),
    ]
    texto = descricao
    for padrao, substituto in traducoes:
        texto = re.sub(padrao, substituto, texto)
    return texto


# ─────────────────────────────────────────────
# Utilitários
# ─────────────────────────────────────────────

def _remover_acentos(texto: str) -> str:
    """Remove acentos do texto para comparações."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return nfkd.encode("ascii", "ignore").decode("ascii")


def _extrair_palavras_chave(titulo: str) -> list[str]:
    """Extrai substantivos-chave do título."""
    stopwords = {"de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
                 "para", "com", "por", "que", "se", "ou", "um", "uma", "o", "a",
                 "os", "as", "e", "como", "mais", "muito", "este", "esta", "esse",
                 "essa", "the", "is", "are", "for", "and", "with", "you", "your",
                 "how", "what", "why", "this", "that", "from", "about"}
    palavras = re.findall(r"\w+", _remover_acentos(titulo.lower()))
    return [p for p in palavras if p not in stopwords and len(p) > 3]
