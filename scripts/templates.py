BASE_TEMPLATE = """Based on the following example, extract entities and 
relations from the provided text.\n\n
Use the following entity types, don't use other entity that is not defined below:
# ENTITY TYPES:
{node_labels}

Use the following relation types, don't use other relation that is not defined below:
# RELATION TYPES:
{rel_types}

Below are a number of examples of text and their extracted entities and relationships.
{examples}

For the following text, extract entities and relations as in the provided example.
{format_instructions}\nText: {input}"""

GUIDELINES_BASESTRINGPARTS = [
    "You are a top-tier molecular biologist specialized in the field of cardiology. "
    "Your task is to identify pairs of proteins which are known to be interacting with "
    " each other. It is very important that the entities that you identify as interacting "
    "to only be proteins. To me, it does not matter the nature of the interaction, it can be "
    "an activation, inhibition, binding, etc.. All that matters is that you provide to me "
    "pairs of proteins which are known to be interacting with each other one way or another."
    "the protein (entities) and relations (the interaction between the proteins) "
    " requested with the user prompt from a given "
    "text. You must generate the output in a JSON format containing a list "
    "'with JSON objects. ",
    'Each object should have the keys: "head", '
    '"relation" and "tail". The "head" and "tail" '
    "key must contain the name or denominator of the extracted protein.",
    "Attempt to extract as many proteins and relations as you can. Maintain "
    "Entity Consistency: When extracting entities, it's vital to ensure "
    'consistency. If a protein, such as "PRKACA", is mentioned multiple '
    "times in the text but is referred to by different names "
    '(e.g., "PRKACA", "PKACA", "cAMP-activated catalytic subunit alpha"), '
    "always use the canonical gene name identifier for "
    "that entity. The knowledge graph should be coherent and easily "
    "understandable, so maintaining consistency in entity references is "
    "crucial.",
    "IMPORTANT NOTES:\n- Don't add any explanation and text.",
]

GUIDELINES_EXAMPLES = [
    {
        "text": (
            "MEF2A transcriptionally upregulates the expression of ZEB2 and CTNNB1"
        ),
        "head": "MEF2A",
        "head_type": "transcription factor",
        "relation": "UPREGULATES",
        "tail": "ZEB2",
        "tail_type": "gene",
    },
    {
        "text": (
            "MEF2A transcriptionally upregulates the expression of ZEB2 and CTNNB1"
        ),
        "head": "MEF2A",
        "head_type": "transcription factor",
        "relation": "UPREGULATES",
        "tail": "CTNNB1",
        "tail_type": "gene",
    },
    {
        "text": (
            "CREM regulate the circadian expression of CYP51 and "
            "other cholesterogenic genes in the human heart."
        ),
        "head": "CREM",
        "head_type": "transcription factor",
        "relation": "REGULATES",
        "tail": "CYP51",
        "tail_type": "gene",
    },
    {
        "text": (
            "STAT3 then travels to the nucleus where it stimulates the transcription of specific genes, "
            "which in-turn are thought to abrogate the inflammatory response by transcriptionally repressing "
            "proinflammatory cytokine genes such as IL-1, IL-6, IL-12, and TNF-α."
        ),
        "head": "STAT3",
        "head_type": "transcription factor",
        "relation": "REPRESS",
        "tail": "IL-1",
        "tail_type": "gene",
    },
    {
        "text": (
            "STAT3 then travels to the nucleus where it stimulates the transcription of specific genes, "
            "which in-turn are thought to abrogate the inflammatory response by transcriptionally repressing "
            "proinflammatory cytokine genes such as IL-1, IL-6, IL-12, and TNF-α."
        ),
        "head": "STAT3",
        "head_type": "transcription factor",
        "relation": "REPRESS",
        "tail": "IL-6",
        "tail_type": "gene",
    },
    {
        "text": (
            "STAT3 then travels to the nucleus where it stimulates the transcription of specific genes, "
            "which in-turn are thought to abrogate the inflammatory response by transcriptionally repressing "
            "proinflammatory cytokine genes such as IL-1, IL-6, IL-12, and TNF-α."
        ),
        "head": "STAT3",
        "head_type": "transcription factor",
        "relation": "REPRESS",
        "tail": "IL-12",
        "tail_type": "gene",
    },
    {
        "text": (
            "STAT3 then travels to the nucleus where it stimulates the transcription of specific genes, "
            "which in-turn are thought to abrogate the inflammatory response by transcriptionally repressing "
            "proinflammatory cytokine genes such as IL-1, IL-6, IL-12, and TNF-α."
        ),
        "head": "STAT3",
        "head_type": "transcription factor",
        "relation": "REPRESS",
        "tail": "TNF-α",
        "tail_type": "gene",
    },
]
