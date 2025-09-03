import requests
import os
import json
import urllib3
from google.cloud import storage

API_URL = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones"
TARGET_CURRENCY = "USD"
GCS_BUCKET_NAME = 'bucket-pi-m3-anhs' 
GCP_CREDENTIALS_PATH = 'gcp_credentials.json'

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_exchange_rate(api_url: str, currency_code: str) -> dict:
    """Obtiene la última cotización para una moneda desde la API del BCRA."""
    print(f"Consultando la API en: {api_url}")
    try:
        response = requests.get(api_url, timeout=15, verify=False)
        response.raise_for_status()
        data = response.json()
        
        for cotizacion in data.get('results', {}).get('detalle', []):
            if cotizacion.get('codigoMoneda') == currency_code:
                return {
                    "fecha": data['results'].get('fecha'),
                    "moneda": cotizacion.get('codigoMoneda'),
                    "descripcion": cotizacion.get('descripcion'),
                    "valor_venta": cotizacion.get('tipoCotizacion')
                }
        return {"error": f"Moneda con código '{currency_code}' no encontrada."}
    except requests.exceptions.RequestException as req_err:
        print(f"Error en la solicitud a la API: {req_err}")
        return {"error": "Error de conexión o en la solicitud a la API."}
    except (ValueError, KeyError) as e:
        print(f"Error en la respuesta de la API: {e}")
        return {"error": "Respuesta no válida de la API."}

def validate_data(data: dict, expected_currency: str) -> bool:
    """Valida la completitud, tipos y consistencia de los datos extraídos."""
    if "error" in data:
        print(f"Validación omitida debido a error previo: {data['error']}")
        return False

    print("Iniciando validación de calidad de datos...")
    required_keys = ["fecha", "moneda", "valor_venta"]
    
 
    for key in required_keys:
        if key not in data or data[key] is None:
            print(f"ERROR DE CALIDAD: El campo requerido '{key}' está ausente o es nulo.")
            return False

    if not isinstance(data["valor_venta"], (int, float)):
        print(f"ERROR DE CALIDAD: 'valor_venta' no es un número (valor: {data['valor_venta']}).")
        return False
        
    if data["moneda"] != expected_currency:
        print(f"ERROR DE CALIDAD: La moneda esperada era '{expected_currency}' pero se recibió '{data['moneda']}'.")
        return False
    
    print("VALIDACIÓN DE CALIDAD EXITOSA: Los datos cumplen con el esquema esperado.")
    return True


def upload_to_gcs(data: dict, bucket_name: str, credentials_path: str) -> str:
    """Sube los datos a GCS. Retorna el nombre del blob si tiene éxito."""
    try:
        file_date = data['fecha']
        currency = data['moneda']
        destination_blob_name = f"raw/bcra_exchange_rate_{currency}_{file_date}.json"
        storage_client = storage.Client.from_service_account_json(credentials_path)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        data_string = json.dumps(data)
        blob.upload_from_string(data_string, content_type='application/json')
        print(f"Datos subidos exitosamente a GCS: gs://{bucket_name}/{destination_blob_name}")
        return destination_blob_name
    except Exception as e:
        print(f"Error al subir el archivo a GCS: {e}")
        return None

def verify_gcs_upload(bucket_name: str, blob_name: str, credentials_path: str):
    """Verifica que un archivo exista en GCS y no esté vacío."""
    if not blob_name:
        print("Verificación de carga omitida.")
        return
    print(f"Verificando la carga del archivo gs://{bucket_name}/{blob_name}...")
    try:
        storage_client = storage.Client.from_service_account_json(credentials_path)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        if blob.exists():
            blob.reload()
            if blob.size > 0:
                print(f"VERIFICACIÓN DE CARGA EXITOSA: El archivo existe y su tamaño es {blob.size} bytes.")
            else:
                print("ERROR DE VERIFICACIÓN DE CARGA: El archivo existe pero está vacío.")
        else:
            print("ERROR DE VERIFICACIÓN DE CARGA: El archivo no se encontró en el bucket.")
    except Exception as e:
        print(f"Error durante la verificación en GCS: {e}")


if __name__ == "__main__":
    print("Iniciando extracción y validación de datos del BCRA...")
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GCP_CREDENTIALS_PATH
    
    exchange_rate_data = get_exchange_rate(API_URL, TARGET_CURRENCY)
    

    if exchange_rate_data and validate_data(exchange_rate_data, TARGET_CURRENCY):
        uploaded_blob_name = upload_to_gcs(exchange_rate_data, GCS_BUCKET_NAME, GCP_CREDENTIALS_PATH)
        if uploaded_blob_name:
            verify_gcs_upload(GCS_BUCKET_NAME, uploaded_blob_name, GCP_CREDENTIALS_PATH)
    else:
        print("El proceso se detuvo debido a datos inválidos o a un error en la extracción.")
    
    print("Proceso finalizado.")