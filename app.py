from flask import Flask, request
from database import conectar_bd

app = Flask(__name__)

@app.route("/probar")
def probar_data():
    conec = conectar_bd()
    if conec.is_connected():
        conec.close()
        return {
            "mensaje": "conexion ok"
        }

@app.route("/api/registrohv", methods=["POST"])
def registrohvida():
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json

    # Verificar si el usuario ya existe por correo
    sql_consulta = "SELECT id FROM hojadvida WHERE correo = %s"
    cursor.execute(sql_consulta, (datos["correo"],))
    usuario_existente = cursor.fetchone()

    if usuario_existente:
        id_existente = usuario_existente[0]
        cursor.close()
        conec.close()
        return {
            "mensaje": "El usuario ya está registrado con este correo",
            "id": id_existente
        }

    # Insertar nueva hoja de vida
    sql = """INSERT INTO hojadvida(nombre, edad, ciudad, correo, fotografia, programa, ficha, jornada) 
             VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"""
    
    valor = (
        datos["nombre"],
        datos["edad"],
        datos["ciudad"],
        datos["correo"],
        datos.get("fotografia"),
        datos["programa"],
        datos["ficha"],
        datos["jornada"]
    )
    
    cursor.execute(sql, valor)
    conec.commit()
    
    id_generado = cursor.lastrowid

    cursor.close()
    conec.close()

    return {
        "mensaje": "Hoja de vida registrada con éxito",
        "id": id_generado
    }, 201

@app.route("/api/hojas-vida/<int:id>")
def obtener_hojasvidaid(id):
    return {
        "mensaje": "hoja de vida encontrada",
        "id": id
    }

@app.route("/api/hojas-vida")
def obtener_hojasvida():
    hojas_vida = [
        {
            "id": 1,
            "nombre": "Triple z",
            "edad": 79,
            "ciudad": "Bogota",
            "fotografia": "foto",
            "programa": "adso",
            "ficha": 3262,
            "jornada": "diurna"
        },
        {
            "id": 2,
            "nombre": "Jeff the killer",
            "edad": 50,
            "ciudad": "Bogota",
            "fotografia": "foto",
            "programa": "adso",
            "ficha": 62320,
            "jornada": "diurna"
        }
    ]
    return hojas_vida


@app.route("/api/hojasvida",methods=["GET"])
def listar_hojasvida():
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    sql = "SELECT * FROM hojadvida"

    cursor.execute(sql)
    datos = cursor.fetchall()

    columnas = [columna[0] for columna in cursor.description]
    resultado = []

    for lista in datos:
        hoja_vida = dict(zip(columnas, lista))
        resultado.append(hoja_vida)

    cursor.close()
    conec.close()

    return {
        "hojas_vida": resultado
    }


if __name__ == "__main__":
    app.run(debug=True)