import os
import subprocess

from marker import settings
from marker.convert import convert_single_pdf
from marker.models import load_all_models

path = "/home/pwiesenbach/guide/data/herzinsuffizienz.pdf"
# path = "/home/pwiesenbach/guide/data/Seite14.pdf"

output = f"/home/pwiesenbach/guide/data/marker/herzinsuffizienz.md"
# output = f"/home/pwiesenbach/guide/data/marker/Seite14.md"

print(path)

model_lst = load_all_models()
full_text, images, out_meta = convert_single_pdf(path, model_lst)

with open(output, "w") as f:
    f.write(full_text)

# os.environ["PAGINATE_OUTPUT"] = "1"
# os.environ["EXTRACT_IMAGES "] = "0"
# result = subprocess.call(
#     [
#         "marker",
#         path,
#         output,
#         "--workers",
#         "4",
#         "--min_length",
#         "1000",
#     ],
# )

print("Finished.")
