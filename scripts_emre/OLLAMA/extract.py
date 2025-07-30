from baml_client.sync_client import b  # isort:skip
import os
output_path =  "/prj/doctoral_letters/guide/outputs2/baml_output"
diff_text = "the ORBITA 2 trial demonstrated that patients with stable angina, who were receiving minimal or no antianginal medication and had objective evidence of ischaemia, experienced a lower angina symptom score following PCI treatment compared with a placebo procedure, indicating a better health status with respect to angina."
easy_text = "The CLARIFY registry found that many CCS patients with angina experience a resolution of symptoms over time"
reif_easy_text = "The CLARIFY registry found that many CCS patients with angina experience a resolution of symptoms over time, often without changes in treatment or revascularization"

def main(text):
    response = b.LogicIdentifier(text)
    print(response)

def test(text):
    functions = [b.FormattedFacts, b.A, b.B, b.C, b.D, b.E, b.F, b.G, b.H, b.I, b.J]
    
    # Create output file path
    output_file = os.path.join(output_path, "sentences_output.txt")
    
    with open(output_file, 'w') as f:
        for func in functions:
            f.write(f"\n=== {func.__name__} ===\n")
            response = func(text)
            
            if hasattr(response, 'sentence'):
                for sentence in response.sentence:
                    f.write(f"- {sentence}\n")
            elif isinstance(response, (list, tuple)):
                for item in response:
                    f.write(f"- {item}\n")
            
            f.write("\n")  # Add blank line between functions

if __name__ == "__main__":
    test(easy_text)
