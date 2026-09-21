from flask import Flask, request
from database import conectar_bd
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route("/probar")
def probar_data():
    conec = conectar_bd()
    if conec.is_connected():
        conec.close()
        return {"mensaje": "conexion ok"}

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



@app.route("/api/registrohv", methods=["POST"])
def registrohvida():
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json

    sql_consulta = "SELECT id_hojadvida FROM hojadvida WHERE correo = %s"
    cursor.execute(sql_consulta, (datos["correo"],))
    usuario_existente = cursor.fetchone()

    if usuario_existente:
        id_existente = usuario_existente[0]
        cursor.close()
        conec.close()
        return {
            "mensaje": "El usuario ya está registrado con este correo",
            "id_hojadvida": id_existente
        }, 400

    sql = """INSERT INTO hojadvida(nombre, edad, ciudad, correo, fotografia, programa, ficha, jornada) 
             VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"""
    
    valor = (
        datos["nombre"],
        datos.get("edad"),
        datos.get("ciudad"),
        datos["correo"],
        datos.get("fotografia"),
        datos.get("programa"),
        datos.get("ficha"),
        datos.get("jornada")
    )
    
    cursor.execute(sql, valor)
    conec.commit()
    id_generado = cursor.lastrowid

    cursor.close()
    conec.close()

    return {"mensaje": "Hoja de vida registrada con éxito", "id_hojadvida": id_generado}, 201


@app.route("/api/hojasvida", methods=["GET"])
def listar_hojasvida():
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    sql = "SELECT * FROM hojadvida"
    cursor.execute(sql)
    datos = cursor.fetchall()

    columnas = [columna[0] for columna in cursor.description]
    resultado = [dict(zip(columnas, lista)) for lista in datos]

    cursor.close()
    conec.close()

    return {"hojas_vida": resultado}, 200


@app.route("/api/hojas-vida/<int:id>", methods=["GET"])
def obtener_hojasvidaid(id):
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    sql = "SELECT * FROM hojadvida WHERE id_hojadvida = %s"
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

    sql_consulta = "SELECT id_hojadvida FROM hojadvida WHERE id_hojadvida = %s"
    cursor.execute(sql_consulta, (id,))
    hoja_vida = cursor.fetchone()

    if not hoja_vida:
        cursor.close()
        conec.close()
        return {"mensaje": "La hoja de vida no existe para actualizar", "id_hojadvida": id}, 404

    sql_update = """UPDATE hojadvida 
                    SET nombre=%s, edad=%s, ciudad=%s, correo=%s, fotografia=%s, programa=%s, ficha=%s, jornada=%s 
                    WHERE id_hojadvida=%s"""
    
    valores = (
        datos["nombre"],
        datos.get("edad"),
        datos.get("ciudad"),
        datos["correo"],
        datos.get("fotografia"),
        datos.get("programa"),
        datos.get("ficha"),
        datos.get("jornada"),
        id
    )

    cursor.execute(sql_update, valores)
    conec.commit()

    cursor.close()
    conec.close()

    return {"mensaje": "Hoja de vida actualizada con éxito", "id_hojadvida": id}, 200


@app.route("/api/eliminarhv/<int:id>", methods=["DELETE"])
def eliminar_hoja_vida(id):
    conec = conectar_bd()
    cursor = conec.cursor()

    sql_consulta = "SELECT id_hojadvida FROM hojadvida WHERE id_hojadvida = %s"
    cursor.execute(sql_consulta, (id,))
    hoja_vida = cursor.fetchone()

    if not hoja_vida:
        cursor.close()
        conec.close()
        return {"mensaje": "La hoja de vida no existe", "id_hojadvida": id}, 404

    sql = "DELETE FROM hojadvida WHERE id_hojadvida = %s"
    cursor.execute(sql, (id,))
    conec.commit()

    cursor.close()
    conec.close()

    return {"mensaje": "Hoja de vida eliminada correctamente", "id_hojadvida": id}, 200



# ESTUDIOS 


@app.route("/api/hojas-vida/<int:id_hv>/estudios", methods=["GET"])
def obtener_estudios_hv(id_hv):
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    sql = "SELECT * FROM estudios WHERE hojadvida_id = %s"
    cursor.execute(sql, (id_hv,))
    datos = cursor.fetchall()

    columnas = [col[0] for col in cursor.description]
    estudios = [dict(zip(columnas, fila)) for fila in datos]

    cursor.close()
    conec.close()
    return {"estudios": estudios}, 200

#agregar estudio

@app.route("/api/hojas-vida/<int:id_hv>/estudios", methods=["POST"])
def registrar_estudio(id_hv):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json

    sql = "INSERT INTO estudios (hojadvida_id, nivel, institucion, titulo, graduacion) VALUES (%s, %s, %s, %s, %s)"
    valores = (
        id_hv,
        datos.get("nivel"),
        datos.get("institucion"),
        datos.get("titulo"),
        datos.get("graduacion")
    )
    
    cursor.execute(sql, valores)
    conec.commit()
    id_generado = cursor.lastrowid

    cursor.close()
    conec.close()
    return {"mensaje": "Estudio registrado con éxito", "id_estu": id_generado}, 201

