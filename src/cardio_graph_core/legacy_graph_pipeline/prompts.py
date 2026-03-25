import argparse

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .graph_utils import escape_json
from .structured_classes import MedicRouter, TableRouter, Triples
from .templates import (
    GUIDELINES_EXAMPLES,
    GUIDELINES_EXAMPLES_SIMPLE,
    TABLE_PROMPT,
    TABLE_PROMPT_SIMPLE,
    TEXT_PROMPT,
    TEXT_PROMPT_SIMPLE,
)

triple_parser = JsonOutputParser(pydantic_object=Triples)
triple_format_instructions = escape_json(triple_parser.get_format_instructions())

table_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            TABLE_PROMPT_SIMPLE.format(
                format_instructions=triple_format_instructions,
                # examples=escape_json(json.dumps(GUIDELINES_EXAMPLES_SIMPLE)),
            ),
        ),
        (
            "human",
            "Extrahiere nun Tripel aus dem folgenden Input in dem vorgegebenen Format: {input}",
        ),
    ]
)

text_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            TEXT_PROMPT_SIMPLE.format(
                format_instructions=triple_format_instructions,
                # examples=escape_json(json.dumps(GUIDELINES_EXAMPLES_SIMPLE)),
            ),
        ),
        (
            "human",
            "Extrahiere nun Tripel aus dem folgenden Input in dem vorgegebenen Format: {input}",
        ),
    ]
)


table_routing_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            Bitte sage mir, ob es sich beim folgenden Text um eine vollständige Tabelle oder Auflistung handelt. Wenn Du Fließtext im Input findest, dann antworte mit "Nein".
            """,
        ),
        (
            "human",
            "Benutze für Deine Antwort das vorgebene Format. Input: {input}",
        ),
    ]
)


simplify_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            Du bist ein erfahrener Wissensgraph-Ersteller.
            Das folgende Tripel stammt aus einer Richtlinie zur Behandlung von chronischer Herzinsuffizienz.
			Bitte vereinfach es:
			* Löse Abkürzungen auf. Bleibe dabei aber stets medizinisch korrekt.
            * Wenn es für eine Abkürzung mehre Alternativen gibt, dann gib mehrere neue Tripel zurück.
            * Vereinfache und korrigiere die Relation zu einem einfachen Prädikat.
            Halte Dich an das folgende JSON Format:

			{format_instructions}

            WICHTIG:
            * Halte die Veränderungen auf Deutsch.
            """.format(
                format_instructions=triple_format_instructions
            ),
        ),
        (
            "human",
            "Benutze für Deine Antwort das vorgebene Format. Input: {input}",
        ),
    ]
)

hallu_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            Im folgenden siehst Du ein Tripel, dass aus einem Text extrahiert wurde.
			Bitte entscheide, ob dieses Tripel tatsächlich so im Text steht. 
			Antworte nur mit "ja" falls Du wirklich alle Wörter im Tripel im Text findest. Ansonsten antworte mit "nein".
            """,
        ),
        (
            "human",
            """
			Benutze für Deine Antwort das vorgebene Format. 

            Text: {text} 
			
			Input: {input}
			""",
        ),
    ]
)
