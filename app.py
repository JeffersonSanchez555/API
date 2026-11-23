from flask import Flask, request, jsonify
from flask_cors import CORS
from database import conectar_bd
from dotenv import load_dotenv
import os
from functools import wraps

load_dotenv()

from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
if not app.config["JWT_SECRET_KEY"]:
    raise RuntimeError("NO SE ENCONTRO LA LLAVE JWT")

jwt = JWTManager(app)
CORS(app)


def rol_requerido(rol):
    def decorador(funcion):
        @wraps(funcion)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()

            if claims.get("rol") != rol:
                return jsonify({"mensaje": "No tiene permiso para acceder"}), 403
            return funcion(*args, **kwargs)
        return wrapper
    return decorador


@app.route("/probar")
def probar_data():
    conec = conectar_bd()
    if conec.is_connected():
        conec.close()
        return {"mensaje": "conexion ok"}


@app.route("/")
def inicio():
    return "Api hoja de vida funcionando"


@app.route("/api/registro-usuario", methods=["POST"])
def registro_usuario():
    datos = request.json or {}

    nombre = datos.get("nombre", "").strip()
    correo = datos.get("correo", "").strip()
    password = datos.get("password", "")
    hoja_vida_id = datos.get("hoja_vida_id")

    if not nombre or not correo or not password:
        return {"error": "Campos vacios"}, 400

    if not (8 <= len(password) <= 15):
        return {"error": "Contrasena debe tener entre 8 y 15 caracteres"}, 400

    conec = conectar_bd()
    cursor = conec.cursor()

    cursor.execute("SELECT id FROM usuarios WHERE nombre = %s OR correo = %s", (nombre, correo))
    if cursor.fetchone():
        cursor.close()
        conec.close()
        return {"error": "Usuario o correo ya registrado"}, 400

    password_encriptada = generate_password_hash(password)

    sql = """INSERT INTO usuarios (nombre, correo, password, rol, estado, hoja_vida_id) 
             VALUES (%s, %s, %s, %s, %s, %s)"""
    valores = (nombre, correo, password_encriptada, 'aprendiz', 1, hoja_vida_id if hoja_vida_id else None)

    cursor.execute(sql, valores)
    conec.commit()

    cursor.close()
    conec.close()

    return {"mensaje": "Usuario registrado exitosamente"}, 201


