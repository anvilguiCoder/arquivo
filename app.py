from flask import Flask, render_template, request, redirect, session, url_for, flash, send_file
import sqlite3
import os
from dotenv import load_dotenv
import pandas as pd
from fpdf import FPDF
from utils import validar_cpf, validar_data
from datetime import datetime
from werkzeug.security import check_password_hash  # certifique-se de importar isso

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "chave-padrao-insegura")

CAMINHO_BANCO = os.getenv("DB_PATH", os.path.join("dados", "banco.sqlite"))

# --- Funções auxiliares ---
def get_db():
    return sqlite3.connect(CAMINHO_BANCO)

def autenticar_usuario(usuario, senha):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT senha, tipo FROM usuarios WHERE usuario = ?", (usuario,))
    resultado = cursor.fetchone()
    conn.close()

    if resultado:
        senha_hash, tipo = resultado
        if check_password_hash(senha_hash, senha):
            return tipo  # Se a senha estiver correta, retorna o tipo
    return None  # Senha ou usuário inválido

def formatar_data(data):
    try:
        return datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m/%Y')
    except:
        return data

def formatar_cpf(cpf):
    cpf = ''.join(filter(str.isdigit, cpf))
    if len(cpf) == 11:
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    return cpf

# --- Rota 1: Login ---
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        tipo = autenticar_usuario(usuario, senha)

        if not tipo:
            flash('Usuário ou senha inválidos.', 'danger')
            return render_template('login.html')
            
        session['usuario'] = usuario
        session['tipo'] = tipo
        return redirect(url_for('dashboard'))


    return render_template('login.html')

# --- Rota 2: Dashboard (Busca de alunos) ---
@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    # Verifica se a URL contém ?limpar=1
    if request.args.get('limpar') == '1':
        return render_template(
            'dashboard.html',
            usuario=session['usuario'],
            tipo=session['tipo'],
            alunos=[],  # tabela vazia
            ordem='nome',
            direcao='asc',
            nome='',
            data_nascimento='',
            cpf='',
            numero_caixa=''
        )

    alunos = []
    filtros = []
    valores = []

    # Obter parâmetros de filtro
    nome = request.args.get('nome')
    data_nascimento = request.args.get('data_nascimento')
    cpf = request.args.get('cpf')
    numero_caixa = request.args.get('numero_caixa')

    if nome:
        nome = nome.strip()
        if nome:
            filtros.append("nome LIKE ?")
            valores.append(f"%{nome}%")

    if data_nascimento:
        data_nascimento = data_nascimento.strip()
        if data_nascimento:
            try:
                data_sql = datetime.strptime(data_nascimento, '%d/%m/%Y').strftime('%Y-%m-%d')
                filtros.append("data_nascimento = ?")
                valores.append(data_sql)
            except ValueError:
                pass

    if cpf:
        cpf = cpf.strip()
        if cpf:
            filtros.append("cpf = ?")
            valores.append(cpf)

    if numero_caixa:
        numero_caixa = numero_caixa.strip()
        if numero_caixa:
            filtros.append("numero_caixa = ?")
            valores.append(numero_caixa)

    # Ordenação
    ordem = request.args.get('ordem', 'nome')
    direcao = request.args.get('direcao', 'asc')
    if ordem not in ['nome', 'data_nascimento', 'cpf', 'numero_caixa']:
        ordem = 'nome'
    if direcao not in ['asc', 'desc']:
        direcao = 'asc'

    query = "SELECT id, nome, data_nascimento, cpf, numero_caixa FROM alunos"
    if filtros:
        query += " WHERE " + " AND ".join(filtros)
    query += f" ORDER BY {ordem} {direcao}"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, valores)
    alunos = cursor.fetchall()
    conn.close()

    alunos_formatados = [
        (id, nome, formatar_data(nasc), formatar_cpf(cpf), caixa)
        for id, nome, nasc, cpf, caixa in alunos
    ]

    return render_template(
        'dashboard.html',
        usuario=session['usuario'],
        tipo=session['tipo'],
        alunos=alunos_formatados,
        ordem=ordem,
        direcao=direcao,
        nome=nome or '',
        data_nascimento=data_nascimento or '',
        cpf=cpf or '',
        numero_caixa=numero_caixa or ''
    )

