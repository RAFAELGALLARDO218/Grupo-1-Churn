import subprocess
import sys

def print_header(text):
    print("\n" + "=" * 60)
    print(f"{text}")
    print("=" * 60)

def run_script(script_path):
    print(f"\n Ejecutando: {script_path}")
    result = subprocess.run([sys.executable, script_path])
    
    if result.returncode != 0:
        print(f"Error en {script_path}")
        return False
    print(f"{script_path} completado")
    return True

def main():
    print_header("PIPELINE DE INGESTA - CHURN")
    
    # ORDEN CORRECTO:
    # 1. Preprocesar (limpia y transforma)
    # 2. Validar (verifica calidad de los datos)
    # 3. Cargar (sube a Supabase)
    
    scripts = [
        "scripts/preprocesar_churn_csv.py",  # 1º Preprocesar
        "scripts/validar_churn_csv.py",     # 2º Validar
        "scripts/carga_churn_csv.py"        # 3º Cargar
    ]
    
    for script in scripts:
        if not run_script(script):
            print(f"\n❌ Pipeline detenido en {script}")
            return False
    
    print_header("PIPELINE COMPLETADO EXITOSAMENTE")
    print("\n Los datos han sido:")
    print("   1. Preprocesados")
    print("   2. Validados")
    print("   3. Cargados a Supabase")
    
    return True

if __name__ == "__main__":
    main()