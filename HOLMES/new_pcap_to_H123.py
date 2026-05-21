import os
import subprocess

def ejecutar_backup(pcap_file):
    # Comando para ejecutar pcap_to_H123.py y pasarle el archivo .pcap
    comando = ['python3', 'pcap_to_H123.py', '--F', pcap_file]
    print(f"Ejecutando: {' '.join(comando)}")
    
    # Ejecutar el comando y obtener la salida
    result = subprocess.run(comando, capture_output=True, text=True)
    return result.stdout

def guardar_resultados_en_archivo(file_name, results):
    # Guardar los resultados en un archivo de texto
    with open(file_name, 'a') as file:
        file.write(results)
        file.write("\n")  # Añadir un salto de línea entre los resultados

def procesar_archivos(pcap_dir):
    # Recorrer todos los archivos .pcap en el directorio de capturas
    for i in range(1, 200):  # Recorre las URLs de 0000001 a 0000199
        archivo_resultados = f"captura_{i:07}_H123.txt"  # Archivo de resultados para cada URL
        
        # Inicializamos el contenido del archivo de resultados
        resultados_url = ""

        for j in range(1, 21):  # Recorre las repeticiones de 01 a 20
            # Crear el nombre del archivo .pcap con el formato correcto
            archivo_pcap = os.path.join(pcap_dir, f"captura_{i:07}_{j:02}_{i}.pcap")

            # Verificamos si el archivo .pcap existe
            if os.path.exists(archivo_pcap):
                print(f"Procesando archivo: {archivo_pcap}")
                
                # Ejecutamos el análisis para el archivo .pcap
                results = ejecutar_backup(archivo_pcap)
                
                # Añadimos los resultados al contenido del archivo de resultados
                resultados_url += results
            else:
                print(f"Archivo no encontrado: {archivo_pcap}")
        
        # Guardamos los resultados en el archivo correspondiente si hay resultados
        if resultados_url:
            guardar_resultados_en_archivo(archivo_resultados, resultados_url)

if __name__ == "__main__":
    # Directorio donde están las capturas
    pcap_dir = "/RAID5-22TB/ohiane.unzilla/x20v9/captura/"
    
    # Procesar todos los archivos en el directorio
    procesar_archivos(pcap_dir)
