from fastapi import FastAPI, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from .database import engine, SessionLocal
from . import models, schemas, crud

models.Base.metadata.create_all(bind=engine)


app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_device_or_404(db: Session, id: str):
	device = db.query(models.Device).filter(models.Device.id == id).first()
	if device is None:
		raise HTTPException(status_code=404, detail=f"Device '{id}' not found")
	return device

@app.get("/")
def get_home():
    return {
        "status": 200
    }

# GET all devices, paginated
@app.get("/devices", response_model=list[schemas.DeviceOut])
def list_devices(
    db: Session = Depends(get_db),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    return crud.list_devices(db, limit, offset)

# GET a single device
@app.get("/devices/{device_id}", response_model=schemas.DeviceWithHistory)
def get_device(device_id: str, db: Session = Depends(get_db)):
	return crud.get_device_or_404(db, device_id)

# CREATE a new device
@app.post("/devices", response_model=schemas.DeviceOut, status_code=status.HTTP_201_CREATED)
def register_device(device: schemas.DeviceCreate, db: Session = Depends(get_db)):
	return crud.register_device(db, device)

# UPDATE a devices status
@app.patch("/devices/{device_id}/status", response_model=schemas.DeviceOut, status_code=status.HTTP_200_OK)
def update_device_status(device_id: str, device: schemas.StatusUpdate, db: Session = Depends(get_db)):
	return crud.update_device_status(db, device_id, device)

# UPDATE a devices information
@app.put("/devices/{device_id}", response_model=schemas.DeviceOut, status_code=status.HTTP_200_OK)
def update_device_info(device_id: str, device: schemas.DeviceBase, db: Session = Depends(get_db)):
	db_device = get_device_or_404(db, device_id)

	db_device.name=device.name
	db_device.type=device.type
	db_device.config=device.config

	db.commit()
	db.refresh(db_device)

	return db_device

# DELETE a device
@app.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: str, db: Session = Depends(get_db)):
    return crud.delete_device(db, device_id)