"""Pré-processamento de texto (Fase 1): normalização, tokenização,
remoção de stopwords e stemming leve para o português."""
import re
import unicodedata

STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "da", "do", "das",
    "dos", "em", "no", "na", "nos", "nas", "por", "para", "pra", "com", "e",
    "ou", "que", "se", "ao", "aos", "ate", "como", "qual", "quais", "quando",
    "onde", "quem", "eu", "me", "meu", "minha", "meus", "minhas", "voce", "vc",
    "ele", "ela", "eles", "elas", "sao", "ser", "foi", "era", "tem", "ter",
    "tenho", "faco", "fazer", "posso", "pode", "preciso", "gostaria", "saber",
    "sobre", "isso", "esse", "essa", "este", "esta", "mais", "mas", "ja", "so",
    "la", "ai", "ola", "oi", "bom", "boa", "dia", "tarde", "noite", "favor",
    "pois", "porque", "entao", "ainda", "tambem", "estou",
}

NEGACOES = {"nao", "nunca", "jamais", "nem", "sem", "nada"}

_SUFIXOS = ("mente", "coes", "cao", "oes", "aes", "ais", "eis", "es", "s")


def sem_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalizar(texto: str) -> str:
    texto = sem_acentos(texto.lower())
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def stem(palavra: str) -> str:
    """Stemming leve (heurístico) para aproximar variações como
    matrícula/matricular/matrículas."""
    for suf in _SUFIXOS:
        if palavra.endswith(suf) and len(palavra) - len(suf) >= 3:
            palavra = palavra[: -len(suf)]
            break
    if len(palavra) > 6 and palavra.endswith(("ar", "er", "ir")):
        palavra = palavra[:-2]
    if len(palavra) > 4 and palavra[-1] in "aeo":
        palavra = palavra[:-1]
    return palavra


def tokenizar(texto: str) -> list[str]:
    """Tokens para recuperação de FAQ (sem stopwords, com stemming)."""
    return [
        stem(t)
        for t in normalizar(texto).split()
        if t not in STOPWORDS and t not in NEGACOES and len(t) > 1
    ]


def tokenizar_sentimento(texto: str) -> list[str]:
    """Tokens para análise de sentimento. Preserva negação: a palavra
    seguinte a um 'não' vira 'NAO_palavra' (ex.: 'não ajudou' -> 'NAO_ajud')."""
    tokens, negando = [], 0
    for t in normalizar(texto).split():
        if t in NEGACOES:
            negando = 2
            continue
        if t in STOPWORDS or len(t) < 2:
            continue
        s = stem(t)
        tokens.append(f"NAO_{s}" if negando else s)
        negando = max(0, negando - 1)
    return tokens
