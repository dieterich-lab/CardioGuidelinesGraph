from query_copy import (
    GetAllNodes,
    UnReificatorTriples,
    pretty_print_triples,
    pretty_print_sep_statements,
    pretty_print_sum_statements,
)
from baml_client.sync_client import b
from baml_client.types import StatementSepIDSummarized, Summary
from neo4j import GraphDatabase

URI = "bolt://neo4j-dev2.internal:7687"
AUTH = ("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj")

# def SummarizeFlatStatement(statement):
#     s_statement = b.SummarizeStatement(statement)
#     return s_statement

# Statement Node ID: 132
#    Subject: rdf:statement
#    SubjectID: 128
#    Predicate: should be considered for
#    PredicateID: 131
#    Object: rdf:statement
#    ObjectID: 127
#    Summary: Symptom improvement achieved by revacularization should be considered for the symptomatic patient being treated with antianginal treatment despite their condition.

# Statement Node ID: 128
#    Subject: symptom improvement
#    SubjectID: 123
#    Predicate: by
#    PredicateID: 130
#    Object: revacularization
#    ObjectID: 124
#    Summary: Symptom improvement is achieved by revacularization.

# Statement Node ID: 127
#    Subject: symptomatic patient
#    SubjectID: 125
#    Predicate: despite
#    PredicateID: 129
#    Object: antianginal treatment
#    ObjectID: 126
#    Summary: The symptomatic patient is being treated with antianginal treatment despite their condition.

# Statement Node ID: 132
#    Subject: rdf:statement
#    SubjectID: 128
#    Predicate: should be considered for
#    PredicateID: 131
#    Object: rdf:statement
#    ObjectID: 127
#    Summary: Symptom improvement achieved by revacularization should be considered for the symptomatic patient being treated with antianginal treatment despite their condition.

id_testlist = ["132", "128", "127", "132"]
summary_testlist = [
    "Symptom improvement achieved by revacularization should be considered for the symptomatic patient being treated with antianginal treatment despite their condition.",
    "Symptom improvement is achieved by revacularization.",
    "The symptomatic patient is being treated with antianginal treatment despite their condition.",
    "Symptom improvement achieved by revacularization should be considered for the symptomatic patient being treated with antianginal treatment despite their condition.",
]


def recursive_summarizer(statement, raw_dict, summarized_dict):
    """
    Recursive function to summarize a statement and its subject and object.
    """
    subject_summary = Summary(summary="")
    object_summary = Summary(summary="")
    if statement.statement_node_ID in summarized_dict:
        return summarized_dict[statement.statement_node_ID]
    if statement.subject == "rdf:statement":
        if statement.subjectID in summarized_dict:
            subject_statement = summarized_dict[statement.subjectID]
        else:
            subject_statement = recursive_summarizer(
                raw_dict[statement.subjectID], raw_dict, summarized_dict
            )
        subject_summary = Summary(summary=subject_statement.summary)

    if statement.object == "rdf:statement":
        if statement.objectID in summarized_dict:
            object_statement = summarized_dict[statement.objectID]
        else:
            object_statement = recursive_summarizer(
                raw_dict[statement.objectID], raw_dict, summarized_dict
            )
        object_summary = Summary(summary=object_statement.summary)

    summary = b.SummarizeStatement(statement, subject_summary, object_summary)
    # summary = Summary(summary = "ABAJABA")
    s_statement = StatementSepIDSummarized(
        statement_node_ID=statement.statement_node_ID,
        subject=statement.subject,
        subjectID=statement.subjectID,
        predicate=statement.predicate,
        predicateID=statement.predicateID,
        object=statement.object,
        objectID=statement.objectID,
        summary=summary.summary,
    )
    print(
        f"Statement Node ID: {s_statement.statement_node_ID} \n   Subject: {s_statement.subject} \n   SubjectID: {s_statement.subjectID} \n   Predicate: {s_statement.predicate} \n   PredicateID: {s_statement.predicateID} \n   Object: {s_statement.object}\n   ObjectID: {s_statement.objectID}\n   Summary: {s_statement.summary}\n"
    )
    summarized_dict[s_statement.statement_node_ID] = s_statement
    return s_statement


def summarizer_main_loop(statements):
    """
    wrapper function for the recursive summarizer.
    """
    raw_dict = {}
    summarized_dict = {}
    for i, s in enumerate(statements.statement, 1):
        raw_dict[s.statement_node_ID] = s
    i = 0
    for key in raw_dict:
        # i += 1
        # if i > 1:
        #     break
        recursive_summarizer(raw_dict[key], raw_dict, summarized_dict)
    for key in summarized_dict:
        s_statement = summarized_dict[key]
        print(
            f"Statement Node ID: {s_statement.statement_node_ID} \n   Subject: {s_statement.subject} \n   SubjectID: {s_statement.subjectID} \n   Predicate: {s_statement.predicate} \n   PredicateID: {s_statement.predicateID} \n   Object: {s_statement.object}\n   ObjectID: {s_statement.objectID}\n   Summary: {s_statement.summary}\n"
        )
    return summarized_dict


def summarize_wrapper():
    """
    Wrapper function to get all Nodes,
    then call the summarizer_main_loop function to summarize the statements,
    and then update the summaries in the Neo4j database.
    """
    # Get all nodes from the database
    nodes = GetAllNodes()

    # Print the nodes to verify
    # print("LENGTH1", len(nodes))
    # pretty_print_triples(triples=nodes)
    statements = UnReificatorTriples(nodes)
    # pretty_print_sep_statements(statements)
    summarized_dict = summarizer_main_loop(statements)
    for key in summarized_dict:
        #    for x in range(len(id_testlist)):
        id = key
        summary = summarized_dict[key].summary
        true_id = ":" + id
        true_id = true_id[-3:]
        try:
            with GraphDatabase.driver(URI, auth=AUTH) as driver:
                driver.verify_connectivity()
                print("Connected to Neo4j database.")
                with driver.session() as session:
                    query = f"""
                    MATCH (n:Node)
                    WHERE RIGHT(elementId(n),3) = "{true_id}"
                    SET n.summary = "{summary}"
                    RETURN n
                    """
                    session.run(query)
                    print("Summary updated successfully for Node ID:", true_id)
        except Exception as e:
            print(f"Database connection error: {str(e)}")
    return


if __name__ == "__main__":
    summarize_wrapper()
