neighbor = {
    "id": 123,
    "value": "CHEF",
    "labels": "Node"
}
print(f"""
        MATCH (n:Node{{id:"{neighbor.get("id")}"}})--(next_neighbor)
        WHERE ID(n) = $chef_id
        RETURN next_neighbor
        """)