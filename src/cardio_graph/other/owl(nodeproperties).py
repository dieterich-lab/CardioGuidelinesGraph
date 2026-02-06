from rdflib import Graph,RDF, RDFS, OWL, URIRef

g = Graph()

g.parse("/prj/doctoral_letters/guide/data/ontologies/cvdo.owl",format="xml")

IAO_0000115 = URIRef("http://purl.obolibrary.org/obo/IAO_0000115")

for s in g.subjects(RDF.type, OWL.Class):
    # Get label (rdfs:label)
    label = next((str(l) for _, _, l in g.triples((s, RDFS.label, None))), None)

    # Get definition (IAO_0000115)
    definition = next((str(d) for _, _, d in g.triples((s, IAO_0000115, None))), None)

    print(f"{label or 'No label'} --> {s}")
    print(f"   Definition: {definition or 'No definition'}\n")


print("DONE")