# --- Rota 3: Cadastro de Alunos (admin) ---
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastrar():
    if 'usuario' not in session or session['tipo'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        nome = request.form['nome'].strip()
        data_nascimento = request.form['data_nascimento'].strip()
        cpf = request.form['cpf'].strip()
        numero_caixa = request.form['numero_caixa'].strip()

        if not validar_cpf(cpf):
            flash("CPF inválido.", 'warning')
        elif not validar_data(data_nascimento):
            flash("Data de nascimento inválida.", 'warning')
        else:
            try:
                data_convertida = datetime.strptime(data_nascimento, '%d/%m/%Y').strftime('%Y-%m-%d')
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO alunos (nome, data_nascimento, cpf, numero_caixa)
                    VALUES (?, ?, ?, ?)
                """, (nome, data_convertida, cpf, numero_caixa))
                conn.commit()
                flash("Aluno cadastrado com sucesso!", 'success')
                return redirect(url_for('dashboard'))
            except sqlite3.IntegrityError:
                flash("Erro: já existe um aluno com esse CPF.", 'danger')
            finally:
                conn.close()

    return render_template('cadastro.html')

# --- Rota 4: Editar aluno ---
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if 'usuario' not in session or session['tipo'] != 'admin':
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome'].strip()
        data_nascimento = request.form['data_nascimento'].strip()
        cpf = request.form['cpf'].strip()
        numero_caixa = request.form['numero_caixa'].strip()

        try:
            if '-' in data_nascimento:
                data_convertida = data_nascimento
            else:
                data_convertida = datetime.strptime(data_nascimento, '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            flash("Formato de data inválido.", "danger")
            return redirect(request.url)

        cursor.execute("""
            UPDATE alunos SET nome=?, data_nascimento=?, cpf=?, numero_caixa=? WHERE id=?
        """, (nome, data_convertida, cpf, numero_caixa, id))
        conn.commit()
        conn.close()
        flash("Aluno atualizado com sucesso!", "success")
        return redirect(url_for('dashboard'))

    cursor.execute("SELECT * FROM alunos WHERE id=?", (id,))
    aluno = cursor.fetchone()
    conn.close()

    aluno = list(aluno)
    aluno[2] = formatar_data(aluno[2])
    aluno.append(datetime.strptime(aluno[2], '%d/%m/%Y').strftime('%Y-%m-%d'))

    return render_template("editar.html", aluno=aluno)

# --- Rota 5: Excluir aluno ---
@app.route('/excluir/<int:id>', methods=['GET', 'POST'])
def excluir(id):
    if 'usuario' not in session or session['tipo'] != 'admin':
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        cursor.execute("DELETE FROM alunos WHERE id=?", (id,))
        conn.commit()
        conn.close()
        flash("Aluno excluído com sucesso!", "success")
        return redirect(url_for('dashboard'))

    cursor.execute("SELECT * FROM alunos WHERE id=?", (id,))
    aluno = cursor.fetchone()
    conn.close()

    aluno = list(aluno)
    aluno[2] = formatar_data(aluno[2])
    aluno[3] = formatar_cpf(aluno[3])

    return render_template("excluir.html", aluno=aluno)

# --- Rota 6: Exportar Excel ---
@app.route('/exportar/excel')
def exportar_excel():
    filtros = []
    valores = []

    # Obter filtros da URL (GET)
    nome = request.args.get('nome', '').strip()
    data_nascimento = request.args.get('data_nascimento', '').strip()
    cpf = request.args.get('cpf', '').strip()
    numero_caixa = request.args.get('numero_caixa', '').strip()

    # Aplicar filtros
    if nome:
        filtros.append("nome LIKE ?")
        valores.append(f"%{nome}%")

    if data_nascimento:
        try:
            data_sql = datetime.strptime(data_nascimento, '%d/%m/%Y').strftime('%Y-%m-%d')
            filtros.append("data_nascimento = ?")
            valores.append(data_sql)
        except ValueError:
            pass

    if cpf:
        filtros.append("cpf = ?")
        valores.append(cpf)

    if numero_caixa:
        filtros.append("numero_caixa = ?")
        valores.append(numero_caixa)

    # Construir query
    query = "SELECT nome, data_nascimento, cpf, numero_caixa FROM alunos"
    if filtros:
        query += " WHERE " + " AND ".join(filtros)

    # Conectar, buscar e exportar
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, valores)
    dados = cursor.fetchall()
    conn.close()

    # Converter para DataFrame
    df = pd.DataFrame(dados, columns=["nome", "data_nascimento", "cpf", "numero_caixa"])
    df["data_nascimento"] = pd.to_datetime(df["data_nascimento"]).dt.strftime('%d/%m/%Y')
    df["cpf"] = df["cpf"].apply(formatar_cpf)

    # Exportar para Excel
    caminho_excel = os.path.join("dados", "alunos.xlsx")
    df.to_excel(caminho_excel, index=False)

    return send_file(caminho_excel, as_attachment=True)


# --- Rota 7: Exportar PDF com tabela formatada ---
@app.route('/exportar/pdf')
def exportar_pdf():
    from fpdf import FPDF

    class PDFComRodape(FPDF):
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 9)
            self.set_text_color(100, 100, 100)
            self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', align='R')

    # --- Obter filtros e ordenação da URL ---
    nome = request.args.get('nome', '').strip()
    data_nascimento = request.args.get('data_nascimento', '').strip()
    cpf = request.args.get('cpf', '').strip()
    numero_caixa = request.args.get('numero_caixa', '').strip()
    ordem = request.args.get('ordem', 'nome')
    direcao = request.args.get('direcao', 'asc')

    # Sanitizar ordenação
    if ordem not in ['nome', 'data_nascimento', 'cpf', 'numero_caixa']:
        ordem = 'nome'
    if direcao not in ['asc', 'desc']:
        direcao = 'asc'

    # --- Montar filtros SQL ---
    filtros = []
    valores = []

    if nome:
        filtros.append("nome LIKE ?")
        valores.append(f"%{nome}%")
    if data_nascimento:
        try:
            data_sql = datetime.strptime(data_nascimento, '%d/%m/%Y').strftime('%Y-%m-%d')
            filtros.append("data_nascimento = ?")
            valores.append(data_sql)
        except:
            pass
    if cpf:
        filtros.append("cpf = ?")
        valores.append(cpf)
    if numero_caixa:
        filtros.append("numero_caixa = ?")
        valores.append(numero_caixa)

    # --- Query final com filtros e ordenação ---
    query = "SELECT nome, data_nascimento, cpf, numero_caixa FROM alunos"
    if filtros:
        query += " WHERE " + " AND ".join(filtros)
    query += f" ORDER BY {ordem} {direcao}"

    # --- Consulta ao banco ---
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, valores)
    alunos = cursor.fetchall()
    conn.close()

    # --- Gerar PDF ---
    pdf = PDFComRodape()
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Lista de Alunos", ln=True, align='C')
    pdf.ln(8)

    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_draw_color(180, 180, 180)
    pdf.set_line_width(0.4)

    col_widths = [70, 35, 50, 25]
    headers = ["Nome", "Nascimento", "CPF", "Caixa"]
    aligns = ['L', 'C', 'C', 'C']

    for i in range(len(headers)):
        pdf.cell(col_widths[i], 10, headers[i], border=1, align=aligns[i], fill=True)
    pdf.ln()

    pdf.set_font("Arial", '', 11)
    fill = False
    for aluno in alunos:
        nome, nasc, cpf_val, caixa = aluno
        nasc_formatada = formatar_data(nasc)
        cpf_formatado = formatar_cpf(cpf_val)
        dados = [nome, nasc_formatada, cpf_formatado, str(caixa)]

        for i in range(len(dados)):
            pdf.cell(col_widths[i], 10, dados[i], border=1, align=aligns[i], fill=fill)
        pdf.ln()
        fill = not fill

    # --- Salvar PDF ---
    os.makedirs("dados", exist_ok=True)
    caminho_pdf = os.path.join("dados", "alunos.pdf")
    pdf.output(caminho_pdf)

    return send_file(caminho_pdf, as_attachment=True)

# --- Rota 8: Logout ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- Execução ---
if __name__ == '__main__':
    app.run(debug=True)