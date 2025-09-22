import os
from openai import OpenAI

api_key = os.getenv("KG_GENERATOR_API_KEY_FIRST")
client = OpenAI(api_key=api_key)
#current_model = "gpt-5"
current_model = "gpt-4.1-nano"

medium_text = (
    "The CLARIFY registry found that many CCS patients with angina experience a "
    "resolution of symptoms over time, often without changes in treatment or revascularization"
)

print(medium_text)


def simplify_text(text: str) -> str:
    """Simplify input text into atomic, self-contained sentences."""
    response = client.chat.completions.create(
        model=current_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a top tier AI specialized in constructing knowledge "
                    "graphs from text, guidelines, or structured/unstructured input."
                ),
            },
            {
                "role": "user",
                "content": f"""
                    Simplify the following text into a list of atomic, self-contained sentences.
                    Each sentence should express only one idea or claim.
                    If a sentence contains both a source (such as a study, registry, or expert) and a claim, split them so that the claim is one sentence and the attribution is a separate sentence referencing the claim.
                    Avoid using pronouns ("this", "these", "it") as subjects—repeat the subject explicitly if necessary.
                    Preserve all information with zero semantic loss.

                    Example:
                    Input:
                    A recent study reported that high blood pressure increases the risk of stroke, especially in elderly patients.

                    Output:
                    1. "High blood pressure increases the risk of stroke."
                    2. "Sentence 1 especially in elderly patients."
                    3. "A recent study reported sentence 1."

                    Now simplify this text:
                    {text}
                    """,
            },
        ],
    )
    return response.choices[0].message.content.strip()


def easy_formatting(text: str) -> str:
    """Simplify input text into atomic, self-contained sentences."""
    response = client.chat.completions.create(
        model=current_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a top tier AI specialized in constructing knowledge "
                    "graphs from text, guidelines, or structured/unstructured input."
                ),
            },
            {
                "role": "user",
                "content": f"""Simplify the following text into a list of atomic, self-contained sentences.
                    Each sentence should express only one idea or claim.
                    If a sentence contains both a source (such as a study, registry, or expert) and a claim, split them so that the claim is one sentence and the attribution is a separate sentence referencing the claim.
                    Avoid using pronouns ("this", "it", etc.) as subjects—repeat the subject explicitly if necessary.
                    Preserve all information with zero semantic loss.

                    Now simplify this text:
                    {text}
                    """,
            },
        ],
    )
    return response.choices[0].message.content.strip()


def hypergrapher(text: str) -> str:
    """create hypergraph from text"""
    response = client.chat.completions.create(
        model=current_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a top tier AI specialized in constructing knowledge "
                    "graphs from text, guidelines, or structured/unstructured input."
                ),
            },
            {
                "role": "user",
                "content": f""" Extract all triples from the following sentences.
                    Nested Statements may be represented by using Nodes that represent entire Statements, indexed by the sentence ID

                    Now transform this text into triples:
                    {text}
                    """,
            },
        ],
    )
    return response.choices[0].message.content.strip()


def prototype_nester(sentences: str, original_text) -> str:
    """reificate given sentences"""
    response = client.chat.completions.create(
        model=current_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a top tier AI specialized in constructing knowledge "
                    "graphs from text, guidelines, or structured/unstructured input."
                ),
            },
            {
                "role": "user",
                "content": f""""If the follwing sentences contain nested statements, identify the nested statement and represent them in a sequence of sentences that each may reference other sentences in the same list"
                    The reference is done by using the sentence ID of the referenced sentence in parentheses.
                    everytime there is a sentence with a reference please explain the full sentence in the explanation field.

                    Example:
                    1. Patients with Fever and a recent travel History to Ghana 
                    2. These Patients should visit a doctor
                    3. This is recommended by the guidelines
                    3. These Patients are at risk of Malaria

                    Nested Statements identified and transformed:
                    1. Patients with Fever and a recent travel History to Ghana 
                    2. (Sentence ID:1) should visit a doctor (meaning: Patients with Fever and a recent travel History to Ghana should visit a doctor)
                    3. (Sentence ID:2) is recommended by the guidelines (meaning: The guidelines recommend that patients with Fever and a recent travel History to Ghana should visit a doctor)
                    3. (Sentence ID:1) are at risk of Malaria (meaning: Patients with Fever and a recent travel History to Ghana are at risk of Malaria)

                    Consider if each sentence represents a full truth, as a false example: "a study has shown that Patients with Fever and a recent travel History to Ghana should visit a doctor"
                    1. A study has found a result
                    2. (Sentence ID:1) involves Patients with Fever and a recent travel History to Ghana (meaning: The study results involve patients with Fever and a recent travel History to Ghana)
                    3. (Sentence ID:2) should visit a doctor (meaning: Patients with Fever and a recent travel History to Ghana should visit a doctor)
                    This is wrong because the second sentence does not represent a full truth on its own it is too incomplete since the study encompasses not only the patients but also the fact that they should visit a doctor
                    Corrected:
                    1. Patients with Fever and a recent travel History to Ghana
                    2. (Sentence ID:1) should visit a doctor (meaning: Patients with Fever and a recent travel History to Ghana should visit a doctor)
                    3. (Sentence ID:2) is shown by a study (meaning: A study has shown that patients with Fever and a recent travel History to Ghana should visit a doctor)

                    You may change the sentences and sentence order in order to get the optimal nesting of statements.

                    DO NOT use the Sentence ID references in the explanation field, just use the full sentence spelled out.

                    Keep your thinking process short and concise, focus on the task at hand.
                    Immediatly output the result if you find yourself thinking the same thing more than twice.

                    Please apply this method to the following sentences:
                    {sentences}
                    Consider the original text:
                    {original_text}
                    """,
            },
        ],
    )
    return response.choices[0].message.content.strip()


nested_output = """ 1. Many CCS patients with angina experience a resolution of angina symptoms over time.
2. The resolution described in (Sentence ID:1) often occurs without changes in treatment or revascularization.
   Explanation: The resolution of angina symptoms over time experienced by many CCS patients with angina often occurs without changes in treatment or revascularization.
3. (Sentence ID:1) was found by the CLARIFY registry.
   Explanation: The CLARIFY registry found that many CCS patients with angina experience a resolution of angina symptoms over time.
4. (Sentence ID:2) was found by the CLARIFY registry.
   Explanation: The CLARIFY registry found that the resolution of angina symptoms over time experienced by many CCS patients with angina often occurs without changes in treatment or revascularization."""

if __name__ == "__main__":
    # hypergraph_output = hypergrapher(medium_text)
    # print("\nHypergraph Output:\n", hypergraph_output)
    # simplified_output = simplify_text(medium_text)
    # print("\nSimplified Text:\n", simplified_output)
    # nested_output = prototype_nester(simplified_output, medium_text)
    # print("\nNested Output:\n", nested_output)
    hypergraph_output = hypergrapher(nested_output)
    print("\nHypergraph Chain Output:\n", hypergraph_output)
    # easy_formatting_output = easy_formatting(medium_text)
    # print("\nEasy Formatting Output:\n", easy_formatting_output)
