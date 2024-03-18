import os
import requests
import json
import pydicom
from requests.auth import HTTPBasicAuth

# Credenciales de autenticación de Orthanc remoto
username_remote = "user1"
password_remote = "pass1"



# URL del Servidor Orthanc remoto
url_remote = "http://222.222.228.180:8042"

# Credenciales de autenticación de Orthanc Local
username_local = "user2"
password_local = "pass2"

# URL del Servidor Orthanc local
url_local = "http://111.111.49.199:8042"

# Carpeta donde se guardarán los datos en el servidor local
base_folder_path_local = "C:\\Orthanc"  # Ruta base para guardar los archivos en el servidor local
os.makedirs(base_folder_path_local, exist_ok=True)  # Crear la carpeta base si no existe

# Endpoint para obtener el primer paciente en el servidor remoto
patient_url_remote = f"{url_remote}/patients"

# Realizar una solicitud GET al servidor Orthanc remoto para obtener información del paciente
response_remote = requests.get(patient_url_remote, auth=HTTPBasicAuth(username_remote, password_remote))

# Comprobar si la solicitud fue exitosa (código de estado 200)
if response_remote.status_code == 200:
    # Obtener el primer paciente de la respuesta JSON del servidor remoto
    patient_id_remote = response_remote.json()[1]

    # Endpoint para obtener información del paciente en el servidor remoto
    patient_info_url_remote = f"{url_remote}/patients/{patient_id_remote}"

    # Realizar una solicitud GET al servidor Orthanc remoto para obtener información del paciente
    patient_info_response_remote = requests.get(patient_info_url_remote, auth=HTTPBasicAuth(username_remote, password_remote))

    # Comprobar si la solicitud fue exitosa (código de estado 200)
    if patient_info_response_remote.status_code == 200:
        # Guardar la información del paciente en un archivo en el servidor local
        patient_info_remote = patient_info_response_remote.json()
        patient_file_path_local = os.path.join(base_folder_path_local, f"patient_{patient_id_remote}.json")
        with open(patient_file_path_local, "w") as patient_file_local:
            json.dump(patient_info_remote, patient_file_local)
        print(f"Información del paciente guardada en: {patient_file_path_local}")

        # Verificar si el nombre del paciente ha sido anonimizado
        patient_name = patient_info_remote.get('MainDicomTags', {}).get('PatientName', 'Desconocido')
        if patient_name == "Anonymized1":
            print("El nombre del paciente ha sido anonimizado.")
        else:
            # Imprimir el nombre del paciente
            print(f"Nombre del paciente: {patient_name}")

        # Obtener el ID del primer estudio asociado al paciente en el servidor remoto
        first_study_id_remote = patient_info_remote["Studies"][0]

        # Endpoint para obtener información del primer estudio en el servidor remoto
        study_info_url_remote = f"{url_remote}/studies/{first_study_id_remote}"

        # Realizar una solicitud GET al servidor Orthanc remoto para obtener información del estudio
        study_info_response_remote = requests.get(study_info_url_remote, auth=HTTPBasicAuth(username_remote, password_remote))

        # Comprobar si la solicitud fue exitosa (código de estado 200)
        if study_info_response_remote.status_code == 200:
            # Guardar la información del estudio en un archivo en el servidor local
            study_info_remote = study_info_response_remote.json()
            study_file_path_local = os.path.join(base_folder_path_local, f"study_{first_study_id_remote}.json")
            with open(study_file_path_local, "w") as study_file_local:
                json.dump(study_info_remote, study_file_local)
            print(f"Información del primer estudio guardada en: {study_file_path_local}")

            # Imprimir el título del estudio
            print(f"Título del estudio: {study_info_remote.get('MainDicomTags', {}).get('StudyDescription', 'Desconocido')}")

            # Imprimir la descripción del estudio
            print(f"Descripción del estudio: {study_info_remote.get('MainDicomTags', {}).get('StudyDescription', 'Desconocido')}")

            # Obtener los identificadores de las series asociadas al estudio en el servidor remoto
            series_ids_remote = study_info_remote["Series"]

            # Descargar los archivos DICOM de cada serie desde el servidor remoto y cargarlos en el servidor local
            for series_id_remote in series_ids_remote:
                # Endpoint para obtener información de la serie en el servidor remoto
                series_info_url_remote = f"{url_remote}/series/{series_id_remote}"

                # Realizar una solicitud GET al servidor Orthanc remoto para obtener información de la serie
                series_info_response_remote = requests.get(series_info_url_remote, auth=HTTPBasicAuth(username_remote, password_remote))

                # Comprobar si la solicitud fue exitosa (código de estado 200)
                if series_info_response_remote.status_code == 200:
                    # Crear la estructura de carpetas basada en el identificador de la serie en el servidor local
                    series_folder_path_local = os.path.join(base_folder_path_local, series_id_remote[:2], series_id_remote[2:4])
                    os.makedirs(series_folder_path_local, exist_ok=True)

                    # Descargar los archivos DICOM de la serie desde el servidor remoto y cargarlos en el servidor local
                    instances_remote = series_info_response_remote.json()["Instances"]
                    for instance_id_remote in instances_remote:
                        # Endpoint para descargar el archivo DICOM desde el servidor remoto
                        instance_url_remote = f"{url_remote}/instances/{instance_id_remote}/file"

                        # Realizar una solicitud GET al servidor Orthanc remoto para descargar el archivo DICOM
                        instance_response_remote = requests.get(instance_url_remote, auth=HTTPBasicAuth(username_remote, password_remote))

                        # Comprobar si la solicitud fue exitosa (código de estado 200)
                        if instance_response_remote.status_code == 200:
                            # Guardar el archivo DICOM en el servidor local
                            dcm_file_path_local = os.path.join(series_folder_path_local, f"{instance_id_remote}.dcm")
                            with open(dcm_file_path_local, "wb") as dcm_file_local:
                                dcm_file_local.write(instance_response_remote.content)
                            #print(f"Archivo DICOM {instance_id_remote} guardado en: {dcm_file_path_local}")

                            # Cargar el archivo DICOM en el servidor local
                            with open(dcm_file_path_local, "rb") as dcm_file_local:
                                files = {'file': (f"{instance_id_remote}.dcm", dcm_file_local, 'application/dicom')}
                                upload_response_local = requests.post(f"{url_local}/instances", auth=HTTPBasicAuth(username_local, password_local), files=files)
                                if upload_response_local.status_code == 200:
                                    print(f"Archivo DICOM ok.")
                                else:
                                    print(f"Error al cargar el archivo DICOM {instance_id_remote} en Orthanc local: {upload_response_local.status_code}")
                        else:
                            print(f"Error al descargar el archivo DICOM {instance_id_remote} desde el servidor remoto: {instance_response_remote.status_code}")
                else:
                    print(f"Error al obtener información de la serie {series_id_remote} desde el servidor remoto: {series_info_response_remote.status_code}")
        else:
            print(f"Error al obtener información del estudio desde el servidor remoto: {study_info_response_remote.status_code}")
    else:
        print(f"Error al obtener información del paciente desde el servidor remoto: {patient_info_response_remote.status_code}")
else:
    print(f"Error al obtener el primer paciente desde el servidor remoto: {response_remote.status_code}")
