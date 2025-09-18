from database import create_tables, engine
from sqlalchemy import inspect

def verify_schema():
    create_tables()
    inspector = inspect(engine)
    
    print("Tables in database:")
    for table_name in inspector.get_table_names():
        print(f"\nTable: {table_name}")
        for column in inspector.get_columns(table_name):
            print(f"  Column: {column['name']}")
            print(f"    Type: {column['type']}")
            print(f"    Nullable: {column['nullable']}")

if __name__ == "__main__":
    verify_schema()