import json

from unstructured_client import UnstructuredClient
from unstructured_client.models import operations, shared

# Update here with your api key and server url
client = UnstructuredClient(
    api_key_auth="2T2v2KfBEUOex0PinVjbLyLADgQfkJ",
    server_url="https://api.unstructuredapp.io/general/v0/general",
)

# Update here with your filename
filename = "/beegfs/prj/LINDA_LLM/PubMed_Resources/Papers_Human_Cardiac_Alternative_Splicing/pdf_separate/10.1002_emmm.201202168.pdf"

with open(filename, "rb") as f:
    files = shared.Files(
        content=f.read(),
        file_name=filename,
    )

# You can choose FAST, HI_RES or OCR_ONLY for strategy, learn more in the docs at step 4
req = operations.PartitionRequest(
    shared.PartitionParameters(files=files, strategy=shared.Strategy.AUTO)
)

try:
    resp = client.general.partition(req)
    print(json.dumps(resp.elements, indent=2))
except Exception as e:
    print(e)
