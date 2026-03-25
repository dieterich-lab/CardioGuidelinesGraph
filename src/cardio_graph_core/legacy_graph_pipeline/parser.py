import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "--dev",
    action="store_true",
)
parser.add_argument(
    "--model", choices=["nemo", "8x22b", "8x7b", "v03", "large", "70b"], default="nemo"
)
parser.add_argument("--port", type=int, choices=[34, 35, 36], default=34)
parser.add_argument("--gpu", type=str, choices=["g2", "g3", "g4", "g5"], default="g4")
args = parser.parse_args()
