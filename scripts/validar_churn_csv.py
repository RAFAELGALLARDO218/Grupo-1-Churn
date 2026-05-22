# scripts/validar_churn_csv.py
# ============================================================
# VALIDACIÓN DE DATOS PREPROCESADOS - CHURN
# ============================================================

from pathlib import Path
import pandas as pd

def validar_dataset(ruta_archivo: Path):
    """
    Valida el archivo preprocesado y corrige problemas básicos
    
    Retorna:
        (bool, DataFrame): (es_válido, DataFrame_corregido)
    """
    
    print("=" * 60)
    print(" INICIANDO VALIDACIÓN DE DATOS - CHURN")
    print("=" * 60)
    
    # 1. Verificar que el archivo existe
    if not ruta_archivo.exists():
        print(f" No se encuentra el archivo: {ruta_archivo}")
        return False, None
    
    # 2. Cargar datos
    df = pd.read_excel(ruta_archivo)
    print(f" Dataset cargado: {len(df)} filas, {len(df.columns)} columnas")
    
    # 3. Verificar columna churn
    if 'churn' not in df.columns:
        print(" Error: No se encuentra la columna 'churn'")
        return False, df
    
    # 4. Mostrar distribución de churn
    churn_counts = df['churn'].value_counts()
    print(f"\n Distribución de churn:")
    print(f"   Churn=1 (Sí): {churn_counts.get(1, 0)}")
    print(f"   Churn=0 (No): {churn_counts.get(0, 0)}")
    
    # 5. Eliminar filas con valores nulos en columnas críticas
    columnas_criticas = ['churn', 'tenure', 'monthlycharges']
    columnas_existentes = [col for col in columnas_criticas if col in df.columns]
    
    if columnas_existentes:
        antes = len(df)
        df = df.dropna(subset=columnas_existentes)
        eliminados = antes - len(df)
        if eliminados > 0:
            print(f" Se eliminaron {eliminados} filas con valores nulos")
    
    # 6. Eliminar duplicados
    antes = len(df)
    df = df.drop_duplicates()
    duplicados = antes - len(df)
    if duplicados > 0:
        print(f" Se eliminaron {duplicados} filas duplicadas")
    
    # 7. Validar rangos
    if 'tenure' in df.columns:
        fuera_rango = (df['tenure'] < 0) | (df['tenure'] > 72)
        if fuera_rango.sum() > 0:
            print(f" Se eliminaron {fuera_rango.sum()} filas con tenure fuera de rango (0-72)")
            df = df[~fuera_rango]
    
    if 'monthlycharges' in df.columns:
        fuera_rango = (df['monthlycharges'] < 0) | (df['monthlycharges'] > 200)
        if fuera_rango.sum() > 0:
            print(f" Se eliminaron {fuera_rango.sum()} filas con monthlycharges fuera de rango (0-200)")
            df = df[~fuera_rango]
    
    if 'seniorcitizen' in df.columns:
        valores_invalidos = ~df['seniorcitizen'].isin([0, 1])
        if valores_invalidos.sum() > 0:
            print(f" Se corrigieron {valores_invalidos.sum()} valores inválidos en seniorcitizen")
            df['seniorcitizen'] = df['seniorcitizen'].apply(lambda x: 1 if x > 0 else 0)
    
    # 8. Verificar que no queden filas
    if len(df) == 0:
        print(" Error: No quedan filas después de la validación")
        return False, df
    
    # 9. Resumen final
    print("\n" + "=" * 60)
    print(" RESUMEN DE VALIDACIÓN")
    print("=" * 60)
    print(f" Filas finales: {len(df)}")
    print(f" Columnas: {len(df.columns)}")
    print(f"\n Distribución final de churn:")
    print(f"   Churn=1: {(df['churn']==1).sum()}")
    print(f"   Churn=0: {(df['churn']==0).sum()}")
    
    print("\n VALIDACIÓN EXITOSA")
    return True, df

def guardar_dataset_validado(df: pd.DataFrame, ruta_salida: Path) -> None:
    """Guarda el dataset validado y corregido"""
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(ruta_salida, index=False)
    print(f"\n Dataset validado guardado en: {ruta_salida}")

# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    # Archivos
    archivo_entrada = Path("data/Telco-Customer-Churn_preprocesado.xlsx")
    archivo_salida = Path("data/Telco-Customer-Churn_validado.xlsx")
    
    # Validar
    valido, df = validar_dataset(archivo_entrada)
    
    if valido and df is not None:
        guardar_dataset_validado(df, archivo_salida)
        print("\n Validación completada. Archivo listo para carga.")
    else:
        print("\n Validación fallida. Revisa los errores.")