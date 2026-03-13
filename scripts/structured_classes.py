from enum import Enum
from typing import List, Literal

from pydantic import BaseModel, Field


class Triple(BaseModel):
    head: str = Field(description="Beschreibt die Start-Entität")
    # head_type: Literal[
    #     "KRANKHEIT",
    #     "ANATOMIE",
    #     "MEDIKAMENTE",
    #     "NICHT-MEDIKAMENTÖSE THERAPEUTISCHE MASSNAHMEN",
    #     "INVASIVE THERAPIEMASSNAHMEN",
    #     "DIAGNOSTIK",
    #     "KRANKHEITSMANAGEMENT",
    #     "PATIENTENMANAGEMENT",
    # ] = Field(
    #     description="""Beschreibt den Typ der Start-Entität.
    # """
    # )
    relation: str = Field(
        description="Beschreibt die Relation zwischen Start-Entität und Ziel-Entität. Darf ein beliebiger Freitext sein."
    )
    tail: str = Field(description="Beschreibt die Ziel-Entität")
    # tail_type: Literal[
    #     "KRANKHEIT",
    #     "ANATOMIE",
    #     "MEDIKAMENTE",
    #     "NICHT-MEDIKAMENTÖSE THERAPEUTISCHE MASSNAHMEN",
    #     "INVASIVE THERAPIEMASSNAHMEN",
    #     "DIAGNOSTIK",
    #     "KRANKHEITSMANAGEMENT",
    #     "PATIENTENMANAGEMENT",
    # ] = Field(
    #     description="""Beschreibt den Typ der End-Entität.
    # """
    # )


class Triples(BaseModel):
    triples: List[Triple] = Field(description="Liste aller extrahierten Triples")


class TableRouter(BaseModel):
    """
    Eine Funktion, die entscheidet ob es sich bei einem Input um eine Tabelle handelt oder nicht.
    """

    # Eine Funktion, die entscheidet ob die eine Entscheidung über einen Input trifft.

    decision: Literal["ja", "nein"] = Field(
        description="Eine entweder positive oder negative Antwort."
    )


class HalluRouter(BaseModel):
    """
    Eine Funktion, die entscheidet ob es sich bei einem Input um eine Halluzination handelt oder nicht.
    """

    # Eine Funktion, die entscheidet ob die eine Entscheidung über einen Input trifft.

    decision: Literal["ja", "nein"] = Field(
        description="Eine entweder positive oder negative Antwort."
    )


class MedicRouter(BaseModel):
    """
    Eine Funktion, die entscheidet ob es sich bei einem Input um Wissen zur medizinischen Behandlung von Patienten handelt.
    """

    decision: Literal["ja", "nein"] = Field(
        description="Eine entweder positive oder negative Antwort."
    )


TRIPLES_SCHEMA = {
    "title": "Tripel-Liste",
    "description": "Liste aller extrahierten Tripel für einen gegebenen Input.",
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "head": {
                "type": "string",
                "description": "Beschreibt die Start-Entität",
            },
            "head_type": {
                "type": "string",
                "description": "Beschreibt den Typ der Start-Entität.",
                "enum": [
                    "KRANKHEIT",
                    "ANATOMIE",
                    "MEDIKAMENTE",
                    "NICHT-MEDIKAMENTÖSE THERAPEUTISCHE MASSNAHMEN",
                    "INVASIVE THERAPIEMASSNAHMEN",
                    "DIAGNOSTIK",
                    "KRANKHEITSMANAGEMENT",
                    "PATIENTENMANAGEMENT",
                ],
            },
            "relation": {
                "type": "string",
                "description": "Beschreibt die Relation zwischen Start-Entität und Ziel-Entität.",
            },
            "tail": {
                "type": "string",
                "description": "Beschreibt die End-Entität.",
            },
            "tail_type": {
                "type": "string",
                "description": "Beschreibt den Typ der Ziel-Entität.",
                "enum": [
                    "KRANKHEIT",
                    "ANATOMIE",
                    "MEDIKAMENTE",
                    "NICHT-MEDIKAMENTÖSE THERAPEUTISCHE MASSNAHMEN",
                    "INVASIVE THERAPIEMASSNAHMEN",
                    "DIAGNOSTIK",
                    "KRANKHEITSMANAGEMENT",
                    "PATIENTENMANAGEMENT",
                ],
            },
        },
    },
    "properties": {},
}

