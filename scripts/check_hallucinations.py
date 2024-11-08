import pickle

task = "guidelines"
graphdoc_pkl_path = f"../outputs/{task}_graph_documents.pkl"

graph_documents = list()
print(f"loading from {graphdoc_pkl_path}")
with open(graphdoc_pkl_path, "rb") as f:
    while 1:
        try:
            graph_documents.append(pickle.load(f))
        except EOFError:
            break

print(len(graph_documents))
match, rels = 0, 0
for doc in graph_documents:
    for rel in doc.relationships:
        rels += 1
        src, tgt = rel.source.id, rel.target.id
        if all(
            [str(src) in doc.source.page_content, str(tgt) in doc.source.page_content]
        ):
            match += 1

score = match / rels

print(score)
