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

# Import SnomedExplorer from snomed_query.py
from cardio_graph.snomedct_utils.snomed_query import SnomedExplorer


class CardioOntologyGenerator:
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

        # Add evidence levels as individuals of a class
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

        # Add evidence level individuals
        evidence_levels = [
            (
                "ClassI",
                "Class I - Evidence and/or general agreement that a treatment is beneficial",
            ),
            (
                "ClassIIa",
                "Class IIa - Weight of evidence in favor of usefulness/efficacy",
            ),
            ("ClassIIb", "Class IIb - Usefulness/efficacy less well established"),
            (
                "ClassIII",
                "Class III - Evidence that treatment is not useful/effective and may be harmful",
            ),
        ]

        for level_id, description in evidence_levels:
            level_uri = self.cgo[level_id]
            self.g.add((level_uri, RDF.type, evidence_class))
            self.g.add((level_uri, RDFS.label, Literal(level_id)))
            self.g.add((level_uri, RDFS.comment, Literal(description)))

    def extract_cardiovascular_concepts(self, limit: int = 500) -> List[Dict]:
        """Extract cardiovascular concepts from SNOMED CT"""
        print("Extracting cardiovascular concepts from SNOMED CT...")

        # Extract concepts related to cardiovascular conditions
        cardio_concepts = self.snomed_explorer.search_cardiovascular_concepts(limit)

        # Extract concepts specifically related to guidelines
        guideline_concepts = (
            self.snomed_explorer.find_cardiovascular_guidelines_concepts()
        )

        # Combine and remove duplicates
        all_concepts = cardio_concepts + guideline_concepts

        # Filter and clean concepts
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
                filtered_concepts.append(concept)

        print(f"Extracted {len(filtered_concepts)} unique cardiovascular concepts")
        return filtered_concepts

    def get_concept_relationships(self, concepts: List[Dict]) -> Dict[str, List[Dict]]:
        """Get relationships for the extracted concepts"""
        print("Retrieving concept relationships...")
        relationships = {}

        for concept in concepts:
            # Extract concept ID based on available fields
            concept_id = None
            if "conceptId" in concept:
                concept_id = concept["conceptId"]
            elif "id" in concept:
                concept_id = concept["id"]

            if concept_id:
                try:
                    rels = self.snomed_explorer.get_relationships(str(concept_id))
                    if rels:
                        relationships[concept_id] = rels
                except Exception as e:
                    print(f"Error getting relationships for concept {concept_id}: {e}")

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
            # Process each relationship based on type
            rel_type = None
            target_id = None

            # Extract relationship type and target based on available fields
            if "typeId" in rel:
                rel_type = rel["typeId"]

            if "destinationId" in rel:
                target_id = rel["destinationId"]
            elif "supertypeId" in rel and rel["subtypeId"] == concept_id:
                target_id = rel["supertypeId"]
            elif "conceptId" in rel and rel["conceptId"] != concept_id:
                target_id = rel["conceptId"]

            if not rel_type or not target_id:
                continue

            # Create target URI
            target_uri = self.snomed[str(target_id)]

            # IS-A relationship (116680003 is the SNOMED CT ID for IS-A)
            if str(rel_type) == "116680003":
                self.g.add((source_uri, RDFS.subClassOf, target_uri))

                # Ensure the target class exists in the ontology
                if target_id not in self.snomed_concepts:
                    term = None
                    if "destinationTerm" in rel:
                        term = rel["destinationTerm"]
                    elif "term" in rel:
                        term = rel["term"]
                    else:
                        term = f"SNOMED Concept {target_id}"

                    self.g.add((target_uri, RDF.type, OWL.Class))
                    self.g.add((target_uri, RDFS.label, Literal(term)))
                    self.snomed_concepts[target_id] = target_uri
            else:
                # Create a relationship property if it doesn't exist
                rel_prop_uri = self.cgo[f"snomed_rel_{rel_type}"]

                if rel_prop_uri not in self.properties:
                    self.g.add((rel_prop_uri, RDF.type, OWL.ObjectProperty))

                    # Try to get a name for the relationship
                    rel_name = f"snomedRelationship_{rel_type}"
                    if "typeTerm" in rel:
                        rel_name = rel["typeTerm"].replace(" ", "_")

                    self.g.add((rel_prop_uri, RDFS.label, Literal(rel_name)))
                    self.properties.add(rel_prop_uri)

                # Add the relationship to the graph
                self.g.add((source_uri, rel_prop_uri, target_uri))

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

            # Create example workflow patterns
            self.create_example_patterns()

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

    def create_example_patterns(self):
        """Create example workflow patterns using the ontology structure"""
        print("Creating example cardiovascular workflow patterns...")

        # Create an example clinical workflow for CCS (Chronic Coronary Syndrome)
        workflow = URIRef(self.cgo["CCS_Management_Workflow"])
        self.g.add((workflow, RDF.type, self.cgo["ClinicalWorkflow"]))
        self.g.add((workflow, RDFS.label, Literal("CCS Management Workflow")))
        self.g.add(
            (
                workflow,
                RDFS.comment,
                Literal(
                    "Clinical workflow for the management of Chronic Coronary Syndrome"
                ),
            )
        )

        # Create workflow steps
        steps = [
            ("Step1_ClinicalAssessment", "Step 1: Clinical Assessment"),
            ("Step2_RiskFactorEvaluation", "Step 2: Risk Factor Evaluation"),
            ("Step3_DiagnosticTesting", "Step 3: Diagnostic Testing"),
            ("Step4_TreatmentSelection", "Step 4: Treatment Selection"),
            ("Step5_FollowUp", "Step 5: Follow-up Planning"),
        ]

        for i, (step_id, step_label) in enumerate(steps):
            step_uri = self.cgo[step_id]
            self.g.add((step_uri, RDF.type, self.cgo["WorkflowStep"]))
            self.g.add((step_uri, RDFS.label, Literal(step_label)))
            self.g.add((workflow, self.cgo["hasStep"], step_uri))

            # Add ordering property
            self.g.add(
                (step_uri, self.cgo["stepOrder"], Literal(i + 1, datatype=XSD.integer))
            )

        # Add some clinical actions to steps
        actions = [
            # Step 1 actions
            ("Action_ECG", "Record 12-lead ECG", "Step1_ClinicalAssessment"),
            (
                "Action_ClinicalHistory",
                "Take detailed clinical history",
                "Step1_ClinicalAssessment",
            ),
            (
                "Action_PhysicalExam",
                "Perform physical examination",
                "Step1_ClinicalAssessment",
            ),
            # Step 2 actions
            (
                "Action_LipidProfile",
                "Measure lipid profile",
                "Step2_RiskFactorEvaluation",
            ),
            (
                "Action_BloodPressure",
                "Measure blood pressure",
                "Step2_RiskFactorEvaluation",
            ),
            (
                "Action_GlucoseLevel",
                "Check blood glucose level",
                "Step2_RiskFactorEvaluation",
            ),
            # Step 3 actions
            (
                "Action_Echocardiography",
                "Perform echocardiography",
                "Step3_DiagnosticTesting",
            ),
            ("Action_StressTest", "Conduct stress test", "Step3_DiagnosticTesting"),
            (
                "Action_CTCA",
                "Perform CT coronary angiography",
                "Step3_DiagnosticTesting",
            ),
            # Step 4 actions
            (
                "Action_StatinPrescription",
                "Prescribe statin therapy",
                "Step4_TreatmentSelection",
            ),
            (
                "Action_AntiplateletPrescription",
                "Prescribe antiplatelet therapy",
                "Step4_TreatmentSelection",
            ),
            (
                "Action_RevascularizationAssessment",
                "Assess need for revascularization",
                "Step4_TreatmentSelection",
            ),
            # Step 5 actions
            ("Action_FollowUpSchedule", "Schedule follow-up visit", "Step5_FollowUp"),
            (
                "Action_CardiacRehab",
                "Refer to cardiac rehabilitation",
                "Step5_FollowUp",
            ),
            (
                "Action_LifestyleCounseling",
                "Provide lifestyle modification counseling",
                "Step5_FollowUp",
            ),
        ]

        for action_id, action_label, step_id in actions:
            action_uri = self.cgo[action_id]
            step_uri = self.cgo[step_id]

            self.g.add((action_uri, RDF.type, self.cgo["ClinicalAction"]))
            self.g.add((action_uri, RDFS.label, Literal(action_label)))
            self.g.add((step_uri, self.cgo["hasAction"], action_uri))

        # Add purposes to some actions
        purposes = [
            ("Purpose_RuleOutACS", "To rule out acute coronary syndrome", "Action_ECG"),
            (
                "Purpose_AssessLVFunction",
                "To assess left ventricular function",
                "Action_Echocardiography",
            ),
            (
                "Purpose_ReduceCardiacEvents",
                "To reduce risk of cardiovascular events",
                "Action_StatinPrescription",
            ),
            (
                "Purpose_PreventThrombosis",
                "To prevent thrombotic events",
                "Action_AntiplateletPrescription",
            ),
        ]

        for purpose_id, purpose_label, action_id in purposes:
            purpose_uri = self.cgo[purpose_id]
            action_uri = self.cgo[action_id]

            self.g.add((purpose_uri, RDF.type, self.cgo["Purpose"]))
            self.g.add((purpose_uri, RDFS.label, Literal(purpose_label)))
            self.g.add((action_uri, self.cgo["hasPurpose"], purpose_uri))

        # Add evidence statements with levels
        evidence_statements = [
            (
                "Evidence_StatinCCS",
                "High-intensity statin therapy is recommended for patients with CCS",
                "Action_StatinPrescription",
                "ClassI",
            ),
            (
                "Evidence_AntiplateletCCS",
                "Low-dose aspirin is recommended for patients with CCS",
                "Action_AntiplateletPrescription",
                "ClassI",
            ),
            (
                "Evidence_EchoCCS",
                "Transthoracic echocardiography is recommended for initial assessment",
                "Action_Echocardiography",
                "ClassI",
            ),
            (
                "Evidence_CTCACCS",
                "CT coronary angiography should be considered as an alternative to invasive angiography",
                "Action_CTCA",
                "ClassIIa",
            ),
        ]

        # Create guideline source
        guideline_uri = self.cgo["ESC_CCS_Guidelines_2019"]
        self.g.add((guideline_uri, RDF.type, self.cgo["Guideline"]))
        self.g.add((guideline_uri, RDFS.label, Literal("ESC Guidelines for CCS 2019")))

        for (
            evidence_id,
            evidence_label,
            action_id,
            evidence_level,
        ) in evidence_statements:
            evidence_uri = self.cgo[evidence_id]
            action_uri = self.cgo[action_id]
            level_uri = self.cgo[evidence_level]

            self.g.add((evidence_uri, RDF.type, self.cgo["EvidenceStatement"]))
            self.g.add((evidence_uri, RDFS.label, Literal(evidence_label)))
            self.g.add((evidence_uri, self.cgo["isRecommendedIn"], guideline_uri))
            self.g.add((evidence_uri, self.cgo["hasEvidenceLevel"], level_uri))
            self.g.add((action_uri, self.cgo["isSupportedBy"], evidence_uri))

        # Add a contrasting statement example
        contrast_uri = self.cgo["Evidence_RevascContrast"]
        self.g.add((contrast_uri, RDF.type, self.cgo["ContrastingStatement"]))
        self.g.add(
            (
                contrast_uri,
                RDFS.label,
                Literal(
                    "While revascularization improves symptoms, it has not been shown to reduce mortality in all patients"
                ),
            )
        )

        revascularization_evidence = self.cgo["Evidence_Revascularization"]
        self.g.add(
            (revascularization_evidence, RDF.type, self.cgo["EvidenceStatement"])
        )
        self.g.add(
            (
                revascularization_evidence,
                RDFS.label,
                Literal(
                    "Revascularization should be considered for symptom improvement in patients with CCS"
                ),
            )
        )
        self.g.add(
            (revascularization_evidence, self.cgo["contrastsWith"], contrast_uri)
        )
        self.g.add(
            (
                self.cgo["Action_RevascularizationAssessment"],
                self.cgo["isSupportedBy"],
                revascularization_evidence,
            )
        )

        # Add medication examples with indications and contraindications
        print("Adding medication examples with the new properties...")

        # Create medications
        medications = [
            ("Med_Atorvastatin", "Atorvastatin", "10-80 mg daily", "2393763"),
            ("Med_Aspirin", "Aspirin", "75-100 mg daily", "1191"),
            ("Med_Clopidogrel", "Clopidogrel", "75 mg daily", "32968"),
            ("Med_Metoprolol", "Metoprolol", "25-200 mg daily", "6918"),
            ("Med_Ramipril", "Ramipril", "2.5-10 mg daily", "35296"),
        ]

        for med_id, med_label, dosage, rxnorm_id in medications:
            med_uri = self.cgo[med_id]
            self.g.add((med_uri, RDF.type, self.cgo["Medication"]))
            self.g.add((med_uri, RDFS.label, Literal(med_label)))
            self.g.add((med_uri, self.cgo["hasDosage"], Literal(dosage)))
            self.g.add((med_uri, self.cgo["hasRxNormId"], Literal(rxnorm_id)))

        # Create conditions
        conditions = [
            ("Cond_CCS", "Chronic Coronary Syndrome", "53741008"),
            ("Cond_ACS", "Acute Coronary Syndrome", "394659003"),
            ("Cond_HF", "Heart Failure", "42343007"),
            ("Cond_AF", "Atrial Fibrillation", "49436004"),
            ("Cond_Hyperlipidemia", "Hyperlipidemia", "55822004"),
            ("Cond_AsthmaHistory", "History of Asthma", "161527007"),
            ("Cond_ActivePepticUlcer", "Active Peptic Ulcer", "397825006"),
        ]

        for cond_id, cond_label, snomed_id in conditions:
            cond_uri = self.cgo[cond_id]
            self.g.add((cond_uri, RDF.type, self.cgo["Condition"]))
            self.g.add((cond_uri, RDFS.label, Literal(cond_label)))
            self.g.add((cond_uri, self.cgo["hasSnomedId"], Literal(snomed_id)))

        # Add indications, recommendations and contraindications
        indications = [
            ("Med_Atorvastatin", "Cond_Hyperlipidemia"),
            ("Med_Atorvastatin", "Cond_CCS"),
            ("Med_Aspirin", "Cond_CCS"),
            ("Med_Clopidogrel", "Cond_ACS"),
            ("Med_Metoprolol", "Cond_CCS"),
            ("Med_Metoprolol", "Cond_HF"),
            ("Med_Ramipril", "Cond_HF"),
        ]

        for med_id, cond_id in indications:
            self.g.add((self.cgo[med_id], self.cgo["hasIndication"], self.cgo[cond_id]))

        contraindications = [
            ("Med_Aspirin", "Cond_ActivePepticUlcer"),
            ("Med_Metoprolol", "Cond_AsthmaHistory"),
        ]

        for med_id, cond_id in contraindications:
            self.g.add(
                (self.cgo[med_id], self.cgo["isContraindicatedIn"], self.cgo[cond_id])
            )

        # Add guideline recommendations with sources and evidence levels
        guideline_sources = [
            ("Source_ESC_CCS_2019", "ESC Guidelines for CCS 2019", "1"),
            ("Source_AHA_ACC_CAD_2014", "AHA/ACC Guideline for SIHD 2014", "5"),
        ]

        for source_id, source_label, page in guideline_sources:
            source_uri = self.cgo[source_id]
            self.g.add((source_uri, RDF.type, self.cgo["GuidelineSource"]))
            self.g.add((source_uri, RDFS.label, Literal(source_label)))
            self.g.add((source_uri, self.cgo["pageNumber"], Literal(int(page))))

        recommendations = [
            (
                "Rec_Statin_CCS",
                "High-intensity statin therapy is recommended for patients with CCS",
                "Source_ESC_CCS_2019",
                "Class I, Level A",
                "Med_Atorvastatin",
            ),
            (
                "Rec_Aspirin_CCS",
                "Low-dose aspirin is recommended for patients with CCS",
                "Source_ESC_CCS_2019",
                "Class I, Level A",
                "Med_Aspirin",
            ),
            (
                "Rec_BetaBlocker_Post_MI",
                "Beta-blockers are recommended in patients with reduced ejection fraction",
                "Source_ESC_CCS_2019",
                "Class I, Level A",
                "Med_Metoprolol",
            ),
            (
                "Rec_ACEi_HF",
                "ACE inhibitors are recommended in patients with heart failure",
                "Source_ESC_CCS_2019",
                "Class I, Level A",
                "Med_Ramipril",
            ),
        ]

        for rec_id, rec_label, source_id, evidence, med_id in recommendations:
            rec_uri = self.cgo[rec_id]
            source_uri = self.cgo[source_id]
            med_uri = self.cgo[med_id]

            self.g.add((rec_uri, RDF.type, self.cgo["GuidelineRecommendation"]))
            self.g.add((rec_uri, RDFS.label, Literal(rec_label)))
            self.g.add((rec_uri, self.cgo["hasSource"], source_uri))
            self.g.add((source_uri, self.cgo["makesRecommendation"], rec_uri))
            self.g.add((rec_uri, self.cgo["hasEvidenceLevelString"], Literal(evidence)))

            # Connect medications to patient phenotypes via recommendations
            if med_id == "Med_Atorvastatin":
                self.g.add(
                    (med_uri, self.cgo["isRecommendedFor"], self.cgo["Cond_CCS"])
                )
            elif med_id == "Med_Aspirin":
                self.g.add(
                    (med_uri, self.cgo["isRecommendedFor"], self.cgo["Cond_CCS"])
                )
            elif med_id == "Med_Metoprolol":
                self.g.add((med_uri, self.cgo["isRecommendedFor"], self.cgo["Cond_HF"]))
            elif med_id == "Med_Ramipril":
                self.g.add((med_uri, self.cgo["isRecommendedFor"], self.cgo["Cond_HF"]))

        # Add SNOMED concept IDs to some entities
        for entity_id, snomed_id in [
            ("Action_ECG", "29303009"),  # ECG procedure
            ("Action_Echocardiography", "40701008"),  # Echocardiography
            ("Action_StatinPrescription", "430193006"),  # Statin therapy
            ("Action_AntiplateletPrescription", "429503005"),  # Antiplatelet therapy
        ]:
            self.g.add(
                (self.cgo[entity_id], self.cgo["hasSnomedId"], Literal(snomed_id))
            )


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
