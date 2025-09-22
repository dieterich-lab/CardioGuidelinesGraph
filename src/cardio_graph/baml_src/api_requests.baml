class APINode {
  label string @description("the label of the node, ONLY: 'Node', 'AND', 'Predicate'")
  id string @description("the ID of the node")
  value string @description("the value of the node")
}

class APINodes {
  nodes APINode[] @description("a list of nodes")
}


class APITriple {
  head_node_label string @description("the label of the head node, ONLY: 'Node', 'AND', 'Predicate'")
  head_node_id string @description("the ID of the head node")
  head_node_value string @description("the value of the head node")
  relation string @description("the relation of the head node to the tail node")
  tail_node_label string @description("the label of the tail node, ONLY: 'Node', 'AND', 'Predicate'")
  tail_node_id string @description("the ID of the tail node")
  tail_node_value string @description("the value of the tail node")
}
class APITriples {
  triples APITriple[] @description("a list of triples")
}


function APIEasyFormatting(input: string) -> SentencesID {
  client GPT41Nano
  prompt #"
    Simplify the following text into a list of atomic, self-contained sentences.
    Each sentence should express only one idea or claim.
    If a sentence contains both a source (such as a study, registry, or expert) and a claim, split them so that the claim is one sentence and the attribution is a separate sentence referencing the claim.
    Avoid using pronouns ("this", "it", etc.) as subjects—repeat the subject explicitly if necessary.
    Preserve all information with zero semantic loss.
    {{input}}
    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}

function APIPrototypeNester(sentences: SentencesID, original: string) -> SentencesIDexplanation {
  client GPT5
  prompt #"
    "If the follwing sentences contain nested statements, identify the nested statement and represent them in a sequence of sentences that each may reference other sentences in the same list"
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
    {{sentences}}
    Consider the original text:
    {{original}}

    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}

function APIHypergrapher(input: SentencesIDexplanation) -> TriplesID {
  client GPT41Nano
  prompt #"
    Extract all triples from the following sentences.
    Nested Statements may be represented by using Nodes that represent entire Statements, indexed by the sentence ID

    Keep your thinking process short and concise, focus on the task at hand.
    Immediatly output the result if you find yourself thinking the same thing more than twice.
    
    {{input}}
    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}

function APITotalConverter(string: string) -> APITriples {
  client GPT5
  prompt #"
    You are tasked with transforming text into a knowledge graph representation using **Nodes** and **Triples**. Follow these rules exactly.  

    1. Nodes
    - Format: (Label; value:"...", id:X)  
    - Labels:  
    - Node → default for all entities.  
    - AND → for conjunctions (always also a Node).  
    - Predicate → only when reifying a statement.  
    - Properties:  
    - id: unique identifier.  
    - value: string name of the entity/predicate.  

    2. Triples
    - Format: (subject_id, relation, object_id)  

    3. Rules
    1. Simple relations:  
    - If text expresses a single fact: (X, predicate, Y).  

    2. Conjunctions (AND):  
    - Use an AND node.  
    - Link conjuncts with (conjunct, part_of, AND-node).  
    - The AND-node may then serve as subject/object.  

    3. Disjunctions (OR):  
    - Do not create an OR node.  
    - Split into separate statements with the same subject and predicate.  

    4. Reification (Nested Statements):  
    - If a statement is attributed to a source (“According to X, …”):  
        - Create a Predicate node for the relation.  
        - Create an rdf_statement node with a summary.  
        - Link as:  
        (rdf_statement, rdf_subject, subj_id)  
        (rdf_statement, rdf_predicate, pred_id)  
        (rdf_statement, rdf_object, obj_id)  
        (source, states, rdf_statement)  

    4. Example A — AND + Reification
    Text:  
    “According to ESC guidelines, CCS patients with angina should receive conservative medical management.”  

    Nodes:  
    (Node; value:"ESC Guidelines"; id:10)  
    (AND; value:"CCS patients with angina"; id:11)  
    (Node; value:"CCS patients"; id:12)  
    (Node; value:"angina"; id:13)  
    (Node; value:"conservative medical management"; id:14)  
    (Predicate; value:"shows"; id:15)  
    (Node; value:"rdf_statement"; summary:"According to ESC guidelines, CCS patients with angina should receive conservative medical management"; id:16)  

    Triples:  
    (12, part_of, 11)  
    (13, part_of, 11)  
    (16, rdf_subject, 11)  
    (16, rdf_predicate, 15)  
    (16, rdf_object, 14)  
    (10, states, 16)  

    5. Example B — OR
    Text:  
    “Patients with atrial fibrillation may be treated with aspirin or clopidogrel.”  

    Nodes:  
    (AND; value:"Patients with atrial fibrillation"; id:20)  
    (Node; value:"Patients"; id:21)  
    (Node; value:"atrial fibrillation"; id:22)  
    (Node; value:"aspirin"; id:23)  
    (Node; value:"clopidogrel"; id:24)  

    Triples:  
    (21, part_of, 20)  
    (22, part_of, 20)  
    (20, may_be_treated_with, 23)  
    (20, may_be_treated_with, 24)  

    Now, apply these rules to the following text, consider the notation in markdown:
    {{string}}  

    {{ ctx.output_format}}  

  "#
}
