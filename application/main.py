from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from minio import Minio
from utils import LoggingLogicFunctions as llf
from utils import DocEduc
from utils import BacklogAction
import os
import pandas as pd 

app = FastAPI()

# Configuration des templates et fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

client = Minio(
    "localhost:9000",
    access_key="admin",
    secret_key="admin123",
    secure=False
)

BUCKET = "documents-edu"
if not client.bucket_exists(BUCKET):
    client.make_bucket(BUCKET)
    

# ========== CHAT BOT SPACE =============
# ========== ROUTES ADMIN HTML ==========

@app.get("/admin", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Page principale - Dashboard"""

    doc_actifs = len([obj.object_name for obj in client.list_objects(BUCKET)])
    if os.path.exists('backlog.txt'):
        number_of_requests =  pd.read_csv('backlog.txt', sep=',', engine='python').shape[0]
    else: 
        number_of_requests = 0
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Dashboard",
        "doc_actifs":f"{doc_actifs}", #
        "number_of_requests":f"{number_of_requests}" #
    })

@app.get("/admin_integration", response_class=HTMLResponse)
async def integration_page(request: Request):
    """Page d'intégration des documents"""
    return templates.TemplateResponse("integration.html", {
        "request": request,
        "title": "Intégration"
    })

# ========== API ENDPOINTS ==========

@app.post("/add_doc")
async def upload_document(
    course: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload un document dans MinIO"""
    client.put_object(
        bucket_name=BUCKET,
        object_name=file.filename,
        data=file.file,
        length=-1,
        part_size=10 * 1024 * 1024,
    )

    minio_path = f"{BUCKET}/{file.filename}"
    doc = DocEduc(course, description, path=minio_path)
    
    llf.acting_backlog(document=doc, action=BacklogAction.ADD.value)
    llf.acting_checkpoints()

    return {"status": "ok", "file": file.filename}

@app.delete("/delete_doc")
async def delete_document(filename: str = Form(...)):
    """Supprime un document de MinIO"""
    objects_list = [obj.object_name for obj in client.list_objects(BUCKET)]

    if filename not in objects_list:
        return {"message": "file not exists"}
    
    client.remove_object(BUCKET, filename)

    dataframe_obj = pd.DataFrame([{"path_bucket": f"{BUCKET}/{filename}"}])
    dataframe_checkpoint = pd.read_csv('checkpoints.csv')
    dataf = dataframe_obj.merge(dataframe_checkpoint, how='left', on='path_bucket')
    
    dataf_dict = dataf[['path_bucket', 'course', 'description']].to_dict(orient="records")[0]
    doc = DocEduc(
        course=dataf_dict.get('course'), 
        description=dataf_dict.get('description'), 
        path=dataf_dict.get('path_bucket')
    )
    
    llf.acting_backlog(document=doc, action=BacklogAction.DELETE.value)
    llf.acting_checkpoints()
    
    return {"status": "deleted", "file": filename}

@app.get("/list_doc")
async def list_documents():
    """Liste tous les documents"""
    if pd.read_csv('checkpoints.csv').empty:
        return {"documents": "null"}
    
    objects = client.list_objects(BUCKET) 
    dataframe_obj = pd.DataFrame([
        {"path_bucket": f"{BUCKET}/{obj.object_name}"} for obj in objects
    ])

    dataframe_checkpoint = pd.read_csv('checkpoints.csv')
    dataf = dataframe_obj.merge(dataframe_checkpoint, how='left', on='path_bucket')
    dataf.drop('log', axis=1, inplace=True)
    
    return {"documents": dataf.to_dict(orient="records")}

@app.put("/update_doc")
async def update_document(filename: str = Form(...)):
    """Mise à jour d'un document (à venir)"""
    return {"message": "for next version, not now"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)