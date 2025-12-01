from fastapi import FastAPI, UploadFile, File, Form
from minio import Minio
from utils import LoggingLogicFunctions as llf
from utils import DocEduc
from utils import BacklogAction
import pandas as pd 

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
    # Logging backlog.txt
    llf.acting_backlog(document= doc, action = BacklogAction.ADD.value)
    # Logging checkpoint.csv
    llf.acting_checkpoints()

    return {"status": "ok", "file": file.filename}

@app.delete("/delete_doc")
async def delete_document(filename: str = Form(...)):

    # check if path_bucket exists

    # bucket_path 
    client.remove_object(BUCKET, filename)

    # dataframe_obj from minio
    dataframe_obj =  pd.DataFrame([{"path_bucket":f"{BUCKET}/{filename}"}])

    # checkpoints table 
    dataframe_checkpoint =  pd.read_csv('checkpoints.csv')

    # join with checkpoints table
    dataf =  dataframe_obj.merge(dataframe_checkpoint, how =  'left', on = 'path_bucket')

    # select columns 
    dataf_dict = dataf[['path_bucket',  'course', 'description']].to_dict(orient="records")[0]
    # create a DocEdu Oject
    doc =  DocEduc(course = dataf_dict.get('course'), 
                description=dataf_dict.get('description'), 
                path=dataf_dict.get('path_bucket'))
    
    # logging delete
    llf.acting_backlog(document= doc, action= BacklogAction.DELETE.value)
    # logging checkpoints
    llf.acting_checkpoints()
    return {"status": "deleted", "file": filename}


@app.get("/list_doc")
async def list_documents():
    objects = client.list_objects(BUCKET) 
    # collect data on minio as table ready to make join with checkpoints table
    dataframe_obj =  pd.DataFrame([{"path_bucket":  f"{BUCKET}/{obj.object_name}"} for obj in objects])

    # checkpoints table 
    dataframe_checkpoint =  pd.read_csv('checkpoints.csv')

    # join with checkpoints table
    dataf =  dataframe_obj.merge(dataframe_checkpoint, how =  'left', on = 'path_bucket')

    # delete columns log
    dataf.drop('log', axis= 1, inplace= True)

    # return information for frontend
    
    return {"documents":dataf.to_dict(orient="records")}




@app.put("/update_doc")
async def update_document(filename: str = Form(...)):
    return {"status":"updated", "file":filename}
