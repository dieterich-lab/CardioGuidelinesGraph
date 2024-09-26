import numpy as np
from fuzzywuzzy import fuzz
from langchain_community.utils.math import cosine_similarity
from langchain_ollama import OllamaEmbeddings

embed_model = "avr/sfr-embedding-mistral"
embeddings = OllamaEmbeddings(
    model=embed_model,
    base_url="http://10.250.135.153:11434",
)


def rerank(entities, retrieval_list, question):
    stat_rank_list = list()
    ratios = list()
    for triplet in retrieval_list:
        ratio = fuzz.ratio(question, triplet)
        stat_rank_list.append((ratio / 100, triplet))
        ratios.append(ratio / 100)
    quest_embeds = embeddings.embed_documents([question])
    triplet_embeds = embeddings.embed_documents(retrieval_list)
    sims = cosine_similarity(quest_embeds, triplet_embeds).mean(0)
    ratios_sims = np.array(sims) + np.array(ratios)
    ranks = ratios_sims.argsort()[::-1]
    rerank_list = np.array(retrieval_list)[ranks].tolist()
    return rerank_list
