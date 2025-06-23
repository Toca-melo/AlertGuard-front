import boto3
import os
from dotenv import load_dotenv
from uvicorn import Config
from botocore.config import Config

load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name="us-east-1",
    onfig=Config(
        signature_version='s3v4',
        connect_timeout=300,
        read_timeout=300
    ) 
)

BUCKET_NAME = os.getenv("S3_BUCKET")

'''
s3.upload_file(
    '/Users/brayanzamora/Downloads/C7Ty4ui5_0.avi',  # Ruta local del video
    BUCKET_NAME,                                     # Nombre del bucket en AWS S3
    '7Ty4ui5_0.avi'                                  # Nombre con el que se guardará en S3
)'''


# aws.py
def subirVideoS3(file_obj, filename):
    s3.upload_fileobj(file_obj, BUCKET_NAME, filename)  # upload_fileobj, no upload_file
    return f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"