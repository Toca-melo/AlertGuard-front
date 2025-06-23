import boto3
import os
from dotenv import load_dotenv
from botocore.config import Config

load_dotenv()

# Configuración mejorada del cliente S3
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "us-east-2"),  # Usa variable de entorno o default
    config=Config(
        signature_version='s3v4',
        connect_timeout=300,
        read_timeout=300,
        retries={'max_attempts': 3}  # Añade reintentos automáticos
    )
)

BUCKET_NAME = os.getenv("S3_BUCKET")

def subir_video_s3(file_obj, filename):
    """Sube un archivo a S3 y retorna la URL pública"""
    try:
        s3.upload_fileobj(
            file_obj,
            BUCKET_NAME,
            filename,
            ExtraArgs={
                'ACL': 'public-read',  # Opcional: ajusta los permisos
                'ContentType': 'video/mp4'  # Ajusta según el tipo de video
            }
        )
        return f"https://{BUCKET_NAME}.s3.{os.getenv('AWS_REGION', 'us-east-2')}.amazonaws.com/{filename}"
    except Exception as e:
        print(f"Error al subir a S3: {str(e)}")
        raise