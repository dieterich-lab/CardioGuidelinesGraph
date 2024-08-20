from __future__ import annotations

from typing import List, Optional

from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    PromptTemplate,
)
from langchain_core.prompts.prompt import PromptTemplate
from langchain_experimental.graph_transformers.llm import UnstructuredRelation


def create_unstructured_prompt(
    base_string_parts,
    examples,
    template,
    node_labels: Optional[List[str]] = None,
    rel_types: Optional[List[str]] = None,
) -> ChatPromptTemplate:
    system_prompt = "\n".join(filter(None, base_string_parts))

    system_message = SystemMessage(content=system_prompt)
    parser = JsonOutputParser(pydantic_object=UnstructuredRelation)

    human_prompt = PromptTemplate(
        template=template,
        input_variables=["input"],
        partial_variables={
            "format_instructions": parser.get_format_instructions(),
            "node_labels": node_labels,
            "rel_types": rel_types,
            "examples": examples,
        },
    )

    human_message_prompt = HumanMessagePromptTemplate(prompt=human_prompt)

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message, human_message_prompt]
    )
    return chat_prompt
