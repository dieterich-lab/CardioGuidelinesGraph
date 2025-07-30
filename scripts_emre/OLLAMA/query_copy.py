from neo4j import GraphDatabase
from baml_client.types import Node, Nodes, Triple, Triples, StatementSepID, StatementsSepID, Statement, Statements, ANDStatement, ANDStatements
import json
from collections import defaultdict
# Database configuration
URI = "bolt://neo4j-dev2.internal:7687"
AUTH = ("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj")
DIR = "/prj/doctoral_letters/guide/outputs2/test_query"


def LogicIdentifier(node, session, zero_nodes, printing=False):
    # if node is an AND node, find all the next neighbors
    if "AND" in node.labels:
        if printing: print("\nAND node found, processing...")
        #query for all relationships of the node
        root_id = node.element_id
        root_value = node.get("value")
        query = f"""
        MATCH (n) 
        WHERE elementId(n) = "{root_id}"
        MATCH p = (n)--(next_neighbor)
        RETURN p
        """
        result = session.run(query)
        #create a set to store the met and unmet conditions
        met_conditions = []
        unmet_conditions = []
        output_list = []
        for record in result:
            for relationship in record["p"].relationships:
                #get the head and tail of each relationship
                head_id = relationship.start_node.element_id
                head_value = relationship.start_node.get("value")
                head_tuple = (head_id, head_value)
                head_tuple_baml = Node(id = head_id[-3:], value=head_value)
                tail_id = relationship.end_node.element_id
                tail_value = relationship.end_node.get("value")
                tail_tuple = (tail_id, tail_value)
                # print("head id:...", head_tuple)
                # print("tail id:...", tail_tuple)
                if head_tuple == (root_id, root_value):
                    triple = Triple(
                        head_node_id=head_id[-3:],
                        head_node_value=head_value,
                        relation=relationship.type,
                        tail_node_id=tail_id[-3:],
                        tail_node_value=tail_value
                    )
                    output_list.append(triple)
                    # print("\nDOWNSTREAM")
                    # print(node.element_id)
                    # print("Relationship:", relationship.type)

                #if the AND node is the tail of the relationship    
                if tail_tuple == (root_id, root_value):
                    if relationship.type == "rdf:subject":
                        triple = Triple(
                            head_node_id=head_id[-3:],
                            head_node_value=head_value,
                            relation=relationship.type,
                            tail_node_id=tail_id[-3:],
                            tail_node_value=tail_value
                        )
                        output_list.append(triple)
                    # print("\nUPSTREAM")
                    # print(node.element_id)
                    # print("Relationship:", relationship.type)

                    # check if the relationship type is "part of" which makes it a condition for the AND statement
                    if relationship.type == "part of":
                        if head_tuple in zero_nodes:
                            met_conditions.append(head_tuple_baml)
                        else:
                            unmet_conditions.append(head_tuple_baml)
        LogicAnalysis = ANDStatement(
            statement = Node(id = root_id[-3:] , value = root_value),
            met_conditions = Nodes(nodes=met_conditions),
            unmet_conditions = Nodes(nodes= unmet_conditions),
            output= Triples(triples=output_list)
        )
        # [AND Node, met conditions, unmet conditions, output set]
        if printing:
            print("\nConditional Analysis of AND node:", root_value)
            print("Met conditions:", met_conditions)
            if not unmet_conditions:
                print("All conditions met for this AND node.")
            else: 
                print("missing conditions for this AND node:", unmet_conditions)
            print("\nOutput set:", output_list)
        return LogicAnalysis
    else: return 



def RecursiveHop(neighbor, session, visited_nodes, zero_nodes, found_relations, logic_analysis):
    # recursive graph traversal with extending over rdf:statements and AND Nodes
    # Call LogicIdentifier for this node to check if the AND conditions are met
    logic = LogicIdentifier(neighbor, session, zero_nodes)
    if logic is not None:
        logic_analysis.append(logic)

    # if the node is either a statement node or an AND node, continue with the hops
    if (neighbor.get("value") == "rdf:statement" or ("AND" in neighbor.labels)):
        second_query = f"""
        MATCH (n) 
        WHERE elementId(n) = "{neighbor.element_id}"
        MATCH p=(n)--(next_neighbor)
        RETURN p,next_neighbor
        """
        #find all the next neighbors of the current node
        second_result = session.run(second_query)
        for second_record in second_result:
            next_neighbor_tuple = (second_record["next_neighbor"].element_id, second_record["next_neighbor"].get("value"))
            rel_tuple = (second_record["p"].relationships[0].type, second_record["p"].relationships[0].start_node.element_id,second_record["p"].relationships[0].start_node.get("value") , second_record["p"].relationships[0].end_node.element_id,second_record["p"].relationships[0].end_node.get("value"))
            if rel_tuple not in found_relations:
                # add the relationship to the found relations set
                found_relations.add(rel_tuple)
            # check if the next neighbor is already visited
            if next_neighbor_tuple not in visited_nodes:
                # add the next neighbor to the visited nodes
                visited_nodes.add(next_neighbor_tuple)
                # explore the next neighbor recursively
                RecursiveHop(second_record["next_neighbor"], session, visited_nodes, zero_nodes, found_relations, logic_analysis)

