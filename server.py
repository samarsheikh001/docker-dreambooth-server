
import datetime
from dotenv import load_dotenv

# load all environment variables
load_dotenv()

from asyncio import sleep
import os
import platform
import shutil
import subprocess
import requests
import zipfile
import io

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import uuid

from to_ckpt import convert_model
from upload import upload_file_to_s3


# now you can use them as regular environment variables
private_key_id = os.getenv('FIREBASE_PRIVATE_KEY_ID')
private_key = os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n')

cred = credentials.Certificate({
    "type": "service_account",
    "project_id": "copykitties-avatar",
    "private_key_id": private_key_id,
    "private_key": private_key,
    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
    "client_id": os.getenv('FIREBASE_CLIENT_ID'),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv('FIREBASE_CERT_URL'),
    "universe_domain": "googleapis.com"
})

app = firebase_admin.initialize_app(cred)
db = firestore.client()


def download_and_extract_zip(url, extract_to='.'):
    print(f"Downloading and extracting zip file from {url}")
    response = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
        zip_file.extractall(path=extract_to)


def delete_file_or_folder(path):
    if os.path.isfile(path):
        os.remove(path)  # remove the file
    elif os.path.isdir(path):
        shutil.rmtree(path)  # remove dir and all contains


def generate_identifier():
    identifier = str(uuid.uuid4())
    return identifier


def check_queued_requests():
    # Create a reference to the 'dreambooth-models' collection
    requests = db.collection('dreambooth-models')

    # Perform a query to find documents where status == 'QUEUE'
    queued_requests = requests.where(
        filter=FieldFilter('status', '==', 'IN_QUEUE')).get()

    # Check if there are any results
    if queued_requests:
        # Get the first request
        first_request = queued_requests[0]
        print(
            f'Request ID: {first_request.id}, Data: {first_request.to_dict()}')
        return first_request
    else:
        print("No requests in 'QUEUE' status.")
        return None


def run_script(request, model_name, output_dir):
    try:
        # Get current timestamp
        now = datetime.datetime.now()
        request.reference.update({'status': 'IN_PROGRESS',
                                  'time_started': now})
        data = request.to_dict()
        subjectIdentifier = generate_identifier()
        subjectType = data.get("subjectType")
        steps = data.get("steps")
        images_url = request.to_dict().get('images')

        instance_prompt = "a photo of a person" if subjectType == "person" else "Unknown subject type"

        request.reference.update({'subjectIdentifier': subjectIdentifier})
        # Download and extract images
        if images_url:
            download_and_extract_zip(images_url, extract_to=subjectIdentifier)

        # Prepare the command
        cmd = [
            "accelerate",
            "launch",
            "train_dreambooth.py",
            "--pretrained_model_name_or_path", model_name,
            "--instance_data_dir", subjectIdentifier,
            "--output_dir", output_dir,
            "--instance_prompt", f"{instance_prompt} {subjectIdentifier}",
            "--resolution", "512",
            "--train_batch_size", "1",
            "--gradient_accumulation_steps", "1",
            "--learning_rate", "5e-6",
            "--lr_scheduler", "constant",
            "--lr_warmup_steps", "0",
            "--max_train_steps", str(steps),
        ]

        # Run the command
        subprocess.run(cmd)
        convert_model(f"output/{steps}", f"{subjectIdentifier}.ckpt", True)
        upload_file_to_s3(f"{subjectIdentifier}.ckpt",
                          f"{subjectIdentifier}.ckpt")

        # Clean up storage
        delete_file_or_folder(subjectIdentifier)  # Delete images folder
        delete_file_or_folder("output")
        delete_file_or_folder(f"{subjectIdentifier}.ckpt")

        # Update the request status to 'FINISHED'
        request.reference.update({'status': 'FINISHED'})
    except Exception as e:
        print(f"Error encountered: {e}")
        # Update the request status to 'FAILED'
        request.reference.update({'status': 'IN_QUEUE'})
        # Rethrow the exception if you want to handle it further up in the call stack
        raise

def terminate_pod(pod_id):
    API_KEY = os.getenv('RUNPOD_API')

    # GraphQL API endpoint URL
    url = f"https://api.runpod.io/graphql?api_key={API_KEY}"

    # GraphQL request headers
    headers = {
        "Content-Type": "application/json",
    }
    query = '''
        mutation PodTerminate($input: PodTerminateInput!) {
          podTerminate(input: $input)
        }
    '''
    payload = {
        "query": query,
        "variables": {
            "input": {
                "podId": pod_id
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        print(data)
        return data
    else:
        print("GraphQL request failed with status code:", response.status_code)
        print(response.text)
        return None

while True:
    # Check queued requests
    queued_request = check_queued_requests()

    if queued_request:
        # Use the data from the request to set the parameters for the run_script function

        run_script(queued_request, "runwayml/stable-diffusion-v1-5", "output")
    else:
        terminate_pod(os.getenv('POD_ID'))
        # No more requests in 'QUEUE' status, exit the loop
        break

#  "IN_QUEUE", "IN_PROGRESS", "FAILED", "COMPLETED"