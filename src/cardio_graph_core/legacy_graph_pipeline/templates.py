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

GUIDELINES_EXAMPLES_SIMPLE = [
    {
        "head": "Herzinsuffizienz",
        "relation": "wird bei LVEF < 40% zu",
        "tail": "Herzinsuffizienz mit reduzierter linksventrikulärer Ejektionsfraktion (HFrEF)",
    },
    {
        "head": "Herzinsuffizienz",
        "relation": "wird bei LVEF 40-49% zu",
        "tail": "Herzinsuffizienz mit geringgradig eingeschränkter linksventrikulärer Ejektionsfraktion (HFmrEF)",
    },
    {
        "head": "Herzinsuffizienz",
        "relation": "wird bei LVEF = 50% zu",
        "tail": "Herzinsuffizienz mit erhaltener linksventrikulärer Ejektionsfraktion (HFpEF)",
    },
    {
        "head": "Das Schlagvolumen des Herzens",
        "relation": "ist reduziert bei",
        "tail": "HFrEF",
    },
    {
        "head": "Myokard",
        "relation": "ist beschädigt bei",
        "tail": "HFrEF",
    },
    {
        "head": "Betablocker",
        "relation": "ist eine prognoseverbessernde Substanzgruppe bei",
        "tail": "HFrEF",
    },
    {
        "head": "Bisoprolol",
        "relation": "ist ein",
        "tail": "Betablocker",
    },
    {
        "head": "ACEi",
        "relation": "kontraindiziert bei",
        "tail": "Angioödem",
    },
    {
        "head": "gesunder Lebensstil",
        "relation": "ist indiziert bei",
        "tail": "chronische Herzinsuffizienz",
    },
    {
        "head": "Anamnese",
        "relation": "ist erforderlich bei Symptomen einer",
        "tail": "Herzinsuffizienz",
    },
    {
        "head": "Shared-Decision-Making",
        "relation": "unterstützt die",
        "tail": "Selbstbestimmungsaufklärung",
    },
]

# 1. head: Beschreibt die Start-Entität.
# 2. relation: Beschreibt die Relation zwischen Start-Entität und Ziel-Entität und darf ein beliebiger Freitext passend zum Input sein.
# 3. tail: Beschreibt die Ziel-Entität.
TABLE_PROMPT = """
Du bist ein spezialisierter Arzt, der medizinische Informationen in Form von Tripeln aus Tabellen 
einer klinischen Richtlinie über Herzinssufizienz extrahiert. 

Halte Dich an das folgende JSON Format:
{format_instructions}

Hier sind Beispiele, wie die gewünschten Tripel aussehen können:
{examples}

WICHTIG:
* Extrahiere für jeden Tabelleneintrag ein eigenes Tripel. Lasse keine Zeile und keine Spalte aus!
"""

TEXT_PROMPT = """
Du bist ein spezialisierter Arzt, der medizinische Informationen in Form von Tripeln aus Paragraphen 
einer klinischen Richtlinie über Herzinssufizienz extrahiert. 

Halte Dich an das folgende JSON Format:
{format_instructions}

Hier sind Beispiele, wie die gewünschten Tripel aussehen können:
{examples}

WICHTIG: 
* Halte die Tripel so generell wie möglich, so dass sie leicht verständlich sind.
"""
TABLE_PROMPT_SIMPLE = """
Du bist ein spezialisierter Arzt, der medizinische Informationen in Form von Tripeln aus Tabellen 
einer klinischen Richtlinie über Herzinssufizienz extrahiert. 

Halte Dich an das folgende JSON Format:
{format_instructions}

WICHTIG:
* Extrahiere für jeden Tabelleneintrag ein eigenes Tripel. Lasse keine Zeile und keine Spalte aus!
* Extrahiere so viele Inhalte wie möglich aus der Tabelle!
"""

TEXT_PROMPT_SIMPLE = """
Du bist ein spezialisierter Arzt, der medizinische Informationen in Form von Tripeln aus Paragraphen 
einer klinischen Richtlinie über Herzinssufizienz extrahiert. 

Halte Dich an das folgende JSON Format:
{format_instructions}

WICHTIG: 
* Halte die Tripel so generell wie möglich, so dass sie leicht verständlich sind.
* Extrahiere so viele Inhalte wie möglich aus dem Text!
"""
# Beispiel: für 'Koronare Herzkrankheit (KHK), arterielle Hypertonie sowie deren Kombination' solltest Du die einzelnen Entitäten
# 'Koronare Herzkrankheit (KHK)', 'arterielle Hypertonie', 'Koronare Herzkrankheit (KHK) und arterielle Hypertonie' erstellen.

# * Wenn Ziel-Entitäten durch Komma getrennt sind, so erstelle ein eigenes Tripel für jeden "tail".
# * Extrahiere ausschließlich Informationen, die im Input stehen und erfinde keine Details.