def GetAllNodes():
    #function to return all triples of the KG
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
            print("Connected to Neo4j database.")
            with driver.session() as session:
                print("Processing GetAllNodes...")
                query = """
                MATCH p = (n:Node)--(p2)
                RETURN p, n, p2
                """
                result = list(session.run(query))

                raw_triples = set()
                for record in result:
                    path = record["p"]
                    rel = path.relationships[0]
                    triple_tuple = (
                        rel.type,
                        rel.start_node.element_id,
                        rel.start_node.get("value"),
                        rel.end_node.element_id,
                        rel.end_node.get("value")
                    )
                    raw_triples.add(triple_tuple)

                print("Found relations:")
                triples = []
                for t in raw_triples:
                    print(f"{t[1][-3:]}/{t[2]} -- {t[0]} --> {t[3][-3:]}/{t[4]}")
                    triple = Triple(
                        head_node_id=t[1][-3:],
                        head_node_value=t[2],
                        relation=t[0],
                        tail_node_id=t[3][-3:],
                        tail_node_value=t[4]
                    )
                    triples.append(triple)

                wrapped = Triples(triples=triples)
                return wrapped


    except Exception as e:
        print(f"Database connection error: {str(e)}")

def OneHop(string):
    # Use a set of node IDs instead of node objects
    visited_nodes = set()
    zero_nodes = set()
    found_relations = set()
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
            print("Connected to Neo4j database.")
            #cypher onehop query
            with driver.session() as session:
                print("Processing OneHop...")
                query = f"""
                MATCH (zero:Node)--(neighbour)
                WHERE zero.value CONTAINS "{string}"
                RETURN zero, neighbour
                """
                result = list(session.run(query))
                # iterate over the query results
                for record in result:
                    # save the element_id and value of the nodes in a tuple for further processing
                    zero_tuple = (record["zero"].element_id,record["zero"].get("value"))
                    neighbor_tuple = (record["neighbour"].element_id,record["neighbour"].get("value"))

                    # check if the zero hop nodes are already visited
                    if zero_tuple not in zero_nodes:
                        # add the zero hop node to the zero nodes set
                        zero_nodes.add(zero_tuple)
                    
                    # Store (id, value) tuples in the visited nodes set
                    if zero_tuple not in visited_nodes:
                        visited_nodes.add(zero_tuple)
                    if neighbor_tuple not in visited_nodes:
                        visited_nodes.add(neighbor_tuple)

                # iterate over the query results again to process the neighbors
                for tryagain in result:  

                    # call recursive hop for the neighbors
                    RecursiveHop(tryagain["neighbour"], session, visited_nodes, zero_nodes, found_relations)

                #print the visited nodes and zero hop nodes
                print("\nVisited nodes:")
                for node in visited_nodes:
                    print(node[1])
                print("\nZero nodes:")
                for node in zero_nodes:
                    print(node[1])
                    
    except Exception as e:
        print(f"Database connection error: {str(e)}")

