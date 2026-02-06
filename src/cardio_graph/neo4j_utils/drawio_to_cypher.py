import xml.etree.ElementTree as ET
import os
from html.parser import HTMLParser

# Set your input and output folders manually here
INPUT_FOLDER = '/prj/doctoral_letters/guide/data2/drawio'
OUTPUT_FOLDER = '/prj/doctoral_letters/guide/outputs2/cypher'


class HTMLCleaner(HTMLParser):
    """A simple HTML parser to extract text content from HTML-like strings."""
    def __init__(self):
        super().__init__()
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def clean(self, html):
        self.text = []
        self.feed(html)
        return ''.join(self.text).strip()


def parse_and_write_cells(file_path, output_file):
    print(f"Parsing file: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        xml_content = f.read()

    try:
        root = ET.fromstring(xml_content)
        diagram = root.find('diagram')
        if diagram is None:
            print(f"Error: No <diagram> tag found in {file_path}.")
            return

        # Check if diagram has child elements
        if len(diagram) > 0:
            diagram_root = diagram
        else:
            diagram_root = ET.fromstring(diagram.text.strip())

        graph_model = diagram_root.find('mxGraphModel')
        if graph_model is None:
            print(f"Error: No <mxGraphModel> tag found in {file_path}.")
            return

        graph_root = graph_model.find('root')
        if graph_root is None:
            print(f"Error: No <root> tag found in {file_path}.")
            return

    except ET.ParseError as e:
        print(f"Error parsing XML content: {e}")
        return

    nodes = {}
    edges = {}
    edge_labels = {}
    html_cleaner = HTMLCleaner()

    # Parse all mxCells
    for cell in graph_root.findall('mxCell'):
        cell_id = cell.attrib.get('id')
        value = cell.attrib.get('value', '').strip()
        value = html_cleaner.clean(value)  # Clean HTML-like content
        source = cell.attrib.get('source')
        target = cell.attrib.get('target')
        edge = cell.attrib.get('edge')
        vertex = cell.attrib.get('vertex')
        parent = cell.attrib.get('parent')
        style = cell.attrib.get('style', '')

        if vertex == '1' and parent == '1':  # It's a node
            nodes[cell_id] = value
        elif edge == '1':  # It's an edge
            edges[cell_id] = {
                'id': cell_id,
                'value': value,  # Direct edge value
                'source': source,
                'target': target
            }
        elif 'edgeLabel' in style:  # It's an edge label
            edge_labels[cell_id] = {
                'value': value,
                'parent': parent
            }

    # Overwrite edge values with edge label values if applicable
    for label_id, label_data in edge_labels.items():
        parent_id = label_data['parent']
        if parent_id in edges:
            edges[parent_id]['value'] = label_data['value']

    # Write Cypher statements to the output file
    for node_id, node_value in nodes.items():
        sanitized_id = node_id.replace("-", "")  # Remove all '-' from the ID
        
        # Handle special nType::AND case
        if "nType::AND" in node_value:
            # Remove nType::AND from value and add as label
            safe_value = node_value.replace("nType::AND", "").strip()
            safe_value = safe_value.replace("'", "\\'")  # Escape single quotes
            output_file.write(f"MERGE (n{sanitized_id}:Node:AND {{id: '{sanitized_id}', value: '{safe_value}'}})\n")
        else:
            safe_value = node_value.replace("'", "\\'")  # Escape single quotes
            output_file.write(f"MERGE (n{sanitized_id}:Node {{id: '{sanitized_id}', value: '{safe_value}'}})\n")

    for edge in edges.values():
        sanitized_source = edge['source'].replace("-", "") if edge['source'] else None
        sanitized_target = edge['target'].replace("-", "") if edge['target'] else None
        safe_value = edge['value'].replace("'", "\\'")  # Escape single quotes
        output_file.write(
            f"MERGE (n{sanitized_source})-[:`{safe_value}`]->(n{sanitized_target})\n"
        )

    print(f"Cypher statements written to {output_file.name}")


def write_raw_content(file_path, output_path):
    """Writes all content from nodes and edges without formatting."""
    print(f"Parsing file for raw content: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        xml_content = f.read()

    try:
        root = ET.fromstring(xml_content)
        diagram = root.find('diagram')
        if diagram is None:
            return

        if len(diagram) > 0:
            diagram_root = diagram
        else:
            diagram_root = ET.fromstring(diagram.text.strip())

        graph_model = diagram_root.find('mxGraphModel')
        if graph_model is None:
            return

        graph_root = graph_model.find('root')
        if graph_root is None:
            return

        html_cleaner = HTMLCleaner()
        content = []

        # Extract all values from mxCells
        for cell in graph_root.findall('mxCell'):
            value = cell.attrib.get('value', '').strip()
            if value:  # Only include non-empty values
                cleaned_value = html_cleaner.clean(value)
                content.append(cleaned_value)

        # Write raw content to file
        raw_output_path = output_path.replace('_cypher.txt', '_raw.txt')
        with open(raw_output_path, 'w', encoding='utf-8') as f:
            f.write(' '.join(content))

    except ET.ParseError as e:
        print(f"Error parsing XML content for raw output: {e}")
        return


def process_folder(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Create consolidated output file for all Cypher statements
    consolidated_output = os.path.join(output_folder, 'consolidated_cypher.txt')
    
    with open(consolidated_output, 'w', encoding='utf-8') as consolidated_file:
        for filename in os.listdir(input_folder):
            if filename.endswith('.drawio') or filename.endswith('.xml'):
                input_path = os.path.join(input_folder, filename)
                output_filename = os.path.splitext(filename)[0] + '_cypher.txt'
                output_path = os.path.join(output_folder, output_filename)

                print(f"Processing file: {filename}")
                
                try:
                    # Create individual Cypher file
                    with open(output_path, 'w', encoding='utf-8') as individual_file:
                        parse_and_write_cells(input_path, individual_file)
                    
                    # Append content to consolidated file
                    with open(output_path, 'r', encoding='utf-8') as individual_file:
                        consolidated_file.write(individual_file.read())
                        consolidated_file.write("\n")  # Add spacing between files
                        
                except ET.ParseError as e:
                    print(f"Error parsing {filename}: {e}")
                    continue

    print(f"All Cypher statements consolidated in: {consolidated_output}")


def main():
    if not os.path.exists(INPUT_FOLDER):
        print(f"Error: Input folder '{INPUT_FOLDER}' does not exist.")
        return
    if not os.path.exists(OUTPUT_FOLDER):
        print(f"Creating output folder '{OUTPUT_FOLDER}'.")
        os.makedirs(OUTPUT_FOLDER)

    process_folder(INPUT_FOLDER, OUTPUT_FOLDER)


if __name__ == '__main__':
    main()