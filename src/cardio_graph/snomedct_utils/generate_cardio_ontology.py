#!/usr/bin/env python3
"""
Generate a cardiovascular guideline ontology from SNOMED CT data

This script extracts relevant cardiovascular concepts from SNOMED CT
and generates an OWL/RDF ontology for use with cardiovascular guidelines.
"""

import argparse
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Set, Tuple

import pandas as pd
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS, XSD

from cardio_graph.snomedct_utils.models import SnapDescription, SnapFSN, SnapPref

# Import SnomedExplorer from snomed_query.py
from cardio_graph.snomedct_utils.snomed_query import SnomedExplorer


class CardioOntologyGenerator:
    def get_type_label(self, type_id: str) -> str:
        """Lookup human-readable label for a SNOMED CT typeId."""
        result = (
            self.snomed_explorer.session.query(SnapFSN)
            .filter_by(conceptId=type_id)
            .first()
        )
        if result and hasattr(result, "term"):
            return result.term
        result = (
            self.snomed_explorer.session.query(SnapPref)
            .filter_by(conceptId=type_id)
            .first()
        )
        if result and hasattr(result, "term"):
            return result.term
        result = (
            self.snomed_explorer.session.query(SnapDescription)
            .filter_by(conceptId=type_id)
            .first()
        )
        if result and hasattr(result, "term"):
            return result.term
        return f"snomedRelationship_{type_id}"

    """Generate a cardiovascular ontology from SNOMED CT data"""

    def __init__(
        self,
        output_path: str = "cardio_ontology.owl",
        snomed_host: str = "10.250.135.23",
        snomed_port: str = "3306",
        snomed_user: str = "test_user",
        snomed_password: str = "medicaldatabase",
        snomed_database: str = "snomedct",
        base_uri: str = "http://dieterich-lab.org/ontologies/cardioguidelinesonto/",
        version: str = "0.1.0",
    ):
        """Initialize the ontology generator"""
        self.output_path = output_path
        self.snomed_explorer = SnomedExplorer(
            host=snomed_host,
            port=snomed_port,
            user=snomed_user,
            password=snomed_password,
            database=snomed_database,
        )

        # Initialize RDF graph and namespaces
        self.g = Graph()
        self.base = Namespace(base_uri)
        self.snomed = Namespace("http://snomed.info/id/")
        self.cgo = Namespace(f"{base_uri}#")  # CardioGuidelinesOntology namespace

        # Register namespaces
        self.g.bind("", self.base)
        self.g.bind("cgo", self.cgo)
        self.g.bind("snomed", self.snomed)
        self.g.bind("owl", OWL)
        self.g.bind("rdf", RDF)
        self.g.bind("rdfs", RDFS)
        self.g.bind("xsd", XSD)
        self.g.bind("skos", SKOS)
        self.g.bind("dcterms", DCTERMS)

        # Set ontology metadata
        self.ont_uri = URIRef(base_uri)
        self.g.add((self.ont_uri, RDF.type, OWL.Ontology))
        self.g.add(
            (self.ont_uri, DCTERMS.title, Literal("Cardiovascular Guidelines Ontology"))
        )
        self.g.add(
            (
                self.ont_uri,
                DCTERMS.description,
                Literal(
                    "An ontology for representing knowledge from cardiovascular guidelines, "
                    "with concepts derived from SNOMED CT and enhanced with guideline-specific classes."
                ),
            )
        )
        self.g.add(
            (
                self.ont_uri,
                DCTERMS.created,
                Literal(datetime.now().isoformat(), datatype=XSD.dateTime),
            )
        )
        self.g.add((self.ont_uri, OWL.versionInfo, Literal(version)))

        # Track classes and properties to avoid duplicates
        self.classes = set()
        self.properties = set()
        self.snomed_concepts = {}  # Map from SNOMED concept ID to URI

        # Initialize core classes and properties
        self._init_core_structure()

    def _init_core_structure(self):
        """Initialize the core ontology structure with specified classes and properties"""
        # Add core classes
        core_classes = [
            (
                "ClinicalWorkflow",
                "Represents a multi-step clinical process from guidelines",
            ),
            ("WorkflowStep", "Represents a single step in a clinical workflow"),
            ("ClinicalAction", "A specific clinical action to be taken"),
            ("Purpose", "The reason or goal for a clinical action"),
            ("LogicalJunction", "Abstract node to represent logical groupings"),
            ("Conjunction", "Logical AND grouping of conditions"),
            ("Disjunction", "Logical OR grouping of conditions"),
            (
                "QuantitativePhenotype",
                "A structured way to represent values with operators",
            ),
            (
                "EvidenceStatement",
                "Reified node representing a claim or recommendation",
            ),
            ("EvidenceSource", "Source of clinical evidence"),
            (
                "ContrastingStatement",
                "Special type of evidence statement used for contrasting patterns",
            ),
            ("PatientPhenotype", "Observable characteristic of a patient"),
            ("Guideline", "A clinical guideline document"),
            ("Recommendation", "A specific recommendation within a guideline"),
            # Additional core classes
            ("Medication", "Pharmaceutical treatment or therapy"),
            ("Condition", "Medical condition or disease state"),
            (
                "GuidelineRecommendation",
                "Formal recommendation from a clinical guideline",
            ),
            ("GuidelineSource", "Source of a clinical guideline or recommendation"),
            # Enhanced cardiovascular domain classes
            ("CardiovascularDisease", "Diseases affecting the heart and blood vessels"),
            ("CardiacImaging", "Diagnostic imaging procedures for the heart"),
            (
                "CardiacBiomarker",
                "Laboratory tests used to diagnose cardiac conditions",
            ),
            (
                "CardiacRiskFactor",
                "Factors that increase risk of cardiovascular disease",
            ),
            ("RiskStratification", "Method for categorizing patient risk levels"),
            ("CardiacDevice", "Medical devices used in cardiovascular care"),
            ("CardiacProcedure", "Interventional procedures on the heart"),
            ("AnticoagulationTherapy", "Therapy to prevent blood clotting"),
            ("AntiplateletTherapy", "Therapy to prevent platelet aggregation"),
            ("LipidLoweringTherapy", "Therapy to reduce lipid levels"),
            ("AntihypertensiveTherapy", "Therapy to reduce blood pressure"),
            ("HeartFailureTherapy", "Therapy specific to heart failure"),
            ("EmergencyCardiacCare", "Immediate interventions for cardiac emergencies"),
            ("CardiacRehabilitation", "Structured program for cardiac recovery"),
            ("PreventiveCardiology", "Approaches to prevent cardiovascular disease"),
        ]

        # Add each class to the ontology
        for class_name, description in core_classes:
            class_uri = self.cgo[class_name]
            self.g.add((class_uri, RDF.type, OWL.Class))
            self.g.add((class_uri, RDFS.label, Literal(class_name)))
            self.g.add((class_uri, RDFS.comment, Literal(description)))
            self.classes.add(class_name)

        # Add subclass relationships
        self.g.add(
            (self.cgo["Conjunction"], RDFS.subClassOf, self.cgo["LogicalJunction"])
        )
        self.g.add(
            (self.cgo["Disjunction"], RDFS.subClassOf, self.cgo["LogicalJunction"])
        )
        self.g.add(
            (
                self.cgo["ContrastingStatement"],
                RDFS.subClassOf,
                self.cgo["EvidenceStatement"],
            )
        )

        # Add enhanced class hierarchies for cardiovascular domain
        self.g.add(
            (self.cgo["CardiovascularDisease"], RDFS.subClassOf, self.cgo["Condition"])
        )
        self.g.add(
            (self.cgo["CardiacImaging"], RDFS.subClassOf, self.cgo["ClinicalAction"])
        )
        self.g.add(
            (self.cgo["CardiacProcedure"], RDFS.subClassOf, self.cgo["ClinicalAction"])
        )
        self.g.add(
            (
                self.cgo["CardiacRiskFactor"],
                RDFS.subClassOf,
                self.cgo["PatientPhenotype"],
            )
        )

        # Add therapy class hierarchies
        therapy_classes = [
            "AnticoagulationTherapy",
            "AntiplateletTherapy",
            "LipidLoweringTherapy",
            "AntihypertensiveTherapy",
            "HeartFailureTherapy",
        ]

        for therapy_class in therapy_classes:
            self.g.add(
                (self.cgo[therapy_class], RDFS.subClassOf, self.cgo["ClinicalAction"])
            )

        # Add additional subclass relations
        self.g.add(
            (
                self.cgo["EmergencyCardiacCare"],
                RDFS.subClassOf,
                self.cgo["ClinicalWorkflow"],
            )
        )
        self.g.add(
            (
                self.cgo["CardiacRehabilitation"],
                RDFS.subClassOf,
                self.cgo["ClinicalWorkflow"],
            )
        )
        self.g.add(
            (
                self.cgo["PreventiveCardiology"],
                RDFS.subClassOf,
                self.cgo["ClinicalWorkflow"],
            )
        )

        # Add core object properties
        core_properties = [
            (
                "hasStep",
                "ClinicalWorkflow",
                "WorkflowStep",
                "Relates a clinical workflow to its constituent steps",
            ),
            (
                "hasAction",
                "WorkflowStep",
                "ClinicalAction",
                "Relates a workflow step to the actions to be performed",
            ),
            (
                "hasPurpose",
                "ClinicalAction",
                "Purpose",
                "Relates a clinical action to its intended purpose",
            ),
            (
                "requiresCondition",
                "ClinicalAction",
                None,
                "Links an action to a condition that must be met",
            ),
            (
                "hasOperand",
                "LogicalJunction",
                None,
                "Links a logical junction to its operands",
            ),
            (
                "contrastsWith",
                "EvidenceStatement",
                "ContrastingStatement",
                "Links an evidence statement to a contrasting statement",
            ),
            (
                "isSupportedBy",
                "EvidenceStatement",
                "EvidenceSource",
                "Links an evidence statement to its supporting source",
            ),
            (
                "isRecommendedIn",
                "ClinicalAction",
                "Guideline",
                "Indicates the guideline in which an action is recommended",
            ),
            (
                "hasRecommendation",
                "Guideline",
                "Recommendation",
                "Links a guideline to its recommendations",
            ),
            (
                "hasEvidenceLevel",
                "Recommendation",
                "EvidenceLevel",
                "Specifies the evidence level for a recommendation",
            ),
            # Additional object properties
            (
                "hasIndication",
                "Medication",
                "Condition",
                "Links a medication to a condition it is indicated for",
            ),
            (
                "isRecommendedFor",
                "Medication",
                "PatientPhenotype",
                "Links a medication to a patient phenotype for which it is recommended",
            ),
            (
                "isContraindicatedIn",
                "Medication",
                "Condition",
                "Links a medication to a condition in which it is contraindicated",
            ),
            (
                "hasSource",
                "GuidelineRecommendation",
                "GuidelineSource",
                "Links a guideline recommendation to its source",
            ),
            (
                "makesRecommendation",
                "GuidelineSource",
                "GuidelineRecommendation",
                "Links a guideline source to a recommendation it makes",
            ),
            # Enhanced clinical relationships
            (
                "interactsWith",
                "Medication",
                "Medication",
                "Indicates that two medications have a drug interaction",
            ),
            (
                "hasInteractionSeverity",
                "interactsWith",
                None,
                "Severity level of a drug interaction (property of a property)",
            ),
            (
                "treats",
                "ClinicalAction",
                "Condition",
                "Indicates that a clinical action treats a condition",
            ),
            (
                "prevents",
                "ClinicalAction",
                "Condition",
                "Indicates that a clinical action prevents a condition",
            ),
            (
                "diagnoses",
                "ClinicalAction",
                "Condition",
                "Indicates that a clinical action diagnoses a condition",
            ),
            (
                "hasAlternative",
                "Medication",
                "Medication",
                "Indicates an alternative medication that can be used",
            ),
            (
                "hasPrecondition",
                "ClinicalAction",
                "PatientPhenotype",
                "Patient condition that must be present before the action",
            ),
            (
                "hasFollowUp",
                "ClinicalAction",
                "ClinicalAction",
                "Indicates a follow-up action that should be performed",
            ),
            (
                "isAdministeredWith",
                "Medication",
                "Medication",
                "Medications that are typically administered together",
            ),
            (
                "isContraryTo",
                "Recommendation",
                "Recommendation",
                "Indicates that two recommendations contradict each other",
            ),
            (
                "supersedes",
                "Guideline",
                "Guideline",
                "Indicates that a guideline supersedes an older one",
            ),
        ]

        # Add each property to the ontology
        for prop_name, domain, range_name, description in core_properties:
            prop_uri = self.cgo[prop_name]
            self.g.add((prop_uri, RDF.type, OWL.ObjectProperty))
            self.g.add((prop_uri, RDFS.label, Literal(prop_name)))
            self.g.add((prop_uri, RDFS.comment, Literal(description)))

            if domain:
                self.g.add((prop_uri, RDFS.domain, self.cgo[domain]))
            if range_name:
                self.g.add((prop_uri, RDFS.range, self.cgo[range_name]))

            self.properties.add(prop_name)

        # Add data properties (owl:DatatypeProperty)
        data_properties = [
            ("hasSnomedId", None, XSD.string, "SNOMED CT identifier for a concept"),
            (
                "hasRxNormId",
                "Medication",
                XSD.string,
                "RxNorm identifier for a medication",
            ),
            (
                "hasDosage",
                "Medication",
                XSD.string,
                "Dosage information for a medication",
            ),
            (
                "hasEvidenceLevelString",
                "Recommendation",
                XSD.string,
                "Evidence level as a string (e.g., 'Class I, Level A')",
            ),
            (
                "pageNumber",
                None,
                XSD.integer,
                "Page number where content appears in a guideline document",
            ),
            (
                "hasFrequency",
                "ClinicalAction",
                XSD.string,
                "Frequency of a clinical action (e.g., 'daily', 'twice daily')",
            ),
            (
                "hasAdverseEffect",
                "Medication",
                XSD.string,
                "Common adverse effect of a medication",
            ),
            (
                "hasConcentration",
                "Medication",
                XSD.string,
                "Concentration or strength of a medication",
            ),
            (
                "hasPrevalence",
                "Condition",
                XSD.string,
                "Prevalence of a condition in the population",
            ),
            (
                "hasPriority",
                "ClinicalAction",
                XSD.integer,
                "Priority level of a clinical action (1=highest)",
            ),
            (
                "hasEffectiveDate",
                "Guideline",
                XSD.date,
                "Date when the guideline became effective",
            ),
            (
                "hasReference",
                "EvidenceStatement",
                XSD.string,
                "Bibliographic reference for an evidence statement",
            ),
        ]

        # Add each data property to the ontology
        for prop_name, domain, range_type, description in data_properties:
            prop_uri = self.cgo[prop_name]
            self.g.add((prop_uri, RDF.type, OWL.DatatypeProperty))
            self.g.add((prop_uri, RDFS.label, Literal(prop_name)))
            self.g.add((prop_uri, RDFS.comment, Literal(description)))

            if domain:
                self.g.add((prop_uri, RDFS.domain, self.cgo[domain]))
            self.g.add((prop_uri, RDFS.range, range_type))

            self.properties.add(prop_name)

        # Create hierarchical evidence level structure

        # Create Recommendation Class structure
        evidence_class = self.cgo["EvidenceLevel"]
        self.g.add((evidence_class, RDF.type, OWL.Class))
        self.g.add((evidence_class, RDFS.label, Literal("Evidence Level")))
        self.g.add(
            (
                evidence_class,
                RDFS.comment,
                Literal("Classification of evidence strength in guidelines"),
            )
        )

        # Create subclasses for recommendation classification and evidence quality
        recommendation_class = self.cgo["RecommendationClass"]
        evidence_quality_class = self.cgo["EvidenceQuality"]

        self.g.add((recommendation_class, RDF.type, OWL.Class))
        self.g.add((recommendation_class, RDFS.label, Literal("Recommendation Class")))
        self.g.add(
            (
                recommendation_class,
                RDFS.comment,
                Literal("Classification of recommendation strength"),
            )
        )

        self.g.add((evidence_quality_class, RDF.type, OWL.Class))
        self.g.add((evidence_quality_class, RDFS.label, Literal("Evidence Quality")))
        self.g.add(
            (
                evidence_quality_class,
                RDFS.comment,
                Literal("Classification of evidence quality/level"),
            )
        )

        # Define recommendation classes (ESC/AHA style)
        recommendation_levels = [
            (
                "ClassI",
                "Class I - Evidence and/or general agreement that a treatment is beneficial, useful, effective",
                "Strong recommendation for an intervention",
            ),
            (
                "ClassIIa",
                "Class IIa - Weight of evidence in favor of usefulness/efficacy",
                "Moderate recommendation in favor of intervention",
            ),
            (
                "ClassIIb",
                "Class IIb - Usefulness/efficacy less well established",
                "Weak recommendation in favor of intervention",
            ),
            (
                "ClassIII",
                "Class III - Evidence that treatment is not useful/effective and may be harmful",
                "Recommendation against intervention",
            ),
        ]

        # Add recommendation class individuals
        for level_id, description, short_def in recommendation_levels:
            level_uri = self.cgo[level_id]
            self.g.add((level_uri, RDF.type, recommendation_class))
            self.g.add((level_uri, RDFS.label, Literal(level_id)))
            self.g.add((level_uri, RDFS.comment, Literal(description)))
            self.g.add((level_uri, self.cgo["shortDefinition"], Literal(short_def)))

        # Define evidence quality levels (ESC/AHA style)
        evidence_qualities = [
            (
                "LevelA",
                "Level A - Data derived from multiple randomized clinical trials or meta-analyses",
                "High quality",
            ),
            (
                "LevelB",
                "Level B - Data derived from a single randomized clinical trial or large non-randomized studies",
                "Moderate quality",
            ),
            (
                "LevelC",
                "Level C - Consensus of opinion of the experts and/or small studies, retrospective studies, registries",
                "Low quality",
            ),
        ]

        # Add evidence quality individuals
        for level_id, description, short_def in evidence_qualities:
            level_uri = self.cgo[level_id]
            self.g.add((level_uri, RDF.type, evidence_quality_class))
            self.g.add((level_uri, RDFS.label, Literal(level_id)))
            self.g.add((level_uri, RDFS.comment, Literal(description)))
            self.g.add((level_uri, self.cgo["shortDefinition"], Literal(short_def)))

        # Create combined evidence levels (as they often appear in guidelines)
        combined_levels = [
            ("ClassI_LevelA", "Class I, Level A", "ClassI", "LevelA"),
            ("ClassI_LevelB", "Class I, Level B", "ClassI", "LevelB"),
            ("ClassI_LevelC", "Class I, Level C", "ClassI", "LevelC"),
            ("ClassIIa_LevelA", "Class IIa, Level A", "ClassIIa", "LevelA"),
            ("ClassIIa_LevelB", "Class IIa, Level B", "ClassIIa", "LevelB"),
            ("ClassIIa_LevelC", "Class IIa, Level C", "ClassIIa", "LevelC"),
            ("ClassIIb_LevelA", "Class IIb, Level A", "ClassIIb", "LevelA"),
            ("ClassIIb_LevelB", "Class IIb, Level B", "ClassIIb", "LevelB"),
            ("ClassIIb_LevelC", "Class IIb, Level C", "ClassIIb", "LevelC"),
            ("ClassIII_LevelA", "Class III, Level A", "ClassIII", "LevelA"),
            ("ClassIII_LevelB", "Class III, Level B", "ClassIII", "LevelB"),
            ("ClassIII_LevelC", "Class III, Level C", "ClassIII", "LevelC"),
        ]

        # Add combined evidence level individuals
        for level_id, label, rec_class, evidence_quality in combined_levels:
            level_uri = self.cgo[level_id]
            self.g.add((level_uri, RDF.type, evidence_class))
            self.g.add((level_uri, RDFS.label, Literal(label)))
            self.g.add(
                (level_uri, self.cgo["hasRecommendationClass"], self.cgo[rec_class])
            )
            self.g.add(
                (level_uri, self.cgo["hasEvidenceQuality"], self.cgo[evidence_quality])
            )

        # Add specialized evidence level types for different guideline systems
        guideline_systems = [
            ("ESC", "European Society of Cardiology"),
            ("AHA_ACC", "American Heart Association / American College of Cardiology"),
            ("NICE", "National Institute for Health and Care Excellence"),
        ]

        for system_id, label in guideline_systems:
            system_uri = self.cgo[f"GuidelineSystem_{system_id}"]
            self.g.add((system_uri, RDF.type, self.cgo["GuidelineSystem"]))
            self.g.add((system_uri, RDFS.label, Literal(label)))

    def extract_cardiovascular_concepts(self, limit: int = 1000) -> List[Dict]:
        """Extract cardiovascular concepts from SNOMED CT"""
        print("Extracting cardiovascular concepts from SNOMED CT...")

        # Extract concepts related to cardiovascular conditions - increased limit
        cardio_concepts = self.snomed_explorer.search_cardiovascular_concepts(limit)

        # Extract concepts specifically related to guidelines
        # This now returns more concepts per term (50 instead of 10)
        guideline_concepts = (
            self.snomed_explorer.find_cardiovascular_guidelines_concepts()
        )

        # Combine and remove duplicates efficiently
        all_concepts = cardio_concepts + guideline_concepts
        print(
            f"Found {len(cardio_concepts)} general cardiovascular concepts and {len(guideline_concepts)} guideline-related concepts"
        )

        # Filter and clean concepts using a more efficient approach with sets
        filtered_concepts = []
        seen_ids = set()

        for concept in all_concepts:
            # Extract concept ID based on available fields
            concept_id = None
            if "conceptId" in concept:
                concept_id = concept["conceptId"]
            elif "id" in concept:
                concept_id = concept["id"]

            if concept_id and concept_id not in seen_ids:
                seen_ids.add(concept_id)

                # Only include active concepts if that information is available
                if "active" in concept and concept["active"] == 0:
                    continue

                filtered_concepts.append(concept)

        print(
            f"Extracted {len(filtered_concepts)} unique cardiovascular concepts after filtering"
        )
        return filtered_concepts

    def get_concept_relationships(self, concepts: List[Dict]) -> Dict[str, List[Dict]]:
        """Get relationships for the extracted concepts"""
        print("Retrieving concept relationships...")
        relationships = {}
        concept_count = len(concepts)
        processed = 0

        # Process concepts in batches to show progress
        batch_size = 100

        for i, concept in enumerate(concepts):
            # Extract concept ID based on available fields
            concept_id = None
            if "conceptId" in concept:
                concept_id = concept["conceptId"]
            elif "id" in concept:
                concept_id = concept["id"]

            if concept_id:
                rels = self.snomed_explorer.get_relationships(str(concept_id))
                if rels:
                    relationships[concept_id] = rels

            processed += 1
            if processed % batch_size == 0 or processed == concept_count:
                print(
                    f"Processed {processed}/{concept_count} concepts ({int(processed/concept_count*100)}%)"
                )

        print(f"Retrieved relationships for {len(relationships)} concepts")
        return relationships

    def add_snomed_concept(self, concept: Dict) -> URIRef:
        """Add a SNOMED CT concept to the ontology"""
        # Extract concept ID and term
        concept_id = None
        term = None

        if "conceptId" in concept:
            concept_id = concept["conceptId"]
        elif "id" in concept:
            concept_id = concept["id"]

        if "term" in concept:
            term = concept["term"]

        if not concept_id or not term:
            # Generate a random UUID for concepts without IDs
            concept_id = str(uuid.uuid4())
            if not term:
                term = f"Unknown Concept {concept_id}"

        # Check if we already have this concept
        if concept_id in self.snomed_concepts:
            return self.snomed_concepts[concept_id]

        # Create a URI for the concept
        concept_uri = self.snomed[str(concept_id)]

        # Add the concept as a class
        self.g.add((concept_uri, RDF.type, OWL.Class))
        self.g.add((concept_uri, RDFS.label, Literal(term)))

        # Add additional metadata if available
        if "active" in concept and concept["active"] == 1:
            self.g.add((concept_uri, self.cgo["isActive"], Literal(True)))

        # Store the URI for future reference
        self.snomed_concepts[concept_id] = concept_uri
        return concept_uri

    def add_relationships(self, concept_id: str, relationships: List[Dict]):
        """Add relationships for a concept to the ontology"""
        if concept_id not in self.snomed_concepts:
            return

        source_uri = self.snomed_concepts[concept_id]

        for rel in relationships:
            rel_type = rel.get("typeId")
            target_id = rel.get("destinationId")

            if not rel_type or not target_id:
                continue

            target_uri = self.snomed[str(target_id)]

            # Always create a relationship property and label
            rel_prop_uri = self.cgo[f"snomed_rel_{rel_type}"]
            if rel_prop_uri not in self.properties:
                self.g.add((rel_prop_uri, RDF.type, OWL.ObjectProperty))
                rel_name = self.get_type_label(str(rel_type))
                self.g.add((rel_prop_uri, RDFS.label, Literal(rel_name)))
                self.properties.add(rel_prop_uri)

            # Add the relationship triple
            self.g.add((source_uri, rel_prop_uri, target_uri))

            # For IS-A, also add subClassOf
            if str(rel_type) == "116680003":
                self.g.add((source_uri, RDFS.subClassOf, target_uri))

            # Ensure the target class exists in the ontology
            if target_id not in self.snomed_concepts:
                term = f"SNOMED Concept {target_id}"
                self.g.add((target_uri, RDF.type, OWL.Class))
                self.g.add((target_uri, RDFS.label, Literal(term)))
                self.snomed_concepts[target_id] = target_uri

    def categorize_concepts(self, concepts: List[Dict]) -> Dict[str, List[URIRef]]:
        """Categorize SNOMED concepts into ontology categories"""
        categories = {
            "ClinicalAction": [],
            "PatientPhenotype": [],
            "Purpose": [],
            "WorkflowStep": [],
            "Guideline": [],
            "EvidenceSource": [],
            "Medication": [],
            "Condition": [],
            "GuidelineRecommendation": [],
            "GuidelineSource": [],
        }

        # Define keyword lists for each category
        keywords = {
            "ClinicalAction": [
                "procedure",
                "therapy",
                "treatment",
                "examination",
                "assessment",
                "monitoring",
                "administration",
                "prescription",
                "intervention",
            ],
            "PatientPhenotype": [
                "finding",
                "disorder",
                "disease",
                "syndrome",
                "condition",
                "symptom",
                "sign",
                "observation",
                "measurement",
                "test result",
            ],
            "Purpose": [
                "goal",
                "target",
                "objective",
                "purpose",
                "aim",
                "intended",
                "indication",
            ],
            "WorkflowStep": [
                "protocol",
                "step",
                "stage",
                "phase",
                "pathway",
                "regimen",
                "algorithm",
            ],
            "Guideline": [
                "guideline",
                "recommendation",
                "protocol",
                "consensus",
                "standard",
                "best practice",
                "statement",
            ],
            "EvidenceSource": [
                "trial",
                "study",
                "evidence",
                "publication",
                "literature",
                "research",
                "meta-analysis",
            ],
            "Medication": [
                "medication",
                "drug",
                "pharmaceutical",
                "pill",
                "tablet",
                "capsule",
                "injection",
                "infusion",
                "anticoagulant",
                "statin",
                "beta blocker",
                "ace inhibitor",
                "antiplatelet",
                "diuretic",
            ],
            "Condition": [
                "disease",
                "disorder",
                "syndrome",
                "condition",
                "pathology",
                "abnormality",
                "deficiency",
                "stenosis",
                "insufficiency",
                "failure",
            ],
            "GuidelineRecommendation": [
                "recommendation",
                "guidance",
                "advised",
                "suggested",
                "should",
                "must",
                "consider",
                "class i",
                "class ii",
                "class iii",
                "level of evidence",
                "grade",
                "strength",
            ],
            "GuidelineSource": [
                "guideline",
                "consensus document",
                "position paper",
                "statement",
                "expert consensus",
                "scientific statement",
                "task force",
                "working group",
                "committee",
            ],
        }

        for concept in concepts:
            # Get the concept URI (add it if not already in the ontology)
            concept_uri = self.add_snomed_concept(concept)

            # Extract term for categorization
            term = ""
            if "term" in concept:
                term = concept["term"].lower()

            # Assign to categories based on keywords
            for category, keyword_list in keywords.items():
                if any(keyword in term for keyword in keyword_list):
                    categories[category].append(concept_uri)
                    # Make it a subclass of the category
                    self.g.add((concept_uri, RDFS.subClassOf, self.cgo[category]))

        return categories

    def generate_ontology(self):
        """Generate the complete cardiovascular guidelines ontology"""
        print("Generating cardiovascular guidelines ontology...")

        try:
            # Connect to the SNOMED CT database
            self.snomed_explorer.connect()

            # Extract concepts
            concepts = self.extract_cardiovascular_concepts()

            if not concepts:
                print("No cardiovascular concepts found in SNOMED CT")
                return False

            # Get relationships
            relationships = self.get_concept_relationships(concepts)

            # Add concepts to the ontology
            for concept in concepts:
                self.add_snomed_concept(concept)

            # Categorize concepts
            categories = self.categorize_concepts(concepts)

            # Print category statistics
            for category, uris in categories.items():
                print(f"  - {category}: {len(uris)} concepts")

            # Add relationships
            for concept_id, rels in relationships.items():
                self.add_relationships(concept_id, rels)

            # Save the ontology to file
            self.g.serialize(destination=self.output_path, format="xml")
            print(f"Ontology generated successfully and saved to {self.output_path}")

            # Print statistics
            print(f"Ontology contains:")
            print(f"  - {len(self.classes)} core classes")
            print(f"  - {len(self.snomed_concepts)} SNOMED CT concepts")
            print(f"  - {len(self.properties)} properties")
            print(f"  - {len(self.g)} total RDF triples")

            return True

        except Exception as e:
            print(f"Error generating ontology: {e}")
            import traceback

            traceback.print_exc()
            return False

        finally:
            # Close the database connection
            self.snomed_explorer.disconnect()


def main():
    parser = argparse.ArgumentParser(
        description="Generate a cardiovascular guideline ontology from SNOMED CT data"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="cardio_ontology.owl",
        help="Output file path for the generated ontology",
    )
    parser.add_argument(
        "--host", default="10.250.135.23", help="SNOMED CT database host"
    )
    parser.add_argument("--port", default="3306", help="SNOMED CT database port")
    parser.add_argument(
        "--user", default="test_user", help="SNOMED CT database username"
    )
    parser.add_argument(
        "--password", default="medicaldatabase", help="SNOMED CT database password"
    )
    parser.add_argument(
        "--database", default="snomedct", help="SNOMED CT database name"
    )
    parser.add_argument(
        "--base-uri",
        default="http://dieterich-lab.org/ontologies/cardioguidelinesonto/",
        help="Base URI for the ontology",
    )
    parser.add_argument("-v", "--version", default="0.1.0", help="Ontology version")

    args = parser.parse_args()

    generator = CardioOntologyGenerator(
        output_path=args.output,
        snomed_host=args.host,
        snomed_port=args.port,
        snomed_user=args.user,
        snomed_password=args.password,
        snomed_database=args.database,
        base_uri=args.base_uri,
        version=args.version,
    )

    success = generator.generate_ontology()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
