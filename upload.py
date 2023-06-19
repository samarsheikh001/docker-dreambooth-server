import os
import boto3

s3 = boto3.resource(
    's3',
    endpoint_url=os.getenv("CLOUDFLARE_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("CLOUDFLARE_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("CLOUDFLARE_SECRET_ACCESS_KEY")
)

bucket = s3.Bucket('models')


def upload_file_to_s3(file_path, s3_key):
    try:
        bucket.upload_file(file_path, s3_key)
        print("File uploaded successfully!")
    except Exception as e:
        print(f"Error uploading file: {e}")
        raise


def download_file_from_s3(s3_key, file_path):
    try:
        bucket.download_file(s3_key, file_path)
        print("File downloaded successfully!")
    except Exception as e:
        print(f"Error downloading file: {e}")


# Replace with the actual file path
file_path = 'f7077585-e43f-4510-bf9c-0ee744472bd0.ckpt'
# Replace with the desired S3 key
s3_key = 'f7077585-e43f-4510-bf9c-0ee744472bd0.ckpt'

# upload_file_to_s3(file_path, s3_key)
# download_file_from_s3(s3_key, file_path)
