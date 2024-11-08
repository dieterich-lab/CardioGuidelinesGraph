import numpy as np
from fuzzywuzzy import fuzz
from langchain_community.utils.math import cosine_similarity


def rerank(embeddings, retrieval_list, question, entities):
    # overlaps = list()
    ratios = list()
    for triplet in retrieval_list:
        # overlaps.append(sum(e in triplet for e in entities) / len(entities))
        ratio = fuzz.partial_token_sort_ratio(question, triplet)
        ratios.append(ratio / 100)
    # quest_embeds = embeddings.embed_documents([question])
    # triplet_embeds = embeddings.embed_documents(retrieval_list)
    # sims = cosine_similarity(quest_embeds, triplet_embeds).mean(0)
    # scores = np.array(sims) + np.array(overlaps)
    ranks = np.array(ratios).argsort()[::-1]
    # ranks = ratios_sims.argsort()[::-1]
    rerank_list = np.array(retrieval_list)[ranks].tolist()
    return rerank_list
