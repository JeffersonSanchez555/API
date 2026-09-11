from flask import Flask, request
from database import conectar_bd

app = Flask(__name__)


@app.route("/probar")
def probar_data():
    conec = conectar_bd()
    if conec.is_connected():
        conec.close()
        return {"mensaje": "conexion ok"}




@app.route("/api/registrohv", methods=["POST"])
def registrohvida():
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json

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
        }, 400

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

    return {"mensaje": "Hoja de vida registrada con éxito", "id": id_generado}, 201



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

    return {"hojas_vida": resultado}, 200



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
        return {"mensaje": "Hoja de vida no encontrada"}, 404

    columnas = [columna[0] for columna in cursor.description]
    hoja_vida = dict(zip(columnas, dato))

    cursor.close()
    conec.close()

    return {"mensaje": "hoja de vida encontrada", "hoja_vida": hoja_vida}, 200



@app.route("/api/actualizarhv/<int:id>", methods=["PUT"])
def actualizar_hoja_vida(id):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json

    sql_consulta = "SELECT id FROM hojadvida WHERE id = %s"
    cursor.execute(sql_consulta, (id,))
    hoja_vida = cursor.fetchone()

    if not hoja_vida:
        cursor.close()
        conec.close()
        return {"mensaje": "La hoja de vida no existe para actualizar", "id": id}, 404

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

    return {"mensaje": "Hoja de vida actualizada con éxito", "id": id}, 200



@app.route("/api/eliminarhv/<int:id>", methods=["DELETE"])
def eliminar_hoja_vida(id):
    conec = conectar_bd()
    cursor = conec.cursor()

    sql_consulta = "SELECT id FROM hojadvida WHERE id = %s"
    cursor.execute(sql_consulta, (id,))
    hoja_vida = cursor.fetchone()

    if not hoja_vida:
        cursor.close()
        conec.close()
        return {"mensaje": "La hoja de vida no existe", "id": id}, 404

    sql = "DELETE FROM hojadvida WHERE id = %s"
    cursor.execute(sql, (id,))
    conec.commit()

    cursor.close()
    conec.close()

    return {"mensaje": "Hoja de vida eliminada correctamente", "id": id}, 200


# Consultar todos los estudios de una hoja de vida
@app.route("/api/hojas-vida/<int:id_hv>/estudios", methods=["GET"])
def obtener_estudios_hv(id_hv):
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    sql = "SELECT * FROM estudios WHERE id_hoja_vida = %s"
    cursor.execute(sql, (id_hv,))
    datos = cursor.fetchall()

    columnas = [col[0] for col in cursor.description]
    estudios = [dict(zip(columnas, fila)) for fila in datos]

    cursor.close()
    conec.close()
    return {"estudios": estudios}, 200


# Registrar un nuevo estudio
@app.route("/api/hojas-vida/<int:id_hv>/estudios", methods=["POST"])
def registrar_estudio(id_hv):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json

    sql = "INSERT INTO estudios (titulo, institucion, fecha_fin, id_hoja_vida) VALUES (%s, %s, %s, %s)"
    valores = (datos["titulo"], datos["institucion"], datos.get("fecha_fin"), id_hv)
    
    cursor.execute(sql, valores)
    conec.commit()
    id_generado = cursor.lastrowid

    cursor.close()
    conec.close()
    return {"mensaje": "Estudio registrado con éxito", "id": id_generado}, 201


# Consultar un estudio
@app.route("/api/estudios/<int:id>", methods=["GET"])
def obtener_estudio(id):
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    sql = "SELECT * FROM estudios WHERE id = %s"
    cursor.execute(sql, (id,))
    dato = cursor.fetchone()

    if not dato:
        cursor.close()
        conec.close()
        return {"mensaje": "Estudio no encontrado"}, 404

    columnas = [col[0] for col in cursor.description]
    estudio = dict(zip(columnas, dato))

    cursor.close()
    conec.close()
    return {"estudio": estudio}, 200


