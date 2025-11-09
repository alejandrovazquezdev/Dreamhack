from db import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets

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


class Sala(db.Model):
    """Modelo para salas de negociación P2P"""
    __tablename__ = 'salas'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(unique=True, index=True)  # Código único de 8 dígitos
    
    # Información del producto
    nombre_producto: Mapped[str] = mapped_column()
    descripcion: Mapped[Optional[str]] = mapped_column(nullable=True)
    precio: Mapped[float] = mapped_column()
    condicion: Mapped[str] = mapped_column()  # 'Nuevo' o 'Usado'
    
    # Relación con el creador
    creador_id: Mapped[int] = mapped_column(db.ForeignKey('usuarios.id'))
    
    # Metadatos
    fecha_creacion: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    activa: Mapped[bool] = mapped_column(default=True)
    
    @staticmethod
    def generar_codigo():
        """Genera un código único de 8 dígitos"""
        while True:
            codigo = ''.join([str(secrets.randbelow(10)) for _ in range(8)])
            # Verificar que no exista
            if not Sala.query.filter_by(codigo=codigo).first():
                return codigo
    
    def get_link(self):
        """Retorna el link completo para compartir"""
        return f"http://127.0.0.1:5000/sala/{self.codigo}"
    
    def __str__(self):
        return f'Sala {self.codigo} - {self.nombre_producto} (${self.precio})'


class MiembroSala(db.Model):
    """Modelo para registrar usuarios que se unen a salas"""
    __tablename__ = 'miembros_sala'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    sala_id: Mapped[int] = mapped_column(db.ForeignKey('salas.id'))
    usuario_id: Mapped[int] = mapped_column(db.ForeignKey('usuarios.id'))
    fecha_union: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    rol: Mapped[str] = mapped_column(default='comprador')  # 'vendedor' o 'comprador'
    
    # Constraint único para evitar duplicados
    __table_args__ = (
        db.UniqueConstraint('sala_id', 'usuario_id', name='unique_miembro_sala'),
    )
    
    def __str__(self):
        return f'Usuario {self.usuario_id} en Sala {self.sala_id}'
