from dotenv import load_dotenv
import os
import psycopg

load_dotenv()

def get_connection_params():
    return {
        "host": os.getenv("SUPABASE_DB_HOST"),
        "port": os.getenv("SUPABASE_DB_PORT", "5432"),
        "dbname": os.getenv("SUPABASE_DB_NAME", "postgres"),
        "user": os.getenv("SUPABASE_DB_USER"),
        "password": os.getenv("SUPABASE_DB_PASSWORD"),
        "sslmode": "require",
    }

def test_connection():
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

def get_postulaciones(limit: int = 20):
    params = get_connection_params()
    missing = [k for k, v in params.items() if k != "sslmode" and not v]
    if missing:
        raise ValueError("Faltan variables: " + ", ".join(missing))

    query = '''
    select
        id,
        cedula,
        periodo,
        sexo,
        preferencia,
        carrera,
        matriculado,
        facultad,
        puntaje,
        grupo_depen,
        region,
        latitud,
        longitud,
        ptje_nem,
        psu_promlm,
        pace,
        gratuidad,
        created_at
    from public.postulaciones_demo
    order by id
    limit %s;
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

def get_postulaciones_stats():
    params = get_connection_params()
    missing = [k for k, v in params.items() if k != "sslmode" and not v]
    if missing:
        raise ValueError("Faltan variables: " + ", ".join(missing))

    summary_query = '''
    select
        count(*) as total_postulaciones,
        round(avg(puntaje)::numeric, 2) as promedio_puntaje,
        round(avg(ptje_nem)::numeric, 2) as promedio_ptje_nem,
        round(avg(psu_promlm)::numeric, 2) as promedio_psu_promlm
    from public.postulaciones_demo;
    '''

    sexo_query = '''
    select sexo, count(*) as total
    from public.postulaciones_demo
    group by sexo
    order by total desc, sexo;
    '''

    region_query = '''
    select region, count(*) as total
    from public.postulaciones_demo
    group by region
    order by total desc, region
    limit 10;
    '''

    carrera_query = '''
    select carrera, count(*) as total
    from public.postulaciones_demo
    group by carrera
    order by total desc, carrera
    limit 10;
    '''

    with psycopg.connect(**params) as conn:
        with conn.cursor() as cur:
            cur.execute(summary_query)
            summary_row = cur.fetchone()

            cur.execute(sexo_query)
            sexo_rows = cur.fetchall()

            cur.execute(region_query)
            region_rows = cur.fetchall()

            cur.execute(carrera_query)
            carrera_rows = cur.fetchall()

    return {
        "total_postulaciones": int(summary_row[0]) if summary_row[0] is not None else 0,
        "promedio_puntaje": float(summary_row[1]) if summary_row[1] is not None else None,
        "promedio_ptje_nem": float(summary_row[2]) if summary_row[2] is not None else None,
        "promedio_psu_promlm": float(summary_row[3]) if summary_row[3] is not None else None,
        "por_sexo": [{"sexo": row[0], "total": int(row[1])} for row in sexo_rows],
        "top_regiones": [{"region": row[0], "total": int(row[1])} for row in region_rows],
        "top_carreras": [{"carrera": row[0], "total": int(row[1])} for row in carrera_rows],
    }
