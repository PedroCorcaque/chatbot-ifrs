"""Busca de respostas no arquivo local de perguntas frequentes
usando TF-IDF + similaridade do cosseno (implementação em Python puro)."""
import json
import math
from collections import Counter
from pathlib import Path

from .nlp import tokenizar

DATA = Path(__file__).resolve().parent.parent / "data" / "faq.json"
LIMIAR = 0.22  # abaixo disso o bot admite que não encontrou resposta


class FAQ:
    def __init__(self, caminho: Path = DATA):
        with open(caminho, encoding="utf-8") as f:
            self.itens = json.load(f)
        docs = []
        for it in self.itens:
            # pergunta e palavras-chave pesam mais que o corpo da resposta
            texto = " ".join(
                [it["pergunta"]] * 2
                + [" ".join(it.get("palavras_chave", []))] * 2
                + [it["resposta"]]
            )
            docs.append(Counter(tokenizar(texto)))
        n = len(docs)
        df = Counter(t for d in docs for t in d)
        self.idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}
        self.vetores = [self._vetor(d) for d in docs]

    def _vetor(self, contagem: Counter) -> dict:
        v = {
            t: (1 + math.log(c)) * self.idf[t]
            for t, c in contagem.items()
            if t in self.idf
        }
        norma = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / norma for t, x in v.items()}

    def buscar(self, consulta: str, k: int = 3):
        q = self._vetor(Counter(tokenizar(consulta)))
        if not q:
            return []
        pontos = []
        for i, v in enumerate(self.vetores):
            s = sum(w * v.get(t, 0.0) for t, w in q.items())
            pontos.append((s, i))
        pontos.sort(reverse=True)
        return [(s, self.itens[i]) for s, i in pontos[:k] if s > 0]

    def responder(self, consulta: str) -> dict:
        achados = self.buscar(consulta)
        if achados and achados[0][0] >= LIMIAR:
            score, item = achados[0]
            return {
                "encontrou": True,
                "resposta": item["resposta"],
                "pergunta_correspondente": item["pergunta"],
                "categoria": item["categoria"],
                "confianca": round(score, 3),
                "sugestoes": [],
            }
        return {
            "encontrou": False,
            "resposta": (
                "Não encontrei essa informação nas perguntas frequentes. "
                "Tente reformular a pergunta ou escolha um dos temas abaixo."
            ),
            "pergunta_correspondente": None,
            "categoria": "sem_resposta",
            "confianca": round(achados[0][0], 3) if achados else 0.0,
            "sugestoes": [it["pergunta"] for _, it in achados]
            or [it["pergunta"] for it in self.itens[:3]],
        }

    def sugestoes(self, n: int = 6):
        return [it["pergunta"] for it in self.itens[:n]]
