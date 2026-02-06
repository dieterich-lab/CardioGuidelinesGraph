from baml_client.sync_client import b 
from query_copy import RelationLogicOneHop, GetAllNodes


file_path = "/prj/doctoral_letters/guide/outputs2/test_query/triples_output.json"
output_path =  "/prj/doctoral_letters/guide/outputs2/baml_output"
prompt =     """Answer the quesion on whether an invasive or a conservative strategy is better for CCS Patients, tell me which end points are affected
Give the exact answer to the question, and then give the reasoning behind it.
Interpret the following Knowledge graph:"""

def main():
    triples = RelationLogicOneHop("angina-healt")
    #triples = GetAllNodes()
    statements = b.UnReificator(triples)
    b.Interpreter(triples, prompt, statements)
    #print(b.Easy(""))
    print("--------------------------------------------------")
    #result = b.SubgraphInterpreter(text, statements)
    #print(result)
if __name__ == "__main__":
    main()
