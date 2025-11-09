from db import db
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash

# Modelo de datos

class Usuarios(db.Model):
    # campos
    # id = db.Column(db.Integer, primary_key=True) #Antes se utilizaba así
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    lastanme: Mapped[str] = mapped_column()
    lastname2: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column()  # Hash de la contraseña
    wallet_link: Mapped[Optional[str]] = mapped_column(nullable=True)
    
    def set_password(self, password):
        """Hashea y guarda la contraseña"""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica si la contraseña es correcta"""
        return check_password_hash(self.password, password)
    
    # metodo str para devolver los metodos de la class
    def __str__(self):
        return (
            f'id:{self.id}'
            f'nombre(s){self.name}'
            f'apellido Paterno{self.lastanme}'
            f'apellido Materno{self.lastname2}'
            f'correo Electrónico{self.email}'
            f'wallet_link{self.wallet_link}'
        )
