TEMPLATE = """ Basierend auf den folgenden Beispielen, extrahiere Entitäten und Relationen aus
dem folgenden Text.\n\n
Benutze ausschließlich die folgenden Typen an Entitäten:
# Entitätentypen:
{node_labels}

WICHTIG: Der Text kann auch aus einer Markdown-Tabelle bestehen. Iteriere über jede Zeile und extrahiere die Beziehungen ebenfalls als Tripel

Beschreibe explizit spezifische Relationen zwischen diesen Begriffen. Innerhalb dieser Relationen dürfen 
komplexe Beziehungen beschrieben sein.

Hier angefügt findest Du eine Reihe an Beispielen:
{examples}

Extrahiere Entitäten und Relationen aus dem folgenden Text, wie es Dir in den Beispielen gezeigt wurde.

{format_instructions}\nText: {input}"""

NODES = [
    "KRANKHEIT",
    "ANATOMIE",
    "MEDIKAMENTE",
    "NICHT-MEDIKAMENTÖSE THERAPEUTISCHE MASSNAHMEN",
    "INVASIVE THERAPIEMASSNAHMEN",
    "DIAGNOSTIK",
    "KRANKHEITSMANAGEMENT",
    "PATIENTENMANAGEMENT",
]

GUIDELINES_BASESTRINGPARTS_JSON = [
    "Du bist ein professioneller Arzt, der sich auf die Krankheit Herzinsuffizienz spezialsiert hat. "
    "Deine Aufgabe ist es, Beziehungen zwischen bestimmten Entitäten aus einer Richtlinie über die Behandlung von Patienten mit "
    "Herzinsuffizienz zu identifizieren. Diese Entitäten beziehen sich sowohl auf das Krankheitsbild Herzinsuffizienz, sowie "
    "dessen Behandlung und den Umgang mit dem Patienten. Die Entitäten sind Dir vorgegeben, Du bist aber frei in der Textwahl "
    "für die Beziehungen zwischen den Entitäten. Stelle Deine Ergebnisse als Liste mit Objekten im JSON Format zur Verfügung. "
    "Jedes Objekt sollte die Schlüssel 'head', 'head_type', 'relation', 'tail' und 'tail_type' beinhalten. "
    "Der 'head'-Schlüssel muss den Namen der ersten Entität enthalten. 'head_type' enthält den Typ dieser Entität."
    "'relation' beinhaltet den Freitext, der die Beziehung zwischen erster und zweiter Entität beschreibt. "
    "Der 'tail'-Schlüssel muss den Namen der zweiten Entität enthalten. 'tail_type' enthält den Typ der zweiten "
    "Entität. "
    "Versuche so viele Entitäten und deren Beziehungen wie möglich zu extrahieren. Achte auf Konsistenz "
    "WICHTIG: Füge keine Erklärungen oder zusätzlichen Text hinzu."
]

GUIDELINES_BASESTRINGPARTS_TRIPLE = [
    "Du bist ein professioneller Arzt, der sich auf die Krankheit Herzinsuffizienz spezialsiert hat. "
    "Deine Aufgabe ist es, Beziehungen zwischen bestimmten Entitäten aus einer Richtlinie über die Behandlung von Patienten mit "
    "Herzinsuffizienz zu identifizieren. Diese Entitäten beziehen sich sowohl auf das Krankheitsbild Herzinsuffizienz, sowie "
    "dessen Behandlung und den Umgang mit dem Patienten. Die Entitäten sind Dir vorgegeben, Du bist aber frei in der Textwahl "
    "für die Beziehungen zwischen den Entitäten. Stelle Deine Ergebnisse als Liste mit Triple-Objekten zur Verfügung. "
    "Jedes Objekt hat die Attribute 'head', 'head_type', 'relation', 'tail' und 'tail_type' beinhalten. "
    "Das 'head'-Attribut muss den Namen der ersten Entität enthalten. 'head_type' enthält den Typ dieser Entität."
    "'relation' beinhaltet den Freitext, der die Beziehung zwischen erster und zweiter Entität beschreibt. "
    "Das 'tail'-Attribut muss den Namen der zweiten Entität enthalten. 'tail_type' enthält den Typ der zweiten "
    "Entität. "
    "Versuche so viele Entitäten und deren Beziehungen wie möglich zu extrahieren. Achte auf Konsistenz "
    "WICHTIG: Füge keine Erklärungen oder zusätzlichen Text hinzu."
]