def LogicOneHop(string):
    # Use a set of node IDs instead of node objects
    visited_nodes = set()
    zero_nodes = set()
    found_relations = set()
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
            print("Connected to Neo4j database.")
            #cypher onehop query
            with driver.session() as session:
                print("Processing OneHop...")
                query = f"""
                MATCH (zero:Node)--(neighbour)
                WHERE zero.value CONTAINS "{string}"
                RETURN zero, neighbour
                """
                result = list(session.run(query))
                # iterate over the query results
                for record in result:
                    # save the element_id and value of the nodes in a tuple for further processing
                    zero_tuple = (record["zero"].element_id,record["zero"].get("value"))
                    neighbor_tuple = (record["neighbour"].element_id,record["neighbour"].get("value"))

                    # check if the zero hop nodes are already visited
                    if zero_tuple not in zero_nodes:
                        # add the zero hop node to the zero nodes set
                        zero_nodes.add(zero_tuple)
                    
                    # Store (id, value) tuples in the visited nodes set
                    if zero_tuple not in visited_nodes:
                        visited_nodes.add(zero_tuple)
                    if neighbor_tuple not in visited_nodes:
                        visited_nodes.add(neighbor_tuple)
                # iterate over the query results again to process the neighbors
                for tryagain in result:  
                    # call LogicIdentifier for the zero nodes
                    LogicIdentifier(tryagain["zero"], session, zero_nodes)
                    # call recursive hop for the neighbors
                    RecursiveHop(tryagain["neighbour"], session, visited_nodes, zero_nodes, found_relations)

                print("\nVisited nodes:")
                for node in visited_nodes:
                    print(node[1])
                print("\nZero nodes:")
                for node in zero_nodes:
                    print(node[1])

    except Exception as e:
        print(f"Database connection error: {str(e)}")

def RelationLogicOneHop(string):
    #find substring match and do an extended onehop
    # Use a set of node IDs instead of node objects
    visited_nodes = set()
    found_relations = set()
    zero_nodes = set()
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
            print("Connected to Neo4j database.")
            #cypher onehop query
            with driver.session() as session:
                print("Processing OneHop...")
                query = f"""
                MATCH p = (zero:Node)--(neighbour)
                WHERE zero.value CONTAINS "{string}"
                RETURN p, zero, neighbour
                """
                result = list(session.run(query))
                # iterate over the query results
                for record in result:
                    # save the element_id and value of the nodes in a tuple for further processing
                    zero_tuple = (record["zero"].element_id,record["zero"].get("value"))
                    neighbor_tuple = (record["neighbour"].element_id,record["neighbour"].get("value"))
                    # save the relationship type and the element_id and value of the nodes in a tuple for further processing
                    rel_tuple = (record["p"].relationships[0].type, record["p"].relationships[0].start_node.element_id,record["p"].relationships[0].start_node.get("value") , record["p"].relationships[0].end_node.element_id,record["p"].relationships[0].end_node.get("value"))
                    # check if the zero hop nodes are already visited
                    if zero_tuple not in zero_nodes:
                        # add the zero hop node to the zero nodes set
                        zero_nodes.add(zero_tuple)
                    if rel_tuple not in found_relations:
                        # add the relationship to the found relations set
                        found_relations.add(rel_tuple)
                    # Store (id, value) tuples in the visited nodes set
                    if zero_tuple not in visited_nodes:
                        visited_nodes.add(zero_tuple)
                    if neighbor_tuple not in visited_nodes:
                        visited_nodes.add(neighbor_tuple)
                # iterate over the query results again to process the neighbors
                for tryagain in result:  
                    # call LogicIdentifier for the zero nodes
                    LogicIdentifier(tryagain["zero"], session, zero_nodes)
                    # call recursive hop for the neighbors
                    RecursiveHop(tryagain["neighbour"], session, visited_nodes, zero_nodes, found_relations)

                print("\nVisited nodes:")
                for node in visited_nodes:
                    print(node[1])
                print("\nZero nodes:")
                for node in zero_nodes:
                    print(node[1])
                print("\nFound relations:")
                triples = []
                for rel in found_relations:
                    triple = Triple(
                        head_node_id=rel[1][-3:],
                        head_node_value=rel[2],
                        relation=rel[0],
                        tail_node_id=rel[3][-3:],
                        tail_node_value=rel[4]
                    )
                    triples.append(triple)

                wrapped = Triples(triples=triples)

                return wrapped
                # for rel in found_relations:
                #     print(rel[1][-3:],"/", rel[2],"--", rel[0],"-->",rel[3][-3:],"/", rel[4])
                # json_output = []
                # for rel in found_relations:
                #     json_output.append({
                #         "head_id": rel[1],
                #         "head_label": rel[2],
                #         "relation": rel[0],
                #         "tail_id": rel[3],
                #         "tail_label": rel[4]
                #         })
                # print(json.dumps(json_output, indent=2))
                #print(json_output)


    except Exception as e:
        print(f"Database connection error: {str(e)}")

