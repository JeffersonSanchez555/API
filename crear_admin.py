from werkzeug.security import (generate_password_hash,check_password_hash)
from database import conectar_bd
from flask import Flask, request,jsonify
from flask_cors import CORS
from database import conectar_bd
from dotenv import load_dotenv
import os
from getpass import getpass




def crear_administrador():

    nombre = input("Ingresar nombre del rol reclutador")
    correo = input("Ingresar correo del rol reclutador")
    password = getpass("Contraseña")


    if len(password) < 8 :
        print("La cocntraseña debe tener minimo 8 caracteres")
        return

    conexion = conectar_bd()
    cursor = conexion.cursor()

    try:
        cursor.execute("SELECT id FROM usuarios WHERE Correo = %s",(correo,))
        existente = cursor.fetchone()

        if existente:
            print("Este correo ya esta registrado")
            return

        #cifrado contra
        password_hash = generate_password_hash(password)

        sql = """INSERT INTO usuarios(nombre,correo,password,rol, estado)VALUES(%s,%s,%s, 'reclutador', 1)"""

        cursor.execute(sql,(nombre,correo, password_hash))

        conexion.commit()
        print("Reclutador creado correctamente")
    except Exception as error:
        conexion.rollback()
        print("Error:",error)
    finally:
            cursor.close()
            conexion.close()

if __name__== "__main__":
     crear_administrador()