GUIDELINES_EXAMPLES = [
    {
        "head": "Herzinsuffizienz",
        "head_type": "KRANKHEIT",
        "relation": "wird bei LVEF < 40% zu",
        "tail": "Herzinsuffizienz mit reduzierter linksventrikulärer Ejektionsfraktion (HFrEF)",
        "tail_type": "KRANKHEIT",
    },
    {
        "head": "Herzinsuffizienz",
        "head_type": "KRANKHEIT",
        "relation": "wird bei LVEF 40-49% zu",
        "tail": "Herzinsuffizienz mit geringgradig eingeschränkter linksventrikulärer Ejektionsfraktion (HFmrEF)",
        "tail_type": "KRANKHEIT",
    },
    {
        "head": "Herzinsuffizienz",
        "head_type": "KRANKHEIT",
        "relation": "wird bei LVEF = 50% zu",
        "tail": "Herzinsuffizienz mit erhaltener linksventrikulärer Ejektionsfraktion (HFpEF)",
        "tail_type": "KRANKHEIT",
    },
    {
        "head": "Das Schlagvolumen des Herzens",
        "head_type": "ANATOMIE",
        "relation": "ist reduziert bei",
        "tail": "HFrEF",
        "tail_type": "KRANKHEIT",
    },
    {
        "head": "Myokard",
        "head_type": "ANATOMIE",
        "relation": "ist beschädigt bei",
        "tail": "HFrEF",
        "tail_type": "KRANKHEIT",
    },
    {
        "head": "Betablocker",
        "head_type": "MEDIKAMENTE",
        "relation": "ist eine prognoseverbessernde Substanzgruppe bei",
        "tail": "HFrEF",
        "tail_type": "KRANKHEIT",
    },
    {
        "head": "Bisoprolol",
        "head_type": "MEDIKAMENTE",
        "relation": "ist ein",
        "tail": "Betablocker",
        "tail_type": "MEDIKAMENTE",
    },
    {
        "head": "ACEi",
        "head_type": "MEDIKAMENTE",
        "relation": "kontraindiziert bei",
        "tail": "Angioödem",
        "tail_type": "KRANKHEIT",
    },
    {
        "head": "gesunder Lebensstil",
        "head_type": "NICHT-MEDIKAMENTÖSE THERAPEUTEISCHE MASSNAHMEN",
        "relation": "ist indiziert bei",
        "tail": "chronische Herzinsuffizienz",
        "tail_type": "KRANKHEIT",
    },
    {
        "head": "Anamnese",
        "head_type": "DIAGNOSTIK",
        "relation": "ist erforderlich bei Symptomen einer",
        "tail": "Herzinsuffizienz",
        "tail_type": "KRANKHEIT",
    },
    {
        "head": "Shared-Decision-Making",
        "head_type": "PATIENTENMANAGEMENT",
        "relation": "unterstützt die",
        "tail": "Selbstbestimmungsaufklärung",
        "tail_type": "PATIENTENMANAGEMENT",
    },
]

TABLE_PROMPT = """
Im folgenden siehst Du eine eine deutsche Tabelle, die aus einer klinischen Richtlinie über Herzinsuffizienz stammt.
Die Tabelle ist im Markdown-Format. Bitte wandle die Tabelle vollständig in Tripel um, so dass die Tripel
in einen Wissensgraphen eingepflegt werden können.

Hier sind Deine Anweisungen:

* Benutze JSON-Format für die Tripel, mit den Einträgen "head", "relation" und "tail".
* Gebe alle möglichen Tripel aus.
* Sollte in einer Zelle eine Liste enthalten sein, erstelle für jedes Listenelement ein eigenes Tripel.
* Gib nur die Liste der JSON-Objekte aus.
* WICHTIG: Antworte auf Deutsch.

Hier ist die Tabelle:

|Substanzklasse|getestet gegen/im Vergleich zu|Mortalität, Hospitalisierungen|langfristige Endpunkte|Hypotonierisiko|Diuretikagebrauch|weitere Anwendungsgebiete|wichtige Kontraindikationen und Sicherheitshinweise|
|---|---|---|---|---|---|---|---|
|ACEi|Placebo|↓|(↔)|↑|(↔)|▪ arterielle Hypertonie ▪ nach Myokardinfarkt|▪ Hypotonie ▪ Hyperkaliämie ▪ Angioödem|
|ARB|ACEi|↔|(↔)|↔|(↔)|▪ insb. diabetische Nephropathie|▪ Husten ▪ Vorsicht bei eGFR < 30 ml/min/1,73 m2|
|ARNI|auf Basis von BB (+MRA)|↓|(↓)|↑|↓| |▪ nach Myokardinfarkt ▪ Bradykardie ▪ Hyperkaliämie ▪ Angioödem|
|BB|auf Basis von ACEi/ARB (+Digitalis)|↓|(↔)|↑|(↔)|▪ A. pectoris ▪ Tachyarrhythmien|▪ AV-Block ▪ Hypotonie (kontraindiziert bei SBP < 90 mmHg)|
|MRA|auf Basis von RASi+BB|↓|?|↑|↓|▪ primärer Hyperaldosteronismus ▪ Ausgleich des kaliuretischen Effekts von Diuretika|▪ Hyperkaliämie, Hyponatriämie ▪ Hypotonie ▪ Gynäkomastie ▪ gastrointestinale Nebenwirkungen|
|SGLT2i|auf Basis von RASi+BB (+MRA)|↓|↓|↔|↓|▪ chronische Nierenerkrankungen|▪ urogenitale Infektionen ▪ atypische Ketoazidose|
"""

WORKING_TABLE_PROMPT = """
Du bist ein spezialisierter Arzt, der medizinische Informationen in Form von Tripeln Tabellen 
einer klinischen Richtlinie über Herzinssufizienz extrahiert. 
Jedes extrahierte Tripel muss immer aus den folgenden drei Einträgen bestehen:
1. head: Beschreibt die Start-Entität.
2. relation: Beschreibt die Relation zwischen Start-Entität und Ziel-Entität und darf ein beliebiger Freitext passend zum Input sein.
3. tail: Beschreibt die Ziel-Entität.

WICHTIG: Extrahiere für jeden Tabelleneintrag ein eigenes Tripel. Lasse keine Zeile und keine Spalte aus!
"""