# Actualizar un estudio
@app.route("/api/estudios/<int:id>", methods=["PUT"])
def actualizar_estudio(id):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json

    sql = "UPDATE estudios SET titulo=%s, institucion=%s, fecha_fin=%s WHERE id=%s"
    valores = (datos["titulo"], datos["institucion"], datos.get("fecha_fin"), id)

    cursor.execute(sql, valores)
    conec.commit()

    cursor.close()
    conec.close()
    return {"mensaje": "Estudio actualizado con éxito", "id": id}, 200


# Eliminar un estudio
@app.route("/api/estudios/<int:id>", methods=["DELETE"])
def eliminar_estudio(id):
    conec = conectar_bd()
    cursor = conec.cursor()

    sql = "DELETE FROM estudios WHERE id = %s"
    cursor.execute(sql, (id,))
    conec.commit()

    cursor.close()
    conec.close()
    return {"mensaje": "Estudio eliminado con éxito", "id": id}, 200


# Consultar experiencias 
@app.route("/api/hojas-vida/<int:id_hv>/experiencias", methods=["GET"])
def obtener_experiencias_hv(id_hv):
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    sql = "SELECT * FROM experiencias WHERE id_hoja_vida = %s"
    cursor.execute(sql, (id_hv,))
    datos = cursor.fetchall()

    columnas = [col[0] for col in cursor.description]
    experiencias = [dict(zip(columnas, fila)) for fila in datos]

    cursor.close()
    conec.close()
    return {"experiencias": experiencias}, 200


# Registrar experiencia 
@app.route("/api/hojas-vida/<int:id_hv>/experiencias", methods=["POST"])
def registrar_experiencia(id_hv):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json

    sql = "INSERT INTO experiencias (empresa, cargo, tiempo, funciones, id_hoja_vida) VALUES (%s, %s, %s, %s, %s)"
    valores = (datos["empresa"], datos["cargo"], datos["tiempo"], datos["funciones"], id_hv)

    cursor.execute(sql, valores)
    conec.commit()
    id_generado = cursor.lastrowid

    cursor.close()
    conec.close()
    return {"mensaje": "Experiencia registrada con éxito", "id": id_generado}, 201


# Consultar experiencia 
@app.route("/api/experiencias/<int:id>", methods=["GET"])
def obtener_experiencia(id):
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    sql = "SELECT * FROM experiencias WHERE id = %s"
    cursor.execute(sql, (id,))
    dato = cursor.fetchone()

    if not dato:
        cursor.close()
        conec.close()
        return {"mensaje": "Experiencia no encontrada"}, 404

    columnas = [col[0] for col in cursor.description]
    experiencia = dict(zip(columnas, dato))

    cursor.close()
    conec.close()
    return {"experiencia": experiencia}, 200


# Actualizar experiencia
@app.route("/api/experiencias/<int:id>", methods=["PUT"])
def actualizar_experiencia(id):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json

    sql = "UPDATE experiencias SET empresa=%s, cargo=%s, tiempo=%s, funciones=%s WHERE id=%s"
    valores = (datos["empresa"], datos["cargo"], datos["tiempo"], datos["funciones"], id)

    cursor.execute(sql, valores)
    conec.commit()

    cursor.close()
    conec.close()
    return {"mensaje": "Experiencia actualizada con éxito", "id": id}, 200


# Eliminar experiencia
@app.route("/api/experiencias/<int:id>", methods=["DELETE"])
def eliminar_experiencia(id):
    conec = conectar_bd()
    cursor = conec.cursor()

    sql = "DELETE FROM experiencias WHERE id = %s"
    cursor.execute(sql, (id,))
    conec.commit()

    cursor.close()
    conec.close()
    return {"mensaje": "Experiencia eliminada con éxito", "id": id}, 200


if __name__ == "__main__":
    app.run(debug=True)