#buscar id

@app.route("/api/estudios/<int:id>", methods=["GET"])
def obtener_estudio(id):
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    sql = "SELECT * FROM estudios WHERE id_estu = %s"
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

#actualizar estudio

@app.route("/api/estudios/<int:id>", methods=["PUT"])
def actualizar_estudio(id):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json

    sql = "UPDATE estudios SET nivel=%s, institucion=%s, titulo=%s, graduacion=%s WHERE id_estu=%s"
    valores = (
        datos.get("nivel"),
        datos.get("institucion"),
        datos.get("titulo"),
        datos.get("graduacion"),
        id
    )

    cursor.execute(sql, valores)
    conec.commit()

    cursor.close()
    conec.close()
    return {"mensaje": "Estudio actualizado con éxito", "id_estu": id}, 200


#eliminar estudio

@app.route("/api/estudios/<int:id>", methods=["DELETE"])
def eliminar_estudio(id):
    conec = conectar_bd()
    cursor = conec.cursor()

    sql = "DELETE FROM estudios WHERE id_estu = %s"
    cursor.execute(sql, (id,))
    conec.commit()

    cursor.close()
    conec.close()
    return {"mensaje": "Estudio eliminado con éxito", "id_estu": id}, 200



# EXPERIENCIAS 


@app.route("/api/hojas-vida/<int:id_hv>/experiencias", methods=["GET"])
def obtener_experiencias_hv(id_hv):
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    sql = "SELECT * FROM experiencias WHERE hojadvida_id = %s"
    cursor.execute(sql, (id_hv,))
    datos = cursor.fetchall()

    columnas = [col[0] for col in cursor.description]
    experiencias = [dict(zip(columnas, fila)) for fila in datos]

    cursor.close()
    conec.close()
    return {"experiencias": experiencias}, 200

#agregar experiencia 

@app.route("/api/hojas-vida/<int:id_hv>/experiencias", methods=["POST"])
def registrar_experiencia(id_hv):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json

    sql = "INSERT INTO experiencias (hojadvida_id, empresa, cargo, tiempo, funciones) VALUES (%s, %s, %s, %s, %s)"
    valores = (
        id_hv,
        datos["empresa"],
        datos.get("cargo"),
        datos.get("tiempo"),
        datos.get("funciones")
    )

    cursor.execute(sql, valores)
    conec.commit()
    id_generado = cursor.lastrowid

    cursor.close()
    conec.close()
    return {"mensaje": "Experiencia registrada con éxito", "id_exp": id_generado}, 201

#buscar id

@app.route("/api/experiencias/<int:id>", methods=["GET"])
def obtener_experiencia(id):
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    sql = "SELECT * FROM experiencias WHERE id_exp = %s"
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

# actualizar exp

@app.route("/api/experiencias/<int:id>", methods=["PUT"])
def actualizar_experiencia(id):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json

    sql = "UPDATE experiencias SET empresa=%s, cargo=%s, tiempo=%s, funciones=%s WHERE id_exp=%s"
    valores = (
        datos["empresa"],
        datos.get("cargo"),
        datos.get("tiempo"),
        datos.get("funciones"),
        id
    )

    cursor.execute(sql, valores)
    conec.commit()

    cursor.close()
    conec.close()
    return {"mensaje": "Experiencia actualizada con éxito", "id_exp": id}, 200


@app.route("/api/experiencias/<int:id>", methods=["DELETE"])
def eliminar_experiencia(id):
    conec = conectar_bd()
    cursor = conec.cursor()

    sql = "DELETE FROM experiencias WHERE id_exp = %s"
    cursor.execute(sql, (id,))
    conec.commit()

    cursor.close()
    conec.close()
    return {"mensaje": "Experiencia eliminada con éxito", "id_exp": id}, 200



# HABILIDADES 


@app.route("/api/experiencias/<int:id_exp>/habilidades", methods=["GET"])
def obtener_habilidades_exp(id_exp):
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    sql = "SELECT * FROM habilidades WHERE experiencia_id = %s"
    cursor.execute(sql, (id_exp,))
    datos = cursor.fetchall()

    columnas = [col[0] for col in cursor.description]
    habilidades = [dict(zip(columnas, fila)) for fila in datos]

    cursor.close()
    conec.close()
    return {"habilidades": habilidades}, 200

#agregar

@app.route("/api/experiencias/<int:id_exp>/habilidades", methods=["POST"])
def registrar_habilidad(id_exp):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json

    sql = "INSERT INTO habilidades (experiencia_id, nombre) VALUES (%s, %s)"
    valores = (id_exp, datos["nombre"])

    cursor.execute(sql, valores)
    conec.commit()
    id_generado = cursor.lastrowid

    cursor.close()
    conec.close()
    return {"mensaje": "Habilidad registrada con éxito", "id_habili": id_generado}, 201

#actualizar habi

@app.route("/api/habilidades/<int:id>", methods=["PUT"])
def actualizar_habilidad(id):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json

    sql = "UPDATE habilidades SET nombre=%s WHERE id_habili=%s"
    valores = (datos["nombre"], id)

    cursor.execute(sql, valores)
    conec.commit()

    cursor.close()
    conec.close()
    return {"mensaje": "Habilidad actualizada con éxito", "id_habili": id}, 200

