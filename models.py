from db import db
from sqlalchemy.orm import Mapped, mapped_column

# Modelo de datos

class Usuarios(db.Model):
    # campos
    # id = db.Column(db.Integer, primary_key=True) #Antes se utilizaba así
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    lastanme: Mapped[str] = mapped_column()
    lastname2: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column(unique=True)
    
    # metodo str para devolver los metodos de la class
    def __str__(self):
        return (
            f'id:{self.id}'
            f'nombre(s){self.name}'
            f'apellido Paterno{self.lastanme}'
            f'apellido Materno{self.lastname2}'
            f'correo Electrónico{self.email}'
        )