@app.route("/api/login", methods=["POST"])
def login():
    datos = request.json or {}

    credencial = datos.get("usuario_o_correo", "").strip() or datos.get("correo", "").strip().lower()
    password = datos.get("password", "")

    if not credencial or not password:
        return {"error": "Faltan credenciales"}, 400

    conec = conectar_bd()
    cursor = conec.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE nombre = %s OR correo = %s", (credencial, credencial))
    datos_usuario = cursor.fetchone()

    if not datos_usuario:
        cursor.close()
        conec.close()
        return {"error": "Credenciales incorrectas"}, 401

    columnas = [columna[0] for columna in cursor.description]
    usuario = dict(zip(columnas, datos_usuario))

    cursor.close()
    conec.close()

    if not check_password_hash(usuario["password"], password):
        return {"error": "Credenciales incorrectas"}, 401

    if usuario.get("estado") == 0:
        return {"error": "Usuario inactivo"}, 403

    token = create_access_token(
        identity=str(usuario["id"]),
        additional_claims={"rol": usuario["rol"]}
    )

    return {
        "mensaje": "Inicio de sesion exitoso",
        "token": token,
        "usuario": {
            "id": usuario["id"],
            "nombre": usuario["nombre"],
            "correo": usuario["correo"],
            "rol": usuario["rol"]
        }
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


@app.route("/api/registrohv", methods=["POST"])
@jwt_required()
def registrohvida():
    usuario_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims.get("rol") != "aprendiz":
        return jsonify({"mensaje": "Solo los aprendices pueden registrar HV"}), 403

    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json or {}

    sql_consulta = "SELECT id_hojadvida FROM hojadvida WHERE correo = %s"
    cursor.execute(sql_consulta, (datos.get("correo"),))
    usuario_existente = cursor.fetchone()

    if usuario_existente:
        id_existente = usuario_existente[0]
        cursor.close()
        conec.close()
        return {
            "mensaje": "El usuario ya está registrado con este correo",
            "id_hojadvida": id_existente
        }, 400

    sql = """INSERT INTO hojadvida(usuario_id, nombre, edad, ciudad, correo, fotografia, programa, ficha, jornada) 
             VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"""

    valor = (
        usuario_id,
        datos.get("nombre"),
        datos.get("edad"),
        datos.get("ciudad"),
        datos.get("correo"),
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
@rol_requerido("administrador")
def listar_hojasvida():
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    try:
        cursor.execute("SELECT * FROM hojadvida")
        filas_hv = cursor.fetchall()
        cols_hv = [col[0] for col in cursor.description]

        resultado = []

        for fila_hv in filas_hv:
            hv = dict(zip(cols_hv, fila_hv))
            id_hv = hv["id_hojadvida"]

            # 1. Estudios
            cursor.execute("SELECT * FROM estudios WHERE hojadvida_id = %s", (id_hv,))
            cols_estudios = [col[0] for col in cursor.description]
            estudios = [dict(zip(cols_estudios, fila)) for fila in cursor.fetchall()]

            # 2. Cursos
            cursor.execute("SELECT * FROM cursos WHERE hojadvida_id = %s", (id_hv,))
            cols_cursos = [col[0] for col in cursor.description]
            cursos = [dict(zip(cols_cursos, fila)) for fila in cursor.fetchall()]

            # 3. Experiencias + Habilidades
            cursor.execute("SELECT * FROM experiencias WHERE hojadvida_id = %s", (id_hv,))
            cols_exp = [col[0] for col in cursor.description]
            experiencias = [dict(zip(cols_exp, fila)) for fila in cursor.fetchall()]

            for exp in experiencias:
                cursor.execute("SELECT * FROM habilidades WHERE experiencia_id = %s", (exp["id_exp"],))
                cols_hab = [col[0] for col in cursor.description]
                exp["habilidades"] = [dict(zip(cols_hab, fila)) for fila in cursor.fetchall()]

            resultado.append({
                "datos_personales": hv,
                "estudios": estudios,
                "cursos": cursos,
                "experiencias": experiencias
            })

        return jsonify({
            "total": len(resultado),
            "hojas_vida": resultado
        }), 200

    except Exception as e:
        return jsonify({"error": "Error al consultar las hojas de vida", "detalle": str(e)}), 500

    finally:
        cursor.close()
        conec.close()


# CONSULTAR MI HOJA DE VIDA APRENDIZ
@app.route("/api/mi-hoja-vida", methods=["GET"])
@jwt_required()
def mi_hoja_vida():
    usuario_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims.get("rol") != "aprendiz":
        return jsonify({"mensaje": "Consulta exclusiva para aprendices"}), 403

    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    cursor.execute("SELECT * FROM hojadvida WHERE usuario_id = %s", (usuario_id,))
    dato_hv = cursor.fetchone()

    if not dato_hv:
        cursor.close()
        conec.close()
        return {"mensaje": "Hoja de vida no encontrada para este usuario"}, 404

    cols_hv = [col[0] for col in cursor.description]
    datos_personales = dict(zip(cols_hv, dato_hv))
    id_hv = datos_personales["id_hojadvida"]

    # Estudios
    cursor.execute("SELECT * FROM estudios WHERE hojadvida_id = %s", (id_hv,))
    cols_estudios = [col[0] for col in cursor.description]
    estudios = [dict(zip(cols_estudios, fila)) for fila in cursor.fetchall()]

    # Cursos
    cursor.execute("SELECT * FROM cursos WHERE hojadvida_id = %s", (id_hv,))
    cols_cursos = [col[0] for col in cursor.description]
    cursos = [dict(zip(cols_cursos, fila)) for fila in cursor.fetchall()]

    # Experiencias
    cursor.execute("SELECT * FROM experiencias WHERE hojadvida_id = %s", (id_hv,))
    cols_exp = [col[0] for col in cursor.description]
    experiencias = [dict(zip(cols_exp, fila)) for fila in cursor.fetchall()]

    # Habilidades vinculadas a cada experiencia
    for exp in experiencias:
        cursor.execute("SELECT * FROM habilidades WHERE experiencia_id = %s", (exp["id_exp"],))
        cols_hab = [col[0] for col in cursor.description]
        exp["habilidades"] = [dict(zip(cols_hab, fila)) for fila in cursor.fetchall()]

    cursor.close()
    conec.close()

    return {
        "datos_personales": datos_personales,
        "estudios": estudios,
        "cursos": cursos,
        "experiencias": experiencias
    }, 200


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
    datos = request.json or {}

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
        datos.get("nombre"),
        datos.get("edad"),
        datos.get("ciudad"),
        datos.get("correo"),
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
@jwt_required()
def eliminar_hoja_vida(id):
    usuario_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims.get("rol") != "aprendiz":
        return jsonify({"mensaje": "Solo los aprendices pueden eliminar su hoja de vida"}), 403

    conec = conectar_bd()
    cursor = conec.cursor()

    sql_consulta = "SELECT id_hojadvida FROM hojadvida WHERE id_hojadvida = %s AND usuario_id = %s"
    cursor.execute(sql_consulta, (id, usuario_id))
    hoja_vida = cursor.fetchone()

    if not hoja_vida:
        cursor.close()
        conec.close()
        return jsonify({"mensaje": "Hoja de vida no encontrada o no autorizada"}), 404

    sql = "DELETE FROM hojadvida WHERE id_hojadvida = %s AND usuario_id = %s"
    cursor.execute(sql, (id, usuario_id))
    conec.commit()

    cursor.close()
    conec.close()

    return jsonify({"mensaje": "Hoja de vida eliminada correctamente", "id_hojadvida": id}), 200


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


@app.route("/api/hojas-vida/<int:id_hv>/estudios", methods=["POST"])
def registrar_estudio(id_hv):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json or {}

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


@app.route("/api/estudios/<int:id>", methods=["PUT"])
def actualizar_estudio(id):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json or {}

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


@app.route("/api/hojas-vida/<int:id_hv>/experiencias", methods=["POST"])
def registrar_experiencia(id_hv):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json or {}

    sql = "INSERT INTO experiencias (hojadvida_id, empresa, cargo, tiempo, funciones) VALUES (%s, %s, %s, %s, %s)"
    valores = (
        id_hv,
        datos.get("empresa"),
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


@app.route("/api/experiencias/<int:id>", methods=["PUT"])
def actualizar_experiencia(id):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json or {}

    sql = "UPDATE experiencias SET empresa=%s, cargo=%s, tiempo=%s, funciones=%s WHERE id_exp=%s"
    valores = (
        datos.get("empresa"),
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


@app.route("/api/experiencias/<int:id_exp>/habilidades", methods=["POST"])
@jwt_required()
def registrar_habilidad(id_exp):
    usuario_id = int(get_jwt_identity())
    datos = request.json or {}

    if get_jwt().get("rol") != "aprendiz":
        return jsonify({"mensaje": "No tienes permiso"}), 403

    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    cursor.execute("""
        SELECT e.id_exp 
        FROM experiencias e
        INNER JOIN hojadvida hv ON hv.id_hojadvida = e.hojadvida_id
        WHERE e.id_exp = %s AND hv.usuario_id = %s
    """, (id_exp, usuario_id))

    if not cursor.fetchone():
        cursor.close()
        conec.close()
        return jsonify({"mensaje": "Experiencia no encontrada o no autorizada"}), 404

    sql = "INSERT INTO habilidades (experiencia_id, nombre) VALUES (%s, %s)"
    valores = (id_exp, datos.get("nombre"))

    cursor.execute(sql, valores)
    conec.commit()
    id_generado = cursor.lastrowid

    cursor.close()
    conec.close()
    return {"mensaje": "Habilidad registrada con éxito", "id_habili": id_generado}, 201


@app.route("/api/habilidades/<int:id>", methods=["PUT"])
def actualizar_habilidad(id):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json or {}

    sql = "UPDATE habilidades SET nombre=%s WHERE id_habili=%s"
    valores = (datos.get("nombre"), id)

    cursor.execute(sql, valores)
    conec.commit()

    cursor.close()
    conec.close()
    return {"mensaje": "Habilidad actualizada con éxito", "id_habili": id}, 200


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


@app.route("/api/hojas-vida/<int:id_hv>/cursos", methods=["POST"])
def registrar_curso(id_hv):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json or {}

    sql = "INSERT INTO cursos (hojadvida_id, nombre) VALUES (%s, %s)"
    valores = (id_hv, datos.get("nombre"))

    cursor.execute(sql, valores)
    conec.commit()
    id_generado = cursor.lastrowid

    cursor.close()
    conec.close()
    return {"mensaje": "Curso registrado con éxito", "id_curso": id_generado}, 201


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


@app.route("/api/cursos/<int:id>", methods=["PUT"])
def actualizar_curso(id):
    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.json or {}

    sql = "UPDATE cursos SET nombre=%s WHERE id_curso=%s"
    valores = (datos.get("nombre"), id)

    cursor.execute(sql, valores)
    conec.commit()

    cursor.close()
    conec.close()
    return {"mensaje": "Curso actualizado con éxito", "id_curso": id}, 200


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