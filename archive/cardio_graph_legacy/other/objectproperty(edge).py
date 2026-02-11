from rdflib import Graph, RDF, RDFS, OWL, URIRef, Namespace

g = Graph()

g.parse("/prj/doctoral_letters/guide/data/ontologies/maxo.owl",format="xml")

from rdflib import Graph, RDF, RDFS, OWL, URIRef, Namespace

# Namespaces
IAO = Namespace("http://purl.obolibrary.org/obo/IAO_")

# Loop through all ObjectProperties
for prop in g.subjects(RDF.type, OWL.ObjectProperty):
    if not isinstance(prop, URIRef):
        continue  # skip blank nodes

    label = next((str(l) for _, _, l in g.triples((prop, RDFS.label, None))), None)
    definition = next((str(d) for _, _, d in g.triples((prop, IAO["0000115"], None))), None)

    print(f"{label or 'No label'}")
    print(f"  Definition: {definition or 'No definition'}\n")
