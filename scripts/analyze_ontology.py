#!/usr/bin/env python3
"""
Script to analyze the cardio ontology for heart failure related terms.
Checks if HFrEF and related concepts are present in the ontology.
"""

import rdflib
from rdflib.namespace import OWL, RDF, RDFS, SKOS


def analyze_ontology():
    ontology_path = (
        "/prj/doctoral_letters/guide/data/ontologies/cardio_ontology_class.owl"
    )

    print(f"Loading ontology from: {ontology_path}")
    g = rdflib.Graph()
    g.parse(ontology_path)

    print(f"Ontology loaded with {len(g)} triples")

    # Get all classes
    classes = list(g.subjects(RDF.type, OWL.Class))
    print(f"Found {len(classes)} classes")

    # Search for heart failure related terms
    hf_related_terms = []
    search_terms = [
        "hfref",
        "hfrEF",
        "HFrEF",
        "HFREF",
        "heart failure",
        "Heart failure",
        "HEART FAILURE",
        "reduced ejection",
        "ejection fraction",
        "systolic",
        "diastolic",
        "cardiac failure",
        "congestive heart failure",
    ]

    print("\n=== SEARCHING FOR HEART FAILURE RELATED TERMS ===")

    for class_uri in classes:
        # Get labels and synonyms
        labels = []

        # Primary label
        for label in g.objects(class_uri, RDFS.label):
            labels.append(str(label))

        # Alternative labels/synonyms
        for alt_label in g.objects(class_uri, SKOS.altLabel):
            labels.append(str(alt_label))

        # Check if any label contains our search terms
        for label in labels:
            for search_term in search_terms:
                if search_term.lower() in label.lower():
                    hf_related_terms.append(
                        {
                            "uri": str(class_uri),
                            "label": label,
                            "matched_term": search_term,
                        }
                    )
                    break

    print(f"\nFound {len(hf_related_terms)} heart failure related terms:")

    for term in hf_related_terms:
        print(f"  URI: {term['uri']}")
        print(f"  Label: {term['label']}")
        print(f"  Matched: {term['matched_term']}")
        print()

    # Also check for any terms containing "failure"
    print("\n=== ALL TERMS CONTAINING 'FAILURE' ===")
    failure_terms = []
    for class_uri in classes:
        labels = []
        for label in g.objects(class_uri, RDFS.label):
            labels.append(str(label))
        for alt_label in g.objects(class_uri, SKOS.altLabel):
            labels.append(str(alt_label))

        for label in labels:
            if "failure" in label.lower():
                failure_terms.append((str(class_uri), label))

    print(f"Found {len(failure_terms)} terms containing 'failure':")
    for uri, label in failure_terms:
        print(f"  {label} -> {uri}")

    # Check total concepts
    print("\n=== ONTOLOGY SUMMARY ===")
    print(f"Total classes: {len(classes)}")
    print(f"Heart failure related: {len(hf_related_terms)}")
    print(f"Terms with 'failure': {len(failure_terms)}")


if __name__ == "__main__":
    analyze_ontology()
