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

# --- CONSULTAR POR ID (Mapeado a BD) ---
@app.route("/api/hojas-vida/<int:id>", methods=["GET"])
def obtener_hojasvidaid(id):
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    sql = "SELECT * FROM hojadvida WHERE id = %s"
    cursor.execute(sql, (id,))
    dato = cursor.fetchone()

    if not dato:
        cursor.close()
        conec.close()
        return {
            "mensaje": "Hoja de vida no encontrada"
        }, 404

    columnas = [columna[0] for columna in cursor.description]
    hoja_vida = dict(zip(columnas, dato))

    cursor.close()
    conec.close()

    return {
        "mensaje": "hoja de vida encontrada",
        "hoja_vida": hoja_vida
    }, 200

# --- ACTUALIZAR REGISTRO POR ID ---
@app.route("/api/actualizarhv/<int:id>", methods=["PUT"])
def actualizar_hoja_vida(id):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json

    # Verificar si el registro existe
    sql_consulta = "SELECT id FROM hojadvida WHERE id = %s"
    cursor.execute(sql_consulta, (id,))
    hoja_vida = cursor.fetchone()

    if not hoja_vida:
        cursor.close()
        conec.close()
        return {
            "mensaje": "La hoja de vida no existe para actualizar",
            "id": id
        }, 404

    sql_update = """UPDATE hojadvida 
                    SET nombre=%s, edad=%s, ciudad=%s, correo=%s, fotografia=%s, programa=%s, ficha=%s, jornada=%s 
                    WHERE id=%s"""
    
    valores = (
        datos["nombre"],
        datos["edad"],
        datos["ciudad"],
        datos["correo"],
        datos.get("fotografia"),
        datos["programa"],
        datos["ficha"],
        datos["jornada"],
        id
    )

    cursor.execute(sql_update, valores)
    conec.commit()

    cursor.close()
    conec.close()

    return {
        "mensaje": "Hoja de vida actualizada con éxito",
        "id": id
    }, 200

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

@app.route("/api/hojasvida", methods=["GET"])
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

@app.route("/api/eliminarhv/<int:id>", methods=["DELETE"])
def eliminar_hoja_vida(id):
    conec = conectar_bd()
    cursor = conec.cursor()

    # Verificar que la hoja de vida exista
    sql_consulta = "SELECT id FROM hojadvida WHERE id = %s"
    cursor.execute(sql_consulta, (id,))
    hoja_vida = cursor.fetchone()

    if not hoja_vida:
        cursor.close()
        conec.close()

        return {
            "mensaje": "La hoja de vida no existe",
            "id": id
        }, 404

    # Corrección: Se cambió "WHERE id = 2" por "WHERE id = %s"
    sql = "DELETE FROM hojadvida WHERE id = %s"
    cursor.execute(sql, (id,))
    conec.commit()

    cursor.close()
    conec.close()

    return {
        "mensaje": "Hoja de vida eliminada correctamente",
        "id": id
    }, 200

if __name__ == "__main__":
    app.run(debug=True)