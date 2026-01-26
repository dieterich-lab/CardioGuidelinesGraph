#!/usr/bin/env python3
"""
Debug script to check if synonyms are being added to the ontology
"""

from rdflib import Graph
from rdflib.namespace import SKOS

# Load the ontology
g = Graph()
g.parse("/prj/doctoral_letters/guide/data/ontologies/cardio_ontology_class.owl")

print(f"Ontology loaded with {len(g)} triples")

# Check for SKOS altLabels
alt_labels = list(g.subject_objects(SKOS.altLabel))
print(f"Found {len(alt_labels)} SKOS altLabel triples")

if alt_labels:
    print("Sample altLabels:")
    for i, (subj, obj) in enumerate(alt_labels[:10]):
        print(f"  {subj} -> {obj}")
else:
    print("No SKOS altLabels found!")

# Check what namespaces are used
print("\nNamespaces in the graph:")
for prefix, namespace in g.namespaces():
    print(f"  {prefix}: {namespace}")

# Check for any triples with "alt" in them
alt_triples = []
for s, p, o in g:
    if "alt" in str(p).lower():
        alt_triples.append((s, p, o))

print(f"\nTriples with 'alt' in predicate: {len(alt_triples)}")
for s, p, o in alt_triples[:5]:
    print(f"  {s} {p} {o}")
