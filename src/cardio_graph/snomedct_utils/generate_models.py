import os

from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.declarative import declarative_base

# Database connection string (edit as needed)
DB_URL = "mysql+pymysql://test_user:medicaldatabase@10.250.135.23:3306/snomedct"
OUTPUT_FILE = "src/cardio_graph/snomedct_utils/models.py"

engine = create_engine(DB_URL)
metadata = MetaData()
metadata.reflect(bind=engine)
Base = declarative_base()


def render_column(col):
    args = []
    if col.primary_key:
        args.append("primary_key=True")
    if not col.nullable:
        args.append("nullable=False")
    if col.default is not None:
        args.append(f"default={col.default.arg!r}")
    return f"    {col.name} = Column({repr(col.type)}, {', '.join(args)})"


with open(OUTPUT_FILE, "w") as f:
    f.write("from sqlalchemy.ext.declarative import declarative_base\n")
    f.write(
        "from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, Text\n"
    )
    f.write("Base = declarative_base()\n\n")
    for table_name, table in metadata.tables.items():
        class_name = "".join([w.capitalize() for w in table_name.split("_")])
        f.write(f"class {class_name}(Base):\n")
        f.write(f"    __tablename__ = '{table_name}'\n")
        for col in table.columns:
            f.write(render_column(col) + "\n")
        f.write("\n")

print(f"Models written to {OUTPUT_FILE}")
