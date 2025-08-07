import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect, Table, Column, String
from sqlalchemy.schema import MetaData

# --- FIX: Reverted to using .env file for security ---
# This ensures your password is not stored in the code.
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

def get_database_engine():
    """Connects to the Cloud SQL database and returns an engine object."""
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")

    if not all([db_user, db_password, db_host, db_port, db_name]):
        raise ValueError("❌ Error: Missing database credentials in .env file.")

    database_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return create_engine(database_url)

def clean_data(df):
    """Cleans the DataFrame extracted from the XLSX file."""
    df.columns = [
        'nombre_completo', 'matricula', 'dias_descanso', 'horario',
        'plaza', 'categoria'
    ]
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    df.dropna(subset=['plaza'], inplace=True)
    df['plaza'] = df['plaza'].astype(str).str.replace('.0', '', regex=False)
    df.drop_duplicates(subset=['plaza'], keep='first', inplace=True)
    final_df = df[['plaza', 'categoria', 'horario', 'dias_descanso', 'matricula', 'nombre_completo']].copy()
    final_df.rename(columns={
        'matricula': 'matricula_actual',
        'nombre_completo': 'nombre_actual'
    }, inplace=True)
    print("✅ Data cleaned successfully from XLSX file.")
    return final_df

def main():
    """
    Main function to extract, clean, and load employee data
    from an XLSX file to a PostgreSQL database.
    """
    try:
        engine = get_database_engine()
        xlsx_path = "plantillajulio2025.xlsx"
        if not os.path.exists(xlsx_path):
            print(f"❌ Error: XLSX file not found at '{xlsx_path}'")
            return

        print(f"Reading data from '{xlsx_path}'...")
        employee_df = pd.read_excel(xlsx_path)
        print(f"Found {len(employee_df)} initial records in the XLSX file.")
        
        cleaned_df = clean_data(employee_df)

        with engine.connect() as connection:
            print("Connecting to database...")
            table_name = 'plazas'
            print(f"Table '{table_name}' exists. Overwriting all data...")
            connection.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;"))
            
            print("Loading new, clean data into the database...")
            cleaned_df.to_sql(table_name, connection, if_exists='append', index=False)
            print("🎉 Success! All records in the 'plazas' table have been replaced with the clean data.")

    except Exception as e:
        print(f"❌ An error occurred during the database operation: {e}")

if __name__ == "__main__":
    main()
