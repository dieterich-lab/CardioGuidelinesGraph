from __future__ import annotations

import json
from typing import Any, List, Optional, Type, TypeVar, Union

import pydantic  # pydantic: ignore
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    PromptTemplate,
)
from langchain_core.prompts.prompt import PromptTemplate
from langchain_experimental.graph_transformers.llm import UnstructuredRelation
from pydantic import BaseModel, Field, create_model

JSON_FORMAT_INSTRUCTIONS = """Der output sollte als JSON formartiert sein, das dem unten aufgeführten JSON-Schema enstpricht.

Beispielsweise, ist für das Schema {{"Eigenschaften": {{"foo": {{"Titel": "Foo", "Beschreibung": "Eine Liste von Zeichenketten", "Type": "Feld", "Elemente": {{"Typ": "Zeichenkeite"}}}}}}, "notwendig": ["foo"]}}
das Objekt {{"foo": ["bar", "baz"]}} eine wohlgeformte Instanz des Schemas. Das Objekt {{"properties": {{"foo": ["bar", "baz"]}}}} ist nicht wohlgeformt.
```
{schema}

```"""


class MyJsonOutputParser(JsonOutputParser):

    def get_format_instructions(self) -> str:
        """Return the format instructions for the JSON output.

        Returns:
            The format instructions for the JSON output.
        """
        # return JSON_FORMAT_INSTRUCTIONS
        if self.pydantic_object is None:
            return "Return a JSON object."
        else:
            # Copy schema to avoid altering original Pydantic schema.
            schema = {k: v for k, v in self._get_schema(self.pydantic_object).items()}

            # Remove extraneous fields.
            reduced_schema = schema
            if "Titel" in reduced_schema:
                del reduced_schema["Titel"]
            if "Typ" in reduced_schema:
                del reduced_schema["Typ"]
            # if "title" in reduced_schema:
            #     del reduced_schema["title"]
            # if "type" in reduced_schema:
            #     del reduced_schema["type"]
            # Ensure json in context is well-formed with double quotes.
            schema_str = json.dumps(reduced_schema)
            return JSON_FORMAT_INSTRUCTIONS.format(schema=schema_str)


class MyUnstructuredRelation(BaseModel):
    head: str = Field(
        description=(
            "Extrahierte Start-Entität wie Microsoft, Apple, John. "
            "Muss einen von Menschen lesbaren einzigargtigen Identifizerer benutzen."
        )
    )
    head_type: str = Field(
        description="Typ der extrahierten Start-Entität wie Person, Firma, etc"
    )
    relation: str = Field(description="relation between the head and the tail entities")
    relation: str = Field(description="Relation zwischen der Start- und End-Entität")
    tail: str = Field(
        description=(
            "Extrahierte End-Entität wie Microsoft, Apple, John. "
            "Muss einen von Menschen lesbaren einzigargtigen Identifizerer benutzen."
        )
    )
    tail_type: str = Field(
        description="Typ der extrahierten End-Entität wie Person, Firma, etc"
    )


def create_unstructured_prompt(
    base_string_parts,
    examples,
    template,
    node_labels: Optional[List[str]] = None,
) -> ChatPromptTemplate:
    system_prompt = "\n".join(filter(None, base_string_parts))

    system_message = SystemMessage(content=system_prompt)
    parser = MyJsonOutputParser(pydantic_object=MyUnstructuredRelation)
    # parser = JsonOutputParser(pydantic_object=UnstructuredRelation)

    human_prompt = PromptTemplate(
        template=template,
        input_variables=["input"],
        partial_variables={
            "format_instructions": parser.get_format_instructions(),
            "node_labels": node_labels,
            "examples": examples,
        },
    )

    human_message_prompt = HumanMessagePromptTemplate(prompt=human_prompt)

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message, human_message_prompt]
    )
    return chat_prompt
