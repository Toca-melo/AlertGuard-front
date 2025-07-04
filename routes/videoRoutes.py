import os
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from bson import ObjectId
from datetime import datetime
from werkzeug.utils import secure_filename
import uuid
import boto3
from pymongo import MongoClient, server_api
from pymongo.errors import PyMongoError
from typing import Optional
from botocore.exceptions import BotoCoreError, ClientError
import logging
from dotenv import load_dotenv

# ======================
# CONSTANTES Y CONFIGURACIÓN
# ======================

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Formatos de video permitidos
ALLOWED_VIDEO_FORMATS = ["mp4", "avi", "mov", "mkv", "webm"]
MAX_FILENAME_LENGTH = 120

# Validación de variables de entorno requeridas
REQUIRED_ENV_VARS = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "S3_BUCKET", "MONGODB_URI"]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    raise RuntimeError(f"Faltan variables de entorno requeridas: {', '.join(missing_vars)}")

# Configuración de AWS S3
try:
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        config=boto3.session.Config(
            connect_timeout=300,
            read_timeout=600,
            retries={'max_attempts': 3}
        )
    )
    # Prueba de conexión con S3
    s3_client.head_bucket(Bucket=os.getenv("S3_BUCKET"))
except (BotoCoreError, ClientError) as e:
    logger.error(f"Error configurando cliente S3: {str(e)}")
    raise RuntimeError("Error de configuración AWS S3 - Verifica tus credenciales y configuración")

# Configuración de MongoDB
try:
    mongo_client = MongoClient(
        os.getenv("MONGODB_URI"),
        server_api=server_api.ServerApi('1'),
        connectTimeoutMS=30000,
        socketTimeoutMS=30000
    )
    # Testear conexión a MongoDB
    mongo_client.admin.command('ping')
except PyMongoError as e:
    logger.error(f"Error configurando MongoDB: {str(e)}")
    raise RuntimeError("Error de configuración MongoDB")

# Inicialización de la base de datos
db = mongo_client["alertguard"]
coleccion_videos = db["videos"]

# ======================
# ROUTER DE FASTAPI
# ======================

videos = APIRouter(prefix="/api/v1/videos", tags=["Videos"])

# ======================
# ENDPOINTS
# ======================

@videos.get('')
async def findAllVideos():
    """Obtiene todos los videos (metadatos)"""
    try:
        resultados = list(coleccion_videos.find(
            {}, 
            {"_id": 1, "nombreVideo": 1, "url": 1, "anomalia": 1, "fecha_subida": 1}
        ))
        
        for video in resultados:
            video["_id"] = str(video["_id"])
            if "fecha_subida" in video:
                video["fecha_subida"] = video["fecha_subida"].isoformat()

        return resultados
    except PyMongoError as e:
        logger.error(f"Error MongoDB: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error al conectar con la base de datos"
        )

@videos.post('', status_code=status.HTTP_201_CREATED)
async def create_video(
    nombreVideo: str, 
    anomalia: bool, 
    file: UploadFile = File(...)
):
    """Sube un video a S3 y guarda metadatos en MongoDB"""
    try:
        # Validaciones
        if not file.filename or "." not in file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo debe tener una extensión válida"
            )

        file_format = file.filename.split(".")[-1].lower()
        if file_format not in ALLOWED_VIDEO_FORMATS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato no soportado. Formatos permitidos: {', '.join(ALLOWED_VIDEO_FORMATS)}"
            )

        # Subida a S3
        s3_key = f"videos/{uuid.uuid4()}_{secure_filename(file.filename)}"
        try:
            s3_client.upload_fileobj(
                file.file,
                os.getenv("S3_BUCKET"),
                s3_key,
                ExtraArgs={
                    'ContentType': file.content_type,
                    'ACL': 'private'  # Cambiar a 'public-read' si necesitas acceso público
                }
            )
            url = f"https://{os.getenv('S3_BUCKET')}.s3.amazonaws.com/{s3_key}"
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Error S3: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Error al subir a AWS S3"
            )

        # Guardar metadatos
        video_data = {
            "nombreVideo": nombreVideo,
            "s3_key": s3_key,
            "url": url,
            "tamaño_bytes": file.size,
            "formato": file_format,
            "anomalia": anomalia,
            "fecha_subida": datetime.utcnow(),
            "procesado": False
        }

        try:
            result = coleccion_videos.insert_one(video_data)
            return {
                "_id": str(result.inserted_id),
                "nombreVideo": nombreVideo,
                "url": url,
                "tamaño": f"{round(file.size / (1024 * 1024), 2)} MB",
                "formato": file_format,
                "anomalia": anomalia,
                "fecha_subida": video_data["fecha_subida"].isoformat()
            }
        except PyMongoError as e:
            logger.error(f"Error MongoDB: {str(e)}")
            # Intentar limpiar S3 si falla MongoDB
            try:
                s3_client.delete_object(Bucket=os.getenv("S3_BUCKET"), Key=s3_key)
            except Exception as s3_err:
                logger.error(f"Error limpiando S3: {str(s3_err)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al guardar metadatos"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )

@videos.get('/{idVideo}')
async def find_id_video(idVideo: str):
    """Obtiene un video específico por ID"""
    try:
        if not ObjectId.is_valid(idVideo):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de video inválido"
            )

        video = coleccion_videos.find_one({"_id": ObjectId(idVideo)})
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video no encontrado"
            )

        video["_id"] = str(video["_id"])
        if "fecha_subida" in video:
            video["fecha_subida"] = video["fecha_subida"].isoformat()
        return video

    except PyMongoError as e:
        logger.error(f"Error MongoDB: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error de base de datos"
        )

@videos.put('/{idVideo}')
async def update_video(idVideo: str, video: dict):
    """Actualiza metadatos de un video"""
    try:
        if not ObjectId.is_valid(idVideo):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de video inválido"
            )

        # Eliminar campos que no deben actualizarse
        video.pop("_id", None)
        video.pop("s3_key", None)
        video.pop("url", None)
        video.pop("fecha_subida", None)

        result = coleccion_videos.update_one(
            {"_id": ObjectId(idVideo)},
            {"$set": video}
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video no encontrado"
            )

        return {"mensaje": "Video actualizado correctamente"}

    except PyMongoError as e:
        logger.error(f"Error MongoDB: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar"
        )

@videos.delete('/{idVideo}')
async def delete_video(idVideo: str):
    """Elimina un video de S3 y MongoDB"""
    try:
        if not ObjectId.is_valid(idVideo):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de video inválido"
            )

        # 1. Obtener metadatos para la clave S3
        video = coleccion_videos.find_one({"_id": ObjectId(idVideo)})
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video no encontrado"
            )

        # 2. Eliminar de S3
        try:
            s3_client.delete_object(
                Bucket=os.getenv("S3_BUCKET"),
                Key=video["s3_key"]
            )
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Error S3 al eliminar: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Error al eliminar de AWS S3"
            )

        # 3. Eliminar de MongoDB
        result = coleccion_videos.delete_one({"_id": ObjectId(idVideo)})
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video no encontrado"
            )

        return {"message": "Video eliminado correctamente"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al eliminar"
        )

@videos.post("/prueba-s3")
async def prueba_s3_connection():
    """Endpoint para probar la conexión con AWS S3"""
    try:
        s3_client.head_bucket(Bucket=os.getenv("S3_BUCKET"))
        return {
            "status": "success", 
            "message": f"Conexión al bucket {os.getenv('S3_BUCKET')} exitosa"
        }
    except (BotoCoreError, ClientError) as e:
        logger.error(f"Error S3: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error conectando a AWS S3: {str(e)}"
        )