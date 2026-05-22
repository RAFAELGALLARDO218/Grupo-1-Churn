# app/db.py
# ============================================================
# CONEXIÓN Y CONSULTAS A BASE DE DATOS - CHURN
# ============================================================

from dotenv import load_dotenv
import os
import psycopg
from psycopg.rows import dict_row

load_dotenv()

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

def test_connection():
    """Prueba la conexión a la base de datos"""
    params = get_connection_params()
    missing = [k for k, v in params.items() if k != "sslmode" and not v]
    if missing:
        return {"status": "error", "detail": "Faltan variables: " + ", ".join(missing)}

    try:
        with psycopg.connect(**params) as conn:
            with conn.cursor() as cur:
                cur.execute("select version();")
                version = cur.fetchone()[0]
        return {"status": "ok", "detail": "Conexion exitosa", "db_version": version}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# ============================================================
# CONSULTAS PARA CHURN
# ============================================================

def get_churn_data(limit: int = 20):
    """
    Obtiene registros de la tabla churn_clientes
    
    Parámetros:
        limit: Número máximo de registros a retornar
    """
    params = get_connection_params()
    missing = [k for k, v in params.items() if k != "sslmode" and not v]
    if missing:
        raise ValueError("Faltan variables: " + ", ".join(missing))

    query = '''
    SELECT 
        id,
        customer_id,
        gender,
        senior_citizen,
        partner,
        dependents,
        tenure,
        phone_service,
        multiple_lines,
        internet_service,
        online_security,
        online_backup,
        device_protection,
        tech_support,
        streaming_tv,
        streaming_movies,
        contract,
        paperless_billing,
        payment_method,
        monthly_charges,
        total_charges,
        churn,
        created_at
    FROM public.churn_clientes
    ORDER BY id
    LIMIT %s;
    '''

    with psycopg.connect(**params) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (limit,))
            rows = cur.fetchall()
            columns = [desc.name for desc in cur.description]

    results = []
    for row in rows:
        item = {}
        for col, value in zip(columns, row):
            if hasattr(value, "isoformat"):
                item[col] = value.isoformat()
            else:
                item[col] = value
        results.append(item)

    return results

def get_churn_statistics():
    """
    Calcula estadísticas básicas de churn_clientes
    """
    params = get_connection_params()
    missing = [k for k, v in params.items() if k != "sslmode" and not v]
    if missing:
        raise ValueError("Faltan variables: " + ", ".join(missing))

    # Resumen general
    summary_query = '''
    SELECT 
        COUNT(*) as total_clientes,
        SUM(churn) as clientes_churn,
        ROUND(AVG(churn) * 100, 2) as tasa_churn_porcentaje,
        ROUND(AVG(tenure), 2) as tenencia_promedio_meses,
        ROUND(AVG(monthly_charges), 2) as cargo_mensual_promedio,
        ROUND(AVG(total_charges), 2) as cargo_total_promedio
    FROM public.churn_clientes;
    '''

    # Churn por género
    gender_query = '''
    SELECT 
        gender, 
        COUNT(*) as total,
        SUM(churn) as churn_count,
        ROUND(AVG(churn) * 100, 2) as churn_rate
    FROM public.churn_clientes
    GROUP BY gender
    ORDER BY churn_rate DESC;
    '''

    # Churn por tipo de contrato
    contract_query = '''
    SELECT 
        contract, 
        COUNT(*) as total,
        SUM(churn) as churn_count,
        ROUND(AVG(churn) * 100, 2) as churn_rate
    FROM public.churn_clientes
    GROUP BY contract
    ORDER BY churn_rate DESC;
    '''

    # Churn por tipo de internet
    internet_query = '''
    SELECT 
        internet_service, 
        COUNT(*) as total,
        SUM(churn) as churn_count,
        ROUND(AVG(churn) * 100, 2) as churn_rate
    FROM public.churn_clientes
    GROUP BY internet_service
    ORDER BY churn_rate DESC;
    '''

    with psycopg.connect(**params) as conn:
        with conn.cursor() as cur:
            # Resumen general
            cur.execute(summary_query)
            summary = cur.fetchone()
            
            # Por género
            cur.execute(gender_query)
            gender_rows = cur.fetchall()
            
            # Por contrato
            cur.execute(contract_query)
            contract_rows = cur.fetchall()
            
            # Por internet
            cur.execute(internet_query)
            internet_rows = cur.fetchall()

    return {
        "resumen": {
            "total_clientes": int(summary[0]) if summary[0] else 0,
            "clientes_churn": int(summary[1]) if summary[1] else 0,
            "clientes_no_churn": int(summary[0] - summary[1]) if summary[0] and summary[1] else 0,
            "tasa_churn_porcentaje": float(summary[2]) if summary[2] else 0.0,
            "tenencia_promedio_meses": float(summary[3]) if summary[3] else 0.0,
            "cargo_mensual_promedio": float(summary[4]) if summary[4] else 0.0,
            "cargo_total_promedio": float(summary[5]) if summary[5] else 0.0,
        },
        "por_genero": [
            {
                "genero": row[0], 
                "total": int(row[1]),
                "churn_count": int(row[2]),
                "churn_rate": float(row[3])
            } 
            for row in gender_rows
        ],
        "por_contrato": [
            {
                "contrato": row[0], 
                "total": int(row[1]),
                "churn_count": int(row[2]),
                "churn_rate": float(row[3])
            } 
            for row in contract_rows
        ],
        "por_internet": [
            {
                "internet_service": row[0], 
                "total": int(row[1]),
                "churn_count": int(row[2]),
                "churn_rate": float(row[3])
            } 
            for row in internet_rows
        ]
    }