def ExactLogicOneHop(string):
    #only exact string match and extended onehop
    # Use a set of node IDs instead of node objects
    visited_nodes = set()
    found_relations = set()
    zero_nodes = set()
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
            print("Connected to Neo4j database.")
            #cypher onehop query
            with driver.session() as session:
                print("Processing OneHop...")
                query = f"""
                MATCH p = (zero:Node)--(neighbour)
                WHERE zero.value = "{string}"
                RETURN p, zero, neighbour
                """
                result = list(session.run(query))
                # iterate over the query results
                for record in result:
                    # save the element_id and value of the nodes in a tuple for further processing
                    zero_tuple = (record["zero"].element_id,record["zero"].get("value"))
                    neighbor_tuple = (record["neighbour"].element_id,record["neighbour"].get("value"))
                    # save the relationship type and the element_id and value of the nodes in a tuple for further processing
                    rel_tuple = (record["p"].relationships[0].type, record["p"].relationships[0].start_node.element_id,record["p"].relationships[0].start_node.get("value") , record["p"].relationships[0].end_node.element_id,record["p"].relationships[0].end_node.get("value"))
                    # check if the zero hop nodes are already visited
                    if zero_tuple not in zero_nodes:
                        # add the zero hop node to the zero nodes set
                        zero_nodes.add(zero_tuple)
                    if rel_tuple not in found_relations:
                        # add the relationship to the found relations set
                        found_relations.add(rel_tuple)
                    # Store (id, value) tuples in the visited nodes set
                    if zero_tuple not in visited_nodes:
                        visited_nodes.add(zero_tuple)
                    if neighbor_tuple not in visited_nodes:
                        visited_nodes.add(neighbor_tuple)
                # iterate over the query results again to process the neighbors
                for tryagain in result:  
                    # call LogicIdentifier for the zero nodes
                    LogicIdentifier(tryagain["zero"], session, zero_nodes)
                    # call recursive hop for the neighbors
                    RecursiveHop(tryagain["neighbour"], session, visited_nodes, zero_nodes, found_relations)

                print("\nVisited nodes:")
                for node in visited_nodes:
                    print(node[1])
                print("\nZero nodes:")
                for node in zero_nodes:
                    print(node[1])
                print("\nFound relations:")
                triples = []
                for rel in found_relations:
                    triple = Triple(
                        head_node_id=rel[1][-3:],
                        head_node_value=rel[2],
                        relation=rel[0],
                        tail_node_id=rel[3][-3:],
                        tail_node_value=rel[4]
                    )
                    triples.append(triple)

                wrapped = Triples(triples=triples)

                return wrapped
                # for rel in found_relations:
                #     print(rel[1][-3:],"/", rel[2],"--", rel[0],"-->",rel[3][-3:],"/", rel[4])
                # json_output = []
                # for rel in found_relations:
                #     json_output.append({
                #         "head_id": rel[1],
                #         "head_label": rel[2],
                #         "relation": rel[0],
                #         "tail_id": rel[3],
                #         "tail_label": rel[4]
                #         })
                # print(json.dumps(json_output, indent=2))
                #print(json_output)


    except Exception as e:
        print(f"Database connection error: {str(e)}")        

