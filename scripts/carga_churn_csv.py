# scripts/carga_churn_xlsx.py
# ============================================================
# CARGA A SUPABASE - Churn Dataset
# ============================================================
# Lee el archivo Excel validado/limpio y lo carga a Supabase
# ============================================================

import os
import pandas as pd
import psycopg
from psycopg import sql
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIGURACIÓN
# ============================================================


EXCEL_PATH = Path("data/Telco-Customer-Churn_validado.xlsx")
SHEET_NAME = "Sheet1"
TABLE_NAME = "public.churn_clientes"

# Modo destructivo:
# True  -> elimina la tabla destino, la vuelve a crear según la estructura del Excel e inserta los datos.
# False -> conserva la tabla actual y solo controla si se limpian o agregan registros.
DROP_AND_RECREATE_TABLE = True

# Solo se usa cuando DROP_AND_RECREATE_TABLE = False.
# True  -> borra los registros actuales con TRUNCATE antes de insertar.
# False -> agrega los datos al final de la tabla existente.
CLEAR_BEFORE_INSERT = False

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def get_connection_params():
    """Obtiene los parámetros de conexión desde variables de entorno"""
    return {
        "host": os.getenv("SUPABASE_DB_HOST"),
        "port": os.getenv("SUPABASE_DB_PORT", "5432"),
        "dbname": os.getenv("SUPABASE_DB_NAME", "postgres"),
        "user": os.getenv("SUPABASE_DB_USER"),
        "password": os.getenv("SUPABASE_DB_PASSWORD"),
        "sslmode": "require",
    }

def validate_env():
    """Valida que existan las variables de entorno requeridas"""
    params = get_connection_params()
    missing = [key for key, value in params.items() if key != "sslmode" and not value]

    if missing:
        raise ValueError("Faltan variables de entorno: " + ", ".join(missing))

    return params

def table_identifier(table_name):
    """Convierte un nombre de tabla tipo 'schema.tabla' en un identificador SQL seguro"""
    return sql.Identifier(*table_name.split("."))

def column_identifiers(columns):
    """Convierte la lista de columnas en identificadores SQL seguros"""
    return sql.SQL(", ").join(sql.Identifier(str(column)) for column in columns)

def infer_postgres_type(series):
    """Infere un tipo PostgreSQL básico a partir del tipo de dato detectado por pandas"""
    dtype = series.dtype

    if pd.api.types.is_integer_dtype(dtype):
        return "BIGINT"
    if pd.api.types.is_float_dtype(dtype):
        return "DOUBLE PRECISION"
    if pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"

    return "TEXT"

# ============================================================
# FUNCIONES DE BASE DE DATOS
# ============================================================

def load_dataframe():
    """Lee el archivo Excel limpio"""
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(f"No se encontró el archivo {EXCEL_PATH}")
    
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
    print(f" Archivo leído: {len(df)} filas, {len(df.columns)} columnas")
    return df

def clear_table(conn):
    """Elimina todos los registros de la tabla destino y reinicia el identificador"""
    query = sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY;").format(
        table_identifier(TABLE_NAME)
    )
    with conn.cursor() as cur:
        cur.execute(query)
    print(f" Tabla {TABLE_NAME} limpiada (TRUNCATE)")

def drop_table(conn):
    """Elimina la tabla destino si existe"""
    query = sql.SQL("DROP TABLE IF EXISTS {};").format(
        table_identifier(TABLE_NAME)
    )
    with conn.cursor() as cur:
        cur.execute(query)
    print(f" Tabla {TABLE_NAME} eliminada")

def create_table_from_dataframe(conn, df):
    """Crea la tabla destino usando las columnas y tipos detectados desde el DataFrame"""
    if df.empty:
        raise ValueError("No se puede crear la tabla porque el DataFrame está vacío")

    column_definitions = []
    for column in df.columns:
        pg_type = infer_postgres_type(df[column])
        column_definitions.append(
            sql.SQL("{} {}").format(
                sql.Identifier(str(column)),
                sql.SQL(pg_type)
            )
        )

    query = sql.SQL("CREATE TABLE {} ({});").format(
        table_identifier(TABLE_NAME),
        sql.SQL(", ").join(column_definitions)
    )

    with conn.cursor() as cur:
        cur.execute(query)
    
    print(f" Tabla {TABLE_NAME} creada con {len(df.columns)} columnas")

def insert_dataframe(conn, df):
    """Inserta un DataFrame en la tabla destino"""
    columns = list(df.columns)
    placeholders = sql.SQL(", ").join(sql.Placeholder() for _ in columns)

    query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        table_identifier(TABLE_NAME),
        column_identifiers(columns),
        placeholders,
    )

    rows = list(df.itertuples(index=False, name=None))

    with conn.cursor() as cur:
        cur.executemany(query, rows)
    
    return len(rows)

def verify_row_count(conn):
    """Verifica cuántos registros hay en la tabla"""
    query = sql.SQL("SELECT COUNT(*) FROM {};").format(
        table_identifier(TABLE_NAME)
    )
    with conn.cursor() as cur:
        cur.execute(query)
        total_rows = cur.fetchone()[0]
    
    print(f" Registros en tabla {TABLE_NAME}: {total_rows}")
    return total_rows

# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def cargar_a_supabase():
    """
    Ejecuta el proceso completo de carga a Supabase.
    
    Retorna:
        int: Número de filas insertadas
    """
    print("=" * 60)
    print(" INICIO DE CARGA A SUPABASE")
    print("=" * 60)
    
    # 1. Validar variables de entorno
    print("\n Validando variables de entorno...")
    params = validate_env()
    print(" Variables de entorno OK")
    
    # 2. Leer archivo Excel
    print(f"\n Leyendo archivo: {EXCEL_PATH}")
    df = load_dataframe()
    
    # 3. Conectar y cargar
    with psycopg.connect(**params) as conn:
        print("\n Conexión a Supabase establecida")
        
        if DROP_AND_RECREATE_TABLE:
            print(f"\n Modo: Recrear tabla {TABLE_NAME}")
            drop_table(conn)
            create_table_from_dataframe(conn, df)
        elif CLEAR_BEFORE_INSERT:
            print(f"\n Modo: Limpiar tabla {TABLE_NAME}")
            clear_table(conn)
        else:
            print(f"\n Modo: Carga incremental")
        
        print(f"\n📥 Insertando datos...")
        inserted_rows = insert_dataframe(conn, df)
        
        conn.commit()
        print(f" {inserted_rows} filas insertadas correctamente")
        
        # Verificar
        total_rows = verify_row_count(conn)
    
    print("\n" + "=" * 60)
    print(" CARGA COMPLETADA EXITOSAMENTE")
    print("=" * 60)
    
    return inserted_rows

# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    cargar_a_supabase()