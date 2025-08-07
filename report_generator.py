import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from openpyxl import load_workbook
from datetime import date
import re

# --- Database Connection Setup ---
load_dotenv()

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

def fetch_overtime_data(engine, start_date, end_date):
    """Fetches overtime and employee data for a given date range."""
    query = f"""
    SELECT
        p.matricula_actual, p.nombre_actual, p.categoria, p.horario, p.dias_descanso,
        te.fecha, te.horas, te.motivo_cobertura, p.plaza
    FROM tiempo_extra te
    JOIN plazas p ON te.plaza_id = p.plaza
    WHERE te.fecha BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY p.nombre_actual, te.fecha;
    """
    df = pd.read_sql(query, engine)
    print(f"Found {len(df)} overtime records between {start_date} and {end_date}.")
    return df

def generate_report(data_df, template_path, output_path, plazas_df):
    """Fills the Excel template with grouped and aggregated overtime data."""
    if data_df.empty:
        print("No data to generate report. Exiting.")
        return

    # --- Group data by employee and by the reason for coverage ---
    # This ensures that if an employee covers for two different people,
    # they will get two separate lines in the report.
    grouped_data = data_df.groupby(['matricula_actual', 'motivo_cobertura']).agg(
        fechas=('fecha', list),
        horas_diarias=('horas', 'first'),
        total_horas=('horas', 'sum'),
        num_dias=('fecha', 'count'),
        nombre_actual=('nombre_actual', 'first'),
        categoria=('categoria', 'first'),
        horario=('horario', 'first'),
        dias_descanso=('dias_descanso', 'first')
    ).reset_index()

    try:
        workbook = load_workbook(template_path)
        sheet = workbook.active
    except FileNotFoundError:
        print(f"❌ Error: Template file not found at '{template_path}'")
        return

    sheet['G5'] = date.today().strftime('%d/%m/%Y')
    start_row = 10

    for index, record in grouped_data.iterrows():
        current_row = start_row + index
        
        # 1. MATRICULA
        sheet[f'A{current_row}'] = record['matricula_actual']
        
        # 2. NOMBRE
        sheet[f'B{current_row}'] = f"{record['nombre_actual']}\n{record['categoria']}\nTURNO: {record['horario']}\nMATRICULA: {record['matricula_actual']}\nDESCANSO: {record['dias_descanso']}"
        
        # 3. CATEGORIA Y JORNADA
        sheet[f'C{current_row}'] = record['categoria']
        
        # 4. MOTIVO DE COBERTURA
        motivo = record['motivo_cobertura']
        # Updated regex to handle the display_name format
        match = re.search(r"Cubre a: (.*) \((\d+)\)\. Folio: (.*)", motivo)
        if match:
            covered_worker_name_plaza, covered_worker_plaza_id, folio = match.groups()
            
            covered_worker_details = plazas_df[plazas_df['plaza'] == covered_worker_plaza_id]
            if not covered_worker_details.empty:
                details = covered_worker_details.iloc[0]
                sheet[f'D{current_row}'] = f"{folio} {details['nombre_actual']}\n{details['categoria']}\nMAT: {details['matricula_actual']}\nTURNO: {details['horario']}\nDESCANSO: {details['dias_descanso']}"
            else:
                sheet[f'D{current_row}'] = motivo
        else:
            sheet[f'D{current_row}'] = motivo

        # 5. PERIODO
        periodo_str = " Y ".join([d.strftime('%d') for d in sorted(record['fechas'])])
        if sorted(record['fechas']):
             periodo_str += sorted(record['fechas'])[0].strftime('/%m/%Y')
        sheet[f'E{current_row}'] = periodo_str
        
        # 6. NUM HORAS, DIAS, TOTAL
        sheet[f'F{current_row}'] = record['horas_diarias']
        sheet[f'G{current_row}'] = record['num_dias']
        sheet[f'H{current_row}'] = record['total_horas']

    workbook.save(output_path)
    print(f"✅ Report successfully generated and saved to '{output_path}'")

if __name__ == "__main__":
    report_start_date = "2025-07-01"
    report_end_date = "2025-07-31"

    template_file = "template_tiempo_extra.xlsx"
    output_file = f"Reporte_Tiempo_Extra_{report_start_date}_a_{report_end_date}.xlsx"

    try:
        print("Connecting to the database...")
        db_engine = get_database_engine()
        all_plazas_df = pd.read_sql("SELECT * FROM plazas", db_engine)
        overtime_df = fetch_overtime_data(db_engine, report_start_date, report_end_date)
        generate_report(overtime_df, template_file, output_file, all_plazas_df)
    except Exception as e:
        print(f"An error occurred: {e}")