def ExactLogicOneHopMultithreaded(string, visited_nodes, found_relations, zero_nodes,logic_analysis,node_is_a_condition, printing=True):
    #find exact string match and extended onehop until meeting visited nodes
    # Use a set of node IDs instead of node objects
    try:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
            if printing: print("Connected to Neo4j database.")
            #cypher onehop query
            with driver.session() as session:
                if printing: print("Processing OneHop...")
                query = f"""
                MATCH p = (zero:Node)--(neighbour)
                WHERE zero.value = "{string}"
                RETURN p, zero, neighbour
                """
                result = list(session.run(query))
                # iterate over the query results
                for record in result:
                    # save the element_id and value of the nodes in a tuple for further processing
                    zero_tuple = (record["zero"].element_id,record["zero"].get("value"))
                    neighbor_tuple = (record["neighbour"].element_id,record["neighbour"].get("value"))
                    # save the relationship type and the element_id and value of the nodes in a tuple for further processing
                    rel_tuple = (record["p"].relationships[0].type, record["p"].relationships[0].start_node.element_id,record["p"].relationships[0].start_node.get("value") , record["p"].relationships[0].end_node.element_id,record["p"].relationships[0].end_node.get("value"))
                    # check if the zero hop nodes are already visited
                    if node_is_a_condition and (zero_tuple not in zero_nodes):
                        # add the zero hop node to the zero nodes set
                        zero_nodes.add(zero_tuple)
                    if rel_tuple not in found_relations:
                        # add the relationship to the found relations set
                        found_relations.add(rel_tuple)
                    # Store (id, value) tuples in the visited nodes set
                    if zero_tuple not in visited_nodes:
                        visited_nodes.add(zero_tuple)
                    if neighbor_tuple not in visited_nodes:
                        visited_nodes.add(neighbor_tuple)
                # iterate over the query results again to process the neighbors
                for tryagain in result:  
                    # call LogicIdentifier for the zero nodes
                    logic = LogicIdentifier(tryagain["zero"], session, zero_nodes)                  
                    if logic is not None:
                        logic_analysis.append(logic)
                    # call recursive hop for the neighbors
                    RecursiveHop(tryagain["neighbour"], session, visited_nodes, zero_nodes, found_relations, logic_analysis)
                if printing:
                    print("\nVisited nodes:")
                    for node in visited_nodes:
                        print(node[1])
                    print("\nZero nodes:")
                    for node in zero_nodes:
                        print(node[1])
                    print("\nFound relations:")
                triples = []
                for rel in found_relations:
                    triple = Triple(
                        head_node_id=rel[1][-3:],
                        head_node_value=rel[2],
                        relation=rel[0],
                        tail_node_id=rel[3][-3:],
                        tail_node_value=rel[4]
                    )
                    triples.append(triple)

                wrapped = Triples(triples=triples)

                return wrapped, visited_nodes, found_relations, zero_nodes, logic_analysis
            
    except Exception as e:
        print(f"Database connection error: {str(e)}")     

def ExactLogicOneHopMultithreadedWrapper(true_given_nodes, queryable_nodes, printing = False):
    visited_nodes = set()
    found_relations = set()
    zero_nodes = set()
    logic_analysis = []
    for node in queryable_nodes:
        node_is_a_condition = False
        if node in true_given_nodes:
            node_is_a_condition = True
        if printing: 
            print("-" * 60)
            print("One Hop for:", node)
        triples, visited_nodes, found_relations, zero_nodes, logic_analysis = ExactLogicOneHopMultithreaded(node, visited_nodes, found_relations, zero_nodes, logic_analysis, node_is_a_condition)
        processed_logic_analysis = ANDStatements(and_statements=logic_analysis)
        if printing:
            pretty_print_triples(triples)
            print("-" * 60)
    return triples, found_relations, processed_logic_analysis

def pretty_print_triples(triples, visited_nodes=None, found_relations=None, zero_nodes=True):
    for i, t in enumerate(triples.triples, 1):
        print(f"{i:2d}. {t.head_node_value} (ID: {t.head_node_id}) --[{t.relation}]--> {t.tail_node_value} (ID: {t.tail_node_id})")
    # if visited_nodes is not None:
    #     print("\nVisited nodes:")
    #     for node in visited_nodes:
    #         print(node[1])
    # if zero_nodes is not None:
    #     print("\nZero nodes:")
    #     for node in zero_nodes:
    #         print(node[1])
    # if found_relations is not None:
    #     print("\nFound relations:")
    #     triples = []
    #     for rel in found_relations:
    #         print(
    #             rel[1][-3:],
    #             rel[2],
    #             rel[0],
    #             rel[3][-3:],
    #             rel[4]
    #                     )

def pretty_print_logic_analysis(logic_analysis):
    for i, logic in enumerate(logic_analysis.and_statements, 1):
        print("AND Node: ", logic.statement)
        print("Met conditions: ", logic.met_conditions)
        # for j, met in enumerate(logic.met_conditions, 1):
        #     print("Met condition: ", met.node)
        # for j, unmet in enumerate(logic.unmet_conditions, 1):
        #     print("Unmet condition: ", unmet.node)
        pretty_print_triples(logic.output)

def pretty_print_statements(statements):
    for i, s in enumerate(statements.statement, 1):
        print(f"{i:2d}. Statement Node: {s.statement_node} \n   Subject: {s.subject} \n   Predicate: {s.predicate} \n   Object: {s.object}\n")

def pretty_print_sep_statements(statements):
    for i, s in enumerate(statements.statement, 1):
        print(f"{i:2d}. Statement Node ID: {s.statement_node_ID} \n   Subject: {s.subject} \n   SubjectID: {s.subjectID} \n   Predicate: {s.predicate} \n   PredicateID: {s.predicateID} \n   Object: {s.object}\n   ObjecID: {s.objectID}\n")

