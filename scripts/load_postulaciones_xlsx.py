from dotenv import load_dotenv
import os
import pandas as pd
import psycopg

load_dotenv()

EXCEL_PATH = "data/postulaciones.xlsx"
SHEET_NAME = "Postulaciones"

EXPECTED_COLUMNS = [
    "CEDULA",
    "PERIODO",
    "SEXO",
    "PREFERENCIA",
    "CARRERA",
    "MATRICULADO",
    "FACULTAD",
    "PUNTAJE",
    "GRUPO_DEPEN",
    "REGION",
    "LATITUD",
    "LONGITUD",
    "PTJE_NEM",
    "PSU_PROMLM",
    "PACE",
    "GRATUIDAD",
]

def get_connection_params():
    return {
        "host": os.getenv("SUPABASE_DB_HOST"),
        "port": os.getenv("SUPABASE_DB_PORT", "5432"),
        "dbname": os.getenv("SUPABASE_DB_NAME", "postgres"),
        "user": os.getenv("SUPABASE_DB_USER"),
        "password": os.getenv("SUPABASE_DB_PASSWORD"),
        "sslmode": "require",
    }

def validate_env():
    params = get_connection_params()
    missing = [k for k, v in params.items() if k != "sslmode" and not v]
    if missing:
        raise ValueError("Faltan variables de entorno: " + ", ".join(missing))
    return params

def load_dataframe():
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
    df.columns = [str(c).strip().upper() for c in df.columns]

    missing_cols = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError("Faltan columnas en el Excel: " + ", ".join(missing_cols))

    df = df[EXPECTED_COLUMNS].copy()

    numeric_columns = [
        "CEDULA", "PERIODO", "PREFERENCIA", "PUNTAJE",
        "LATITUD", "LONGITUD", "PTJE_NEM", "PSU_PROMLM"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

def clear_table(conn):
    with conn.cursor() as cur:
        cur.execute("truncate table public.postulaciones_demo restart identity;")

def insert_rows(conn, df):
    sql = '''
    insert into public.postulaciones_demo (
        cedula, periodo, sexo, preferencia, carrera, matriculado, facultad,
        puntaje, grupo_depen, region, latitud, longitud, ptje_nem,
        psu_promlm, pace, gratuidad
    ) values (
        %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s,
        %s, %s, %s
    )
    '''

    rows = []
    for _, row in df.iterrows():
        rows.append((
            None if pd.isna(row["CEDULA"]) else int(row["CEDULA"]),
            None if pd.isna(row["PERIODO"]) else int(row["PERIODO"]),
            None if pd.isna(row["SEXO"]) else str(row["SEXO"]),
            None if pd.isna(row["PREFERENCIA"]) else int(row["PREFERENCIA"]),
            None if pd.isna(row["CARRERA"]) else str(row["CARRERA"]),
            None if pd.isna(row["MATRICULADO"]) else str(row["MATRICULADO"]),
            None if pd.isna(row["FACULTAD"]) else str(row["FACULTAD"]),
            None if pd.isna(row["PUNTAJE"]) else int(row["PUNTAJE"]),
            None if pd.isna(row["GRUPO_DEPEN"]) else str(row["GRUPO_DEPEN"]),
            None if pd.isna(row["REGION"]) else str(row["REGION"]),
            None if pd.isna(row["LATITUD"]) else float(row["LATITUD"]),
            None if pd.isna(row["LONGITUD"]) else float(row["LONGITUD"]),
            None if pd.isna(row["PTJE_NEM"]) else int(row["PTJE_NEM"]),
            None if pd.isna(row["PSU_PROMLM"]) else int(row["PSU_PROMLM"]),
            None if pd.isna(row["PACE"]) else str(row["PACE"]),
            None if pd.isna(row["GRATUIDAD"]) else str(row["GRATUIDAD"]),
        ))

    with conn.cursor() as cur:
        cur.executemany(sql, rows)

def main():
    params = validate_env()
    df = load_dataframe()

    print(f"Filas leidas desde Excel: {len(df)}")

    with psycopg.connect(**params) as conn:
        clear_table(conn)
        insert_rows(conn, df)
        conn.commit()

    print("Carga completada correctamente en public.postulaciones_demo")

if __name__ == "__main__":
    main()
