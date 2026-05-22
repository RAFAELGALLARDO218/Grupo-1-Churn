import pandas as pd
import psycopg
from psycopg.rows import dict_row
import os
from dotenv import load_dotenv

load_dotenv()

def load_churn_to_supabase():
    # Leer CSV
    df = pd.read_csv("data/02_Base_WA_Fn-UseC_-Telco-Customer-Churn.csv")
    
    # Limpiar datos
    df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
    df = df.dropna(subset=['TotalCharges'])
    
    # Convertir Churn de Yes/No a 1/0
    df['Churn'] = df['Churn'].map({'Yes': 1, 'No': 0})
    
    # Renombrar columnas para la tabla
    df = df.rename(columns={
        'customerID': 'customer_id',
        'gender': 'gender',
        'SeniorCitizen': 'senior_citizen',
        'Partner': 'partner',
        'Dependents': 'dependents',
        'tenure': 'tenure',
        'PhoneService': 'phone_service',
        'MultipleLines': 'multiple_lines',
        'InternetService': 'internet_service',
        'OnlineSecurity': 'online_security',
        'OnlineBackup': 'online_backup',
        'DeviceProtection': 'device_protection',
        'TechSupport': 'tech_support',
        'StreamingTV': 'streaming_tv',
        'StreamingMovies': 'streaming_movies',
        'Contract': 'contract',
        'PaperlessBilling': 'paperless_billing',
        'PaymentMethod': 'payment_method',
        'MonthlyCharges': 'monthly_charges',
        'TotalCharges': 'total_charges',
        'Churn': 'churn'
    })
    
    # Conectar a Supabase
    conn_string = f"postgresql://{os.getenv('SUPABASE_DB_USER')}:{os.getenv('SUPABASE_DB_PASSWORD')}@{os.getenv('SUPABASE_DB_HOST')}:{os.getenv('SUPABASE_DB_PORT')}/{os.getenv('SUPABASE_DB_NAME')}"
    
    with psycopg.connect(conn_string) as conn:
        # Limpiar tabla existente (opcional)
        conn.execute("TRUNCATE TABLE churn_clientes RESTART IDENTITY")
        
        # Insertar datos
        for _, row in df.iterrows():
            conn.execute("""
                INSERT INTO churn_clientes (
                    customer_id, gender, senior_citizen, partner, dependents,
                    tenure, phone_service, multiple_lines, internet_service,
                    online_security, online_backup, device_protection, tech_support,
                    streaming_tv, streaming_movies, contract, paperless_billing,
                    payment_method, monthly_charges, total_charges, churn
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['customer_id'], row['gender'], row['senior_citizen'],
                row['partner'], row['dependents'], row['tenure'],
                row['phone_service'], row['multiple_lines'], row['internet_service'],
                row['online_security'], row['online_backup'], row['device_protection'],
                row['tech_support'], row['streaming_tv'], row['streaming_movies'],
                row['contract'], row['paperless_billing'], row['payment_method'],
                row['monthly_charges'], row['total_charges'], row['churn']
            ))
        conn.commit()
    
    print(f"✅ Cargadas {len(df)} filas en churn_clientes")

if __name__ == "__main__":
    load_churn_to_supabase()