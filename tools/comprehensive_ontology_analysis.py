#!/usr/bin/env python3
"""
Comprehensive analysis of the cardio ontology to evaluate its suitability
as a knowledge base for entity linking.
"""

import re
from collections import Counter, defaultdict

import rdflib
from rdflib.namespace import OWL, RDF, RDFS, SKOS


def comprehensive_ontology_analysis():
    ontology_path = (
        "/prj/doctoral_letters/guide/data/ontologies/cardio_ontology_class.owl"
    )

    print("=" * 80)
    print("COMPREHENSIVE CARDIO ONTOLOGY ANALYSIS")
    print("=" * 80)

    print(f"Loading ontology from: {ontology_path}")
    g = rdflib.Graph()
    g.parse(ontology_path)

    print(f"Ontology loaded with {len(g)} triples")

    # Basic statistics
    classes = list(g.subjects(RDF.type, OWL.Class))
    properties = list(g.subjects(RDF.type, OWL.ObjectProperty)) + list(
        g.subjects(RDF.type, OWL.DatatypeProperty)
    )
    individuals = list(g.subjects(RDF.type, OWL.NamedIndividual))

    print("\n=== BASIC STATISTICS ===")
    print(f"Total classes: {len(classes)}")
    print(f"Total properties: {len(properties)}")
    print(f"Total individuals: {len(individuals)}")
    print(f"Total triples: {len(g)}")

    # Analyze class labels and synonyms
    print("\n=== LABEL AND SYNONYM ANALYSIS ===")
    labels_count = 0
    alt_labels_count = 0
    classes_with_labels = 0
    classes_with_alt_labels = 0

    label_lengths = []
    alt_label_lengths = []

    for class_uri in classes:
        has_label = False
        has_alt_label = False

        # Primary labels
        for label in g.objects(class_uri, RDFS.label):
            labels_count += 1
            has_label = True
            label_lengths.append(len(str(label)))

        # Alternative labels/synonyms
        for alt_label in g.objects(class_uri, SKOS.altLabel):
            alt_labels_count += 1
            has_alt_label = True
            alt_label_lengths.append(len(str(alt_label)))

        if has_label:
            classes_with_labels += 1
        if has_alt_label:
            classes_with_alt_labels += 1

    print(
        f"Classes with primary labels: {classes_with_labels}/{len(classes)} ({classes_with_labels/len(classes)*100:.1f}%)"
    )
    print(
        f"Classes with alternative labels: {classes_with_alt_labels}/{len(classes)} ({classes_with_alt_labels/len(classes)*100:.1f}%)"
    )
    print(f"Total primary labels: {labels_count}")
    print(f"Total alternative labels: {alt_labels_count}")
    print(
        f"Average label length: {sum(label_lengths)/len(label_lengths):.1f} characters"
        if label_lengths
        else "No labels found"
    )
    print(
        f"Average alt label length: {sum(alt_label_lengths)/len(alt_label_lengths):.1f} characters"
        if alt_label_lengths
        else "No alt labels found"
    )

    # Analyze hierarchical structure
    print("\n=== HIERARCHICAL STRUCTURE ANALYSIS ===")
    subclass_relationships = list(g.subject_objects(RDFS.subClassOf))
    print(f"Subclass relationships: {len(subclass_relationships)}")

    # Find root classes (classes that are not subclasses of anything)
    subclasses = set()
    for subj, obj in subclass_relationships:
        subclasses.add(subj)

    root_classes = [cls for cls in classes if cls not in subclasses]
    print(f"Root classes: {len(root_classes)}")

    # Analyze depth of hierarchy
    depths = {}

    def get_depth(cls, visited=None):
        if visited is None:
            visited = set()
        if cls in visited:
            return 0  # Avoid cycles
        visited.add(cls)

        parents = list(g.objects(cls, RDFS.subClassOf))
        if not parents:
            return 0
        return 1 + max(get_depth(parent, visited.copy()) for parent in parents)

    max_depth = 0
    for cls in classes:
        depth = get_depth(cls)
        depths[cls] = depth
        max_depth = max(max_depth, depth)

    print(f"Maximum hierarchy depth: {max_depth}")
    avg_depth = sum(depths.values()) / len(depths) if depths else 0
    print(f"Average hierarchy depth: {avg_depth:.2f}")

    # Cardiovascular concept coverage analysis
    print("\n=== CARDIOVASCULAR CONCEPT COVERAGE ===")

    cardio_keywords = [
        # Heart conditions
        "heart",
        "cardiac",
        "cardio",
        "myocardial",
        "ventricular",
        "atrial",
        # Blood vessels
        "vascular",
        "artery",
        "vein",
        "aortic",
        "coronary",
        "peripheral",
        # Blood pressure
        "hypertension",
        "hypotension",
        "pressure",
        # Heart failure types
        "hfref",
        "hfrEF",
        "HFrEF",
        "hfpef",
        "HFpEF",
        "HF-PEF",
        # Arrhythmias
        "arrhythmia",
        "fibrillation",
        "tachycardia",
        "bradycardia",
        # Valvular diseases
        "valve",
        "stenosis",
        "regurgitation",
        "insufficiency",
        # Other cardiac conditions
        "ischemia",
        "infarct",
        "angina",
        "cardiomyopathy",
        "pericarditis",
        # Risk factors
        "cholesterol",
        "lipid",
        "diabetes",
        "obesity",
        # Procedures and treatments
        "angioplasty",
        "stent",
        "bypass",
        "transplant",
        "catheterization",
    ]

    coverage_stats = defaultdict(int)
    covered_concepts = set()

    for class_uri in classes:
        labels = []
        for label in g.objects(class_uri, RDFS.label):
            labels.append(str(label).lower())
        for alt_label in g.objects(class_uri, SKOS.altLabel):
            labels.append(str(alt_label).lower())

        for label in labels:
            for keyword in cardio_keywords:
                if keyword.lower() in label:
                    coverage_stats[keyword] += 1
                    covered_concepts.add(str(class_uri))
                    break

    print(
        f"Cardiovascular concepts covered: {len(covered_concepts)}/{len(classes)} ({len(covered_concepts)/len(classes)*100:.1f}%)"
    )
    print("\nTop cardiovascular keywords found:")
    sorted_keywords = sorted(coverage_stats.items(), key=lambda x: x[1], reverse=True)
    for keyword, count in sorted_keywords[:15]:
        print(f"  {keyword}: {count} concepts")

    # SNOMED CT integration analysis
    print("\n=== SNOMED CT INTEGRATION ANALYSIS ===")
    snomed_references = 0
    snomed_classes = 0

    for class_uri in classes:
        uri_str = str(class_uri)
        if "snomed.info" in uri_str:
            snomed_classes += 1
            # Check for SNOMED ID pattern
            if re.search(r"/id/\d+", uri_str):
                snomed_references += 1

    print(
        f"Classes with SNOMED CT URIs: {snomed_classes}/{len(classes)} ({snomed_classes/len(classes)*100:.1f}%)"
    )
    print(
        f"Classes with SNOMED CT IDs: {snomed_references}/{len(classes)} ({snomed_references/len(classes)*100:.1f}%)"
    )

    # Entity linking suitability assessment
    print("\n=== ENTITY LINKING SUITABILITY ASSESSMENT ===")
    print("Evaluating ontology richness for entity linking...")

    # Criteria for entity linking suitability
    criteria = {
        "Total Concepts": (len(classes) > 500, f"{len(classes)} classes"),
        "Label Coverage": (
            classes_with_labels / len(classes) > 0.8,
            f"{classes_with_labels/len(classes)*100:.1f}% labeled",
        ),
        "Synonym Coverage": (
            classes_with_alt_labels / len(classes) > 0.3,
            f"{classes_with_alt_labels/len(classes)*100:.1f}% with synonyms",
        ),
        "Hierarchical Structure": (
            len(subclass_relationships) > 100,
            f"{len(subclass_relationships)} subclass relationships",
        ),
        "Cardio Coverage": (
            len(covered_concepts) / len(classes) > 0.4,
            f"{len(covered_concepts)/len(classes)*100:.1f}% cardiovascular concepts",
        ),
        "External References": (
            snomed_classes > 50,
            f"{snomed_classes} SNOMED CT references",
        ),
    }

    score = 0
    total_criteria = len(criteria)

    print("\nAssessment Criteria:")
    for criterion, (passed, detail) in criteria.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} {criterion}: {detail}")
        if passed:
            score += 1

    suitability_score = score / total_criteria * 100
    print(
        f"\nOverall Suitability Score: {suitability_score:.1f}% ({score}/{total_criteria} criteria met)"
    )

    if suitability_score >= 80:
        print("🎉 EXCELLENT: Ontology is very suitable for entity linking!")
    elif suitability_score >= 60:
        print("👍 GOOD: Ontology is reasonably suitable for entity linking")
    elif suitability_score >= 40:
        print("⚠️  MODERATE: Ontology may need enhancement for robust entity linking")
    else:
        print("❌ POOR: Ontology needs significant improvement for entity linking")

    # Recommendations
    print("\n=== RECOMMENDATIONS ===")
    recommendations = []

    if classes_with_labels / len(classes) < 0.9:
        recommendations.append("Add primary labels to unlabeled classes")

    if classes_with_alt_labels / len(classes) < 0.5:
        recommendations.append(
            "Add more synonyms/alternative labels for better matching"
        )

    if len(subclass_relationships) < len(classes) * 0.5:
        recommendations.append("Expand hierarchical relationships between concepts")

    if len(covered_concepts) / len(classes) < 0.6:
        recommendations.append("Add more cardiovascular disease concepts")

    if snomed_classes < len(classes) * 0.5:
        recommendations.append(
            "Increase integration with SNOMED CT or other standard vocabularies"
        )

    if recommendations:
        print("Recommendations for improvement:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    else:
        print("No major recommendations - ontology is well-structured!")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    comprehensive_ontology_analysis()
