from baml_client.sync_client import b  # isort:skip
import os
output_path =  "/prj/doctoral_letters/guide/outputs2/baml_output"
paragraph = "The CLARIFY registry found that many CCS patients with angina experience a resolution of symptoms over time"
medium_text = "The CLARIFY registry found that many CCS patients with angina experience a resolution of symptoms over time, often without changes in treatment or revascularization"
diff_text = "the ORBITA 2 trial demonstrated that patients with stable angina, who were receiving minimal or no antianginal medication and had objective evidence of ischaemia, experienced a lower angina symptom score following PCI treatment compared with a placebo procedure, indicating a better health status with respect to angina."

def test(text):
    b.FormattedFacts
    
    # Create output file path
    output_file = os.path.join(output_path, "sentences_output.txt")
    
    with open(output_file, 'w') as f:
            f.write("\n=== Formatted Text ===\n")
            response = b.FormattedFacts(text)
            b.GraphConstructor(text)
            
            if hasattr(response, 'sentence'):
                for sentence in response.sentence:
                    f.write(f"- {sentence}\n")
            elif isinstance(response, (list, tuple)):
                for item in response:
                    f.write(f"- {item}\n")
            
            f.write("\n")  # Add blank line between functions
def main(text):
    response = b.EasyFormatting(text)
    nested = b.PrototypeNester(sentences=response, original=text)
    triples = b.Hypergrapher(nested)
    print(triples)

if __name__ == "__main__":
    main(medium_text)