def pretty_print_sum_statements(statement):
    for i, s_statement in enumerate(statement.statement, 1):
        print(f"{i:2d}. Statement Node ID: {s_statement.statement_node_ID} \n   Subject: {s_statement.subject} \n   SubjectID: {s_statement.subjectID} \n   Predicate: {s_statement.predicate} \n   PredicateID: {s_statement.predicateID} \n   Object: {s_statement.object}\n   ObjectID: {s_statement.objectID}\n   Summary: {s_statement.summary}\n")

def entities_to_list(entities):
    list = []
    for i, t in enumerate(entities.entities, 1):
        list.append(t.entity)
    return list

def UnReificator(found_relations):
    statements = {}

    for rel in found_relations:
        head_node_id=rel[1][-3:]
        head_node_value=rel[2]
        relation=rel[0]
        tail_node_id=rel[3][-3:]
        tail_node_value=rel[4]
        
        if head_node_value == "rdf:statement":
            if head_node_id not in statements:
                statements[head_node_id] = ["subj", "subjid" , "pred","predid", "obj", "objid"]
            if relation == "rdf:subject":
                statements[head_node_id][0] = tail_node_value
                statements[head_node_id][1] = tail_node_id
            elif relation == "rdf:predicate":
                statements[head_node_id][2] = tail_node_value
                statements[head_node_id][3] = tail_node_id
            elif relation == "rdf:object":
                statements[head_node_id][4] = tail_node_value
                statements[head_node_id][5] = tail_node_id
    list_statements = []
    for key in statements:
        # Create a Statement object for each rdf:statement node
        statement = Statement(
            statement_node= str(key) + " rdf:statement", 
            subject= statements[key][1] +" "+ statements[key][0],
            predicate=statements[key][3] +" "+ statements[key][2],
            object=statements[key][5] +" "+ statements[key][4]
        )
        list_statements.append(statement)
    wrapped = Statements(statement=list_statements)
    return wrapped

def UnReificatorTriples(triples):
    statements = {}
    for i, t in enumerate(triples.triples, 1):
        head_node_id=t.head_node_id
        head_node_value=t.head_node_value
        relation=t.relation
        tail_node_id=t.tail_node_id
        tail_node_value=t.tail_node_value
        
        if head_node_value == "rdf:statement":
            if head_node_id not in statements:
                statements[head_node_id] = ["subj", "subjid" , "pred","predid", "obj", "objid"]
            if relation == "rdf:subject":
                statements[head_node_id][0] = tail_node_value
                statements[head_node_id][1] = tail_node_id
            elif relation == "rdf:predicate":
                statements[head_node_id][2] = tail_node_value
                statements[head_node_id][3] = tail_node_id
            elif relation == "rdf:object":
                statements[head_node_id][4] = tail_node_value
                statements[head_node_id][5] = tail_node_id
    list_statements = []
    for key in statements:
        # Create a Statement object for each rdf:statement node
        statement = StatementSepID(
            statement_node_ID= str(key), 
            subject= statements[key][0],
            subjectID= statements[key][1],
            predicate=statements[key][2],
            predicateID= statements[key][3],
            object=statements[key][4],
            objectID= statements[key][5]
        )
        list_statements.append(statement)
    wrapped = StatementsSepID(statement=list_statements)
    return wrapped

if __name__ == "__main__":
    visited_nodes = set()
    found_relations = set()
    zero_nodes = set()
    #result = GetAllNodes()  # This returns a Triples object
    result = ExactLogicOneHopMultithreaded("angina-health related Status",visited_nodes, found_relations, zero_nodes)
    pretty_print_triples(result[0], result[1], result[2], result[3])
    statements = UnReificator(result[2])
    print(statements)
    pretty_print_statements(statements)

    # Convert triples to dictionary format for JSON
    #output_data = []
    # for triple in result.triples:
    #     output_data.append({
    #         "head_node_id": triple.head_node_id,
    #         "head_node_value": triple.head_node_value,
    #         "relation": triple.relation,
    #         "tail_node_id": triple.tail_node_id,
    #         "tail_node_value": triple.tail_node_value
    #     })

    
    # # Write to JSON file
    # import os
    # output_file = os.path.join(DIR, "triples_output.json")
    
    # with open(output_file, 'w', encoding='utf-8') as f:
    #     json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # print(f"Results written to: {output_file}")


