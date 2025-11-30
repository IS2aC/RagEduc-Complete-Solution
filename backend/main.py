from fastapi import FastAPI, UploadFile, File, Form
from minio import Minio
from datetime import datetime
from utils import LoggingLogicFunctions as llf
from utils import DocEduc
from utils import BacklogAction

app = FastAPI()

client = Minio(
    "localhost:9000",
    access_key="admin",
    secret_key="admin123",
    secure=False
)

BUCKET = "documents-edu"
if not client.bucket_exists(BUCKET):
    client.make_bucket(BUCKET)

@app.post("/add_doc")
async def upload_document(
    course: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...)
):
    client.put_object(
        bucket_name=BUCKET,
        object_name=file.filename,
        data=file.file,
        length=-1,
        part_size=10 * 1024 * 1024,
    )


    # Recuperation du chemin du dernier fichier inserer
    minio_path = f"{BUCKET}/{file.filename}"
    # Creation de l'element DocEduc pour les besoins du logging
    doc =  DocEduc(course, description, path=minio_path)
    #logging 
    llf.acting_backlog(document= doc, action = BacklogAction.ADD.value)


    return {"status": "ok", "file": file.filename}


@app.delete("/delete_doc")
async def delete_document(filename: str = Form(...)):
    client.remove_object(BUCKET, filename)
    return {"status": "deleted", "file": filename}


@app.get("/list_doc")
async def list_documents():
    objects = client.list_objects(BUCKET)
    return [{"name": obj.object_name} for obj in objects]
