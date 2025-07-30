from neo4j import GraphDatabase
import json
# Database configuration
URI = "bolt://neo4j-dev2.internal:7687"
AUTH = ("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj")
DIR = "/prj/doctoral_letters/guide/outputs2/test_query"

class Triple:
    def __init__(self, head_node_id, head_node_value, relation, tail_node_id, tail_node_value):
        self.head_node_id = head_node_id
        self.head_node_value = head_node_value
        self.relation = relation
        self.tail_node_id = tail_node_id
        self.tail_node_value = tail_node_value

    def to_dict(self):
        return {
            "head_node_id": self.head_node_id,
            "head_node_value": self.head_node_value,
            "relation": self.relation,
            "tail_node_id": self.tail_node_id,
            "tail_node_value": self.tail_node_value
        }
    def __repr__(self):
        return f"{self.head_node_id} / {self.head_node_value} -- {self.relation} --> {self.tail_node_id} / {self.tail_node_value}"


def LogicIdentifier(node, session, zero_nodes):
 
    # if node is an AND node, find all the next neighbors
    if "AND" in node.labels:
        print("\nAND node found, processing...")
        #query for all relationships of the node
        query = f"""
        MATCH (n) 
        WHERE elementId(n) = "{node.element_id}"
        MATCH p = (n)--(next_neighbor)
        RETURN p
        """
        result = session.run(query)
        #create a set to store the met and unmet conditions
        met_conditions = set()
        unmet_conditions = set()
        output_set = set()
        for record in result:
            for relationship in record["p"].relationships:
                #get the head and tail of each relationship
                head_tuple = (relationship.start_node.element_id, relationship.start_node.get("value"))
                tail_tuple = (relationship.end_node.element_id, relationship.end_node.get("value"))
                # print("head id:...", head_tuple)
                # print("tail id:...", tail_tuple)
                if head_tuple == (node.element_id, node.get("value")):
                    output_set.add((head_tuple,relationship.type,tail_tuple))
                    # print("\nDOWNSTREAM")
                    # print(node.element_id)
                    # print("Relationship:", relationship.type)

                #if the AND node is the tail of the relationship    
                if tail_tuple == (node.element_id, node.get("value")):
                    if relationship.type == "rdf:subject":
                        output_set.add((head_tuple,relationship.type,tail_tuple))
                    # print("\nUPSTREAM")
                    # print(node.element_id)
                    # print("Relationship:", relationship.type)

                    # check if the relationship type is "part of" which makes it a condition for the AND statement
                    if relationship.type == "part of":
                        if head_tuple in zero_nodes:
                            met_conditions.add(head_tuple)
                        else:
                            unmet_conditions.add(head_tuple)
        print("\nConditional Analysis of AND node:", node.get("value"))
        print("Met conditions:", met_conditions)
        if not unmet_conditions:
            print("All conditions met for this AND node.")
        else: 
            print("missing conditions for this AND node:", unmet_conditions)
        print("\nOutput set:", output_set)



def RecursiveHop(neighbor, session, visited_nodes, zero_nodes,found_relations):
    # Call LogicIdentifier for this node to check if the AND conditions are met
    LogicIdentifier(neighbor, session, zero_nodes)
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
                RecursiveHop(second_record["next_neighbor"], session, visited_nodes, zero_nodes, found_relations)


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
                return triples
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

if __name__ == "__main__":
    print(*RelationLogicOneHop("angina-health"), sep="\n")

