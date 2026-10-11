# Chatbot de dúvidas · IFRS Campus Viamão

Chatbot que responde perguntas dos estudantes a partir de um arquivo local de
perguntas frequentes (`data/faq.json`). Depois de cada resposta, o aluno avalia
com uma frase; a frase é classificada (positivo, neutro ou negativo) por um
classificador Naive Bayes, e um painel resume as avaliações com TextRank.

## Estrutura

```
api/index.py            API Flask (entrada da Vercel)
chatbot/nlp.py          Pré-processamento: normalização, stopwords, stemming, negação
chatbot/retriever.py    Busca na FAQ: TF-IDF + similaridade do cosseno
chatbot/sentiment.py    Classificador Naive Bayes de sentimento
chatbot/summarizer.py   Sumarização extrativa TextRank
chatbot/storage.py      Armazenamento das avaliações (Upstash Redis ou /tmp)
data/faq.json           Perguntas e respostas (edite aqui)
data/sentimento_treino.json  Frases rotuladas para treinar o classificador
public/index.html       Interface do chat
public/admin.html       Painel com distribuição e resumos
vercel.json             Configuração de deploy
```

## Rodar localmente

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
ADMIN_TOKEN=minha-senha python api/index.py          # Windows (PowerShell): $env:ADMIN_TOKEN="minha-senha"; python api/index.py
```

Chat em http://localhost:5000 e painel em http://localhost:5000/admin.

## Deploy na Vercel

1. Suba a pasta para um repositório no GitHub.
2. Na Vercel, clique em **Add New → Project** e importe o repositório
   (nenhuma configuração de build é necessária).
3. Em **Settings → Environment Variables**, crie `ADMIN_TOKEN` com uma senha
   para o painel `/admin`.
4. **Guardar as avaliações:** o disco da Vercel é temporário. Em
   **Storage / Marketplace**, adicione **Upstash Redis** ao projeto. As variáveis
   `KV_REST_API_URL` e `KV_REST_API_TOKEN` (ou `UPSTASH_REDIS_REST_*`) são
   injetadas automaticamente e o código as usa sem mudanças.
5. Faça o redeploy. Teste `/api/saude`: o campo `armazenamento` deve mostrar `redis`.

Via CLI: `npm i -g vercel && vercel --prod`.

## Personalizar

- **Respostas:** edite `data/faq.json` (`pergunta`, `palavras_chave`, `resposta`).
  As respostas atuais são exemplos genéricos: troque pelas informações oficiais do campus.
- **Sensibilidade da busca:** ajuste `LIMIAR` em `chatbot/retriever.py`.
- **Qualidade do sentimento:** adicione frases rotuladas em
  `data/sentimento_treino.json` (o modelo é treinado ao iniciar).

## Identidade visual

A interface usa a paleta do pôster do projeto: lilás `#AA83E9` (faixas de título), lilás claro `#F4EDFF` (fundos), roxo `#341B5F` (botões, do mascote) e fonte Arial. As cores ficam nas variáveis CSS no início de `public/index.html` e `public/admin.html`.

## Observações

- Só depende de Flask. TF-IDF, Naive Bayes e TextRank estão em Python puro,
  o que mantém o deploy leve e rápido na Vercel.
- Não há limite de requisições no endpoint de avaliação; para uso em
  produção, considere adicionar rate limiting.
