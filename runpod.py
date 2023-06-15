import os
import uuid
import requests

API_KEY = os.getenv("RUNPOD_API_KEY")

# GraphQL API endpoint URL
url = f"https://api.runpod.io/graphql?api_key={API_KEY}"

# GraphQL request headers
headers = {
    "Content-Type": "application/json",
}

def terminate_pod(pod_id):
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
        return data
    else:
        print("GraphQL request failed with status code:", response.status_code)
        print(response.text)
        return None


def get_pods():
    query = '''
        query Pods {
          myself {
            pods {
              id
              name
              runtime {
                uptimeInSeconds
                ports {
                  ip
                  isIpPublic
                  privatePort
                  publicPort
                  type
                }
                gpus {
                  id
                  gpuUtilPercent
                  memoryUtilPercent
                }
                container {
                  cpuPercent
                  memoryPercent
                }
              }
            }
          }
        }
    '''
    payload = {
        "query": query,
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        pods = data["data"]["myself"]["pods"]
        return pods
    else:
        print("GraphQL request failed with status code:", response.status_code)
        print(response.text)
        return None

def find_and_terminate_pod(name_to_find):
    pods = get_pods()
    found_id = None
    
    for item in pods:
        if item['name'] == name_to_find:
            found_id = item['id']
            terminate_pod(found_id)
            break