TABLE = """
|Substanzklasse|getestet gegen/im Vergleich zu|Mortalität, Hospitalisierungen|langfristige Endpunkte|Hypotonierisiko|Diuretikagebrauch|weitere Anwendungsgebiete|wichtige Kontraindikationen und Sicherheitshinweise|
|---|---|---|---|---|---|---|---|
|ACEi|Placebo|↓|(↔)|↑|(↔)|▪ arterielle Hypertonie ▪ nach Myokardinfarkt|▪ Hypotonie ▪ Hyperkaliämie ▪ Angioödem|
|ARB|ACEi|↔|(↔)|↔|(↔)|▪ insb. diabetische Nephropathie|▪ Husten ▪ Vorsicht bei eGFR < 30 ml/min/1,73 m2|
|ARNI|auf Basis von BB (+MRA)|↓|(↓)|↑|↓| |▪ nach Myokardinfarkt ▪ Bradykardie ▪ Hyperkaliämie ▪ Angioödem|
|BB|auf Basis von ACEi/ARB (+Digitalis)|↓|(↔)|↑|(↔)|▪ A. pectoris ▪ Tachyarrhythmien|▪ AV-Block ▪ Hypotonie (kontraindiziert bei SBP < 90 mmHg)|
|MRA|auf Basis von RASi+BB|↓|?|↑|↓|▪ primärer Hyperaldosteronismus ▪ Ausgleich des kaliuretischen Effekts von Diuretika|▪ Hyperkaliämie, Hyponatriämie ▪ Hypotonie ▪ Gynäkomastie ▪ gastrointestinale Nebenwirkungen|
"""

TEXT = """
Somatoforme Störungen können vorliegen, wenn der Patient wiederholt über körperliche Beschwerden klagt, die durch den somatischen Befund nicht ausreichend erklärbar sind, wenn er trotz Aufklärung über mögliche psychosomatische Hintergründe von einer körperlichen Ursache überzeugt ist und deswegen wiederholt Ärzte aufsucht und/oder wenn die bereits durchgeführte Diagnostik und (evtl. invasive) Therapie unverhältnismäßig zur gesicherten Befundlage erscheint. (Selbst-)Beurteilungsbögen können eingesetzt werden, um die psychischen Merkmale somatoformer Störungen zu erfassen und zu objektivieren (deutschsprachig z. B. SSD-12: Somatic Symptom Disorder-B Criteria Scale [76,77]; SSEQ: Fragebogen zum Erleben von Körperbeschwerden [78]).

Erhärtet sich nach dem Screening der Verdacht auf psychische/psychosomatische Komorbiditäten, können sich daraus entweder therapeutische Konsequenzen ergeben (siehe Kapitel 8.7 Psychische Komorbidität) oder Überweisungen an andere Fachgruppen (Psychosomatik, Psychiatrie, Psychotherapie) zwecks weiterer Diagnostik und ggf. Behandlung (siehe Tabelle 28, Kapitel 12.1 Koordination der ambulanten Versorgung).

Zur Behandlung psychischer/psychosomatischer Erkrankungen bei Patienten mit Herzinsuffizienz siehe Kapitel 8.7 Psychische Komorbidität. Das Patientenblatt „Warum alltägliche und seelische Belastungen wichtig werden können“ erklärt in allgemeinverständlicher Sprache den Zusammenhang zwischen psychischen und somatischen Beschwerden (siehe Anhang Patientenblätter).
"""


class MedicEntities(BaseModel):
    """
    Ein Klasse, die eine Liste von

    - medizinischen,
    - anatomischen,
    - diagnostischen
    - labortechnischen

       Konzepten enhält.
    """

    names: List[str] = Field(
        ...,
        description="Liste mit medizinischen, anatomischen, diagnostischen und laborwissenschaftlichen Konzepten.",
    )


class Entities(BaseModel):
    """
    Eine Liste von Nomen und Konzepten.
    """

    names: List[str] = Field(..., description="Eine Liste von Nomen und Konzepten.")
