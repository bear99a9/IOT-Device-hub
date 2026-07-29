from fastapi import HTTPException
from sqlalchemy.orm import Session
from . import models, schemas

def get_device_or_404(db: Session, id: str) -> schemas.DeviceOut:
	device = db.query(models.Device).filter(models.Device.id == id).first()
	if device is None:
		raise HTTPException(status_code=404, detail=f"Device '{id}' not found")
	return device

def list_devices(db: Session, limit: int, offset: int) -> list[schemas.DeviceOut]:
  return db.query(models.Device).limit(limit).offset(offset)

def get_device(db: Session, id: str) -> schemas.DeviceWithHistory:
	return get_device_or_404(db, id)

def register_device(db: Session, device: schemas.DeviceCreate) -> schemas.DeviceOut:
    new_device = models.Device(
      name=device.name,
      type=device.type,
      config=device.config,
      status=device.status,
    )
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
  
    db.add(models.StatusHistory(device_id=new_device.id, status=new_device.status))
    db.commit()
    db.refresh(new_device)
      
    return new_device

def update_device_status(db: Session, id: str, device: schemas.StatusUpdate) -> schemas.StatusUpdate:
    db_device = get_device_or_404(db, id)
    
    db_device.status=device.status

    db.add(models.StatusHistory(device_id=id, status=device.status))
    db.commit()
    db.refresh(db_device)

    return db_device

def update_device_info(db: Session, id: str, device: schemas.DeviceBase) -> schemas.DeviceOut:
    db_device = get_device_or_404(db, id)

    db_device.name=device.name
    db_device.type=device.type
    db_device.config=device.config

    db.commit()
    db.refresh(db_device)

    return db_device


def delete_device(db: Session, id: str) -> None:
    device_to_delete = get_device_or_404(db, id)
    db.delete(device_to_delete)
    db.commit()

    return None