from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel

# Configuración de la base de datos MySQL
DATABASE_URL = "mysql+mysqlconnector://root@localhost/test_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Modelo de la base de datos
class ItemDB(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(length=255), index=True)
    description = Column(String(length=255), index=True)
    price = Column(Float)
    tax = Column(Float)

# Crear la tabla en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://127.0.0.1",  # Sin barra al final
    "http://127.0.0.1:5500",  # Sin barra al final
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modelo Pydantic para la entrada de datos
class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None


# Ruta para obtener todos los ítems
@app.get("/items/")
def read_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    items = db.query(ItemDB).offset(skip).limit(limit).all()
    return items

# Ruta para crear un nuevo ítem
@app.post("/items/")
def create_item(item: Item, db: Session = Depends(get_db)):
    db_item = ItemDB(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# Ruta para obtener un ítem por ID
@app.get("/items/{item_id}")
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# Ruta para actualizar un ítem por ID
@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item, db: Session = Depends(get_db)):
    db_item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    for field, value in item.dict().items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    return db_item

# Ruta para eliminar un ítem por ID
@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted successfully"}