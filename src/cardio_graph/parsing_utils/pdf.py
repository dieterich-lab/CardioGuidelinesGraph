from pypdf import PdfReader, PdfWriter
import os

reader = PdfReader("/beegfs/prj/doctoral_letters/guide/data/pdf/esc/esc_ccs.pdf")

output_folder = "/beegfs/prj/doctoral_letters/guide/data/pdf/esc/esc_pages"

os.makedirs(output_folder, exist_ok=True)

pages_to_extract = list(range(69-15, 77-14)) # pages 69-77

for page_number in pages_to_extract:
    writer = PdfWriter()
    writer.add_page(reader.pages[page_number])
    
    output_path = os.path.join(output_folder, f"page_{page_number + 15}.pdf")
    with open(output_path, "wb") as out_file:
        writer.write(out_file)

print("done")