#eliminar habi

@app.route("/api/habilidades/<int:id>", methods=["DELETE"])
def eliminar_habilidad(id):
    conec = conectar_bd()
    cursor = conec.cursor()

    sql = "DELETE FROM habilidades WHERE id_habili = %s"
    cursor.execute(sql, (id,))
    conec.commit()

    cursor.close()
    conec.close()
    return {"mensaje": "Habilidad eliminada con éxito", "id_habili": id}, 200



# CURSOS 


@app.route("/api/hojas-vida/<int:id_hv>/cursos", methods=["GET"])
def obtener_cursos_hv(id_hv):
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    sql = "SELECT * FROM cursos WHERE hojadvida_id = %s"
    cursor.execute(sql, (id_hv,))
    datos = cursor.fetchall()

    columnas = [col[0] for col in cursor.description]
    cursos = [dict(zip(columnas, fila)) for fila in datos]

    cursor.close()
    conec.close()
    return {"cursos": cursos}, 200

#registrar curso

@app.route("/api/hojas-vida/<int:id_hv>/cursos", methods=["POST"])
def registrar_curso(id_hv):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json

    sql = "INSERT INTO cursos (hojadvida_id, nombre) VALUES (%s, %s)"
    valores = (id_hv, datos["nombre"])

    cursor.execute(sql, valores)
    conec.commit()
    id_generado = cursor.lastrowid

    cursor.close()
    conec.close()
    return {"mensaje": "Curso registrado con éxito", "id_curso": id_generado}, 201

#buscar id

@app.route("/api/cursos/<int:id>", methods=["GET"])
def obtener_curso(id):
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    sql = "SELECT * FROM cursos WHERE id_curso = %s"
    cursor.execute(sql, (id,))
    dato = cursor.fetchone()

    if not dato:
        cursor.close()
        conec.close()
        return {"mensaje": "Curso no encontrado"}, 404

    columnas = [col[0] for col in cursor.description]
    curso = dict(zip(columnas, dato))

    cursor.close()
    conec.close()
    return {"curso": curso}, 200

#actualizar curso

@app.route("/api/cursos/<int:id>", methods=["PUT"])
def actualizar_curso(id):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json

    sql = "UPDATE cursos SET nombre=%s WHERE id_curso=%s"
    valores = (datos["nombre"], id)

    cursor.execute(sql, valores)
    conec.commit()

    cursor.close()
    conec.close()
    return {"mensaje": "Curso actualizado con éxito", "id_curso": id}, 200

#eliminar 

@app.route("/api/cursos/<int:id>", methods=["DELETE"])
def eliminar_curso(id):
    conec = conectar_bd()
    cursor = conec.cursor()

    sql = "DELETE FROM cursos WHERE id_curso = %s"
    cursor.execute(sql, (id,))
    conec.commit()

    cursor.close()
    conec.close()
    return {"mensaje": "Curso eliminado con éxito", "id_curso": id}, 200


# CONSULTA COMPLETA


@app.route("/api/hojas-vida/<int:id_hv>/completa", methods=["GET"])
def obtener_hoja_vida_completa(id_hv):
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    # 1. Datos personales
    cursor.execute("SELECT * FROM hojadvida WHERE id_hojadvida = %s", (id_hv,))
    dato_hv = cursor.fetchone()
    if not dato_hv:
        cursor.close()
        conec.close()
        return {"mensaje": "Hoja de vida no encontrada"}, 404

    cols_hv = [col[0] for col in cursor.description]
    datos_personales = dict(zip(cols_hv, dato_hv))

    # 2. Estudios
    cursor.execute("SELECT * FROM estudios WHERE hojadvida_id = %s", (id_hv,))
    cols_estudios = [col[0] for col in cursor.description]
    estudios = [dict(zip(cols_estudios, fila)) for fila in cursor.fetchall()]

    # 3. Cursos
    cursor.execute("SELECT * FROM cursos WHERE hojadvida_id = %s", (id_hv,))
    cols_cursos = [col[0] for col in cursor.description]
    cursos = [dict(zip(cols_cursos, fila)) for fila in cursor.fetchall()]

    # 4. Experiencias y sus Habilidades
    cursor.execute("SELECT * FROM experiencias WHERE hojadvida_id = %s", (id_hv,))
    cols_exp = [col[0] for col in cursor.description]
    experiencias = [dict(zip(cols_exp, fila)) for fila in cursor.fetchall()]

    for exp in experiencias:
        cursor.execute("SELECT * FROM habilidades WHERE experiencia_id = %s", (exp["id_exp"],))
        cols_hab = [col[0] for col in cursor.description]
        exp["habilidades"] = [dict(zip(cols_hab, fila)) for fila in cursor.fetchall()]

    cursor.close()
    conec.close()

    return {
        "datos_personales": datos_personales,
        "informacion_academica": estudios,
        "cursos": cursos,
        "experiencia_laboral": experiencias
    }, 200


if __name__ == "__main__":
    app.run(debug=True)