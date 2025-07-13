from flask import Flask, render_template, request, redirect, session, url_for, flash, send_file
import os
from dotenv import load_dotenv
import pandas as pd
from utils import validar_cpf, validar_data
from datetime import datetime
from werkzeug.security import check_password_hash
from db import get_db

load_dotenv()

from inicializar import criar_tabelas, inicializar_admin
criar_tabelas()
inicializar_admin()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "chave-padrao-insegura")

# --- Funções auxiliares ---
def autenticar_usuario(usuario, senha):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT senha, tipo FROM usuarios WHERE usuario = %s", (usuario,))
    resultado = cursor.fetchone()
    conn.close()

    if resultado:
        senha_hash = resultado["senha"] if isinstance(resultado, dict) else resultado[0]
        tipo = resultado["tipo"] if isinstance(resultado, dict) else resultado[1]
        if check_password_hash(senha_hash, senha):
            return tipo
    return None

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

        # ✅ Redireciona com campos limpos no dashboard
        return redirect(url_for('dashboard', limpar=1))

    return render_template('login.html')

# --- Rota 2: Dadhboard ---
@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if request.args.get('limpar') == '1':
        return render_template(
            'dashboard.html',
            usuario=session['usuario'],
            tipo=session['tipo'],
            alunos=[],
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

    # Corrigir: nome_busca para não ser sobrescrito
    nome_busca = request.args.get('nome')
    data_nascimento = request.args.get('data_nascimento')
    cpf = request.args.get('cpf')
    numero_caixa = request.args.get('numero_caixa')

    if nome_busca:
        nome_busca = nome_busca.strip()
        if nome_busca:
            filtros.append("nome ILIKE %s")
            valores.append(f"%{nome_busca}%")

    if data_nascimento:
        data_nascimento = data_nascimento.strip()
        if data_nascimento:
            try:
                data_sql = datetime.strptime(data_nascimento, '%d/%m/%Y').strftime('%Y-%m-%d')
                filtros.append("data_nascimento = %s")
                valores.append(data_sql)
            except ValueError:
                pass

    if cpf:
        cpf = cpf.strip()
        if cpf:
            filtros.append("cpf = %s")
            valores.append(cpf)

    if numero_caixa:
        numero_caixa = numero_caixa.strip()
        if numero_caixa:
            filtros.append("numero_caixa = %s")
            valores.append(numero_caixa)

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

    alunos_formatados = []
    for aluno in alunos:
        try:
            if isinstance(aluno, dict):
                id = aluno['id']
                nome = aluno['nome']
                nasc = aluno['data_nascimento']
                cpf_val = aluno['cpf']
                caixa = aluno['numero_caixa']
            else:
                id, nome, nasc, cpf_val, caixa = aluno

            alunos_formatados.append((
                id,
                nome,
                formatar_data(nasc),
                formatar_cpf(cpf_val),
                caixa
            ))
        except Exception as e:
            print("[ERRO formatando aluno]", e)

    return render_template(
        'dashboard.html',
        usuario=session['usuario'],
        tipo=session['tipo'],
        alunos=alunos_formatados,
        ordem=ordem,
        direcao=direcao,
        nome=nome_busca or '',
        data_nascimento=data_nascimento or '',
        cpf=cpf or '',
        numero_caixa=numero_caixa or ''
    )

# --- Rota 3: Cadastro de Alunos ---
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
                    VALUES (%s, %s, %s, %s)
                """, (nome, data_convertida, cpf, numero_caixa))
                conn.commit()
                flash("Aluno cadastrado com sucesso!", 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                if "duplicate key value" in str(e):
                    flash("Erro: já existe um aluno com esse CPF.", 'danger')
                else:
                    flash("Erro ao cadastrar aluno.", 'danger')
                print("[ERRO]", e)
            finally:
                conn.close()

    return render_template('cadastro.html')

# --- Rota 4: Editar ---
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
            UPDATE alunos
            SET nome = %s, data_nascimento = %s, cpf = %s, numero_caixa = %s
            WHERE id = %s
        """, (nome, data_convertida, cpf, numero_caixa, id))
        conn.commit()
        conn.close()
        flash("Aluno atualizado com sucesso!", "success")
        return redirect(url_for('dashboard'))

    cursor.execute("SELECT * FROM alunos WHERE id = %s", (id,))
    aluno = cursor.fetchone()
    conn.close()

    if not aluno:
        flash("Aluno não encontrado.", "warning")
        return redirect(url_for('dashboard'))

    aluno = list(aluno.values())
    aluno[2] = formatar_data(aluno[2])
    aluno.append(datetime.strptime(aluno[2], '%d/%m/%Y').strftime('%Y-%m-%d'))

    return render_template("editar.html", aluno=aluno)

# --- Rota 5: Excluir ---
@app.route('/excluir/<int:id>', methods=['GET', 'POST'])
def excluir(id):
    if 'usuario' not in session or session['tipo'] != 'admin':
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        cursor.execute("DELETE FROM alunos WHERE id = %s", (id,))
        conn.commit()
        conn.close()
        flash("Aluno excluído com sucesso!", "success")
        return redirect(url_for('dashboard'))

    cursor.execute("SELECT * FROM alunos WHERE id = %s", (id,))
    aluno = cursor.fetchone()
    conn.close()

    if not aluno:
        flash("Aluno não encontrado.", "warning")
        return redirect(url_for('dashboard'))

    aluno = list(aluno.values())
    aluno[2] = formatar_data(aluno[2])
    aluno[3] = formatar_cpf(aluno[3])

    return render_template("excluir.html", aluno=aluno)

# --- Rota 6: Exportar Excel ---
# --- Rota 6: Exportar Excel ---
@app.route('/exportar/excel')
def exportar_excel():
    from psycopg2.extras import RealDictCursor

    filtros = []
    valores = []

    # Obter filtros da URL (GET)
    nome = request.args.get('nome', '').strip()
    data_nascimento = request.args.get('data_nascimento', '').strip()
    cpf = request.args.get('cpf', '').strip()
    numero_caixa = request.args.get('numero_caixa', '').strip()

    # Aplicar filtros
    if nome:
        filtros.append("nome ILIKE %s")
        valores.append(f"%{nome}%")

    if data_nascimento:
        try:
            data_sql = datetime.strptime(data_nascimento, '%d/%m/%Y').strftime('%Y-%m-%d')
            filtros.append("data_nascimento = %s")
            valores.append(data_sql)
        except ValueError:
            pass

    if cpf:
        filtros.append("cpf = %s")
        valores.append(cpf)

    if numero_caixa:
        filtros.append("numero_caixa = %s")
        valores.append(numero_caixa)

    # Construir query
    query = "SELECT nome, data_nascimento, cpf, numero_caixa FROM alunos"
    if filtros:
        query += " WHERE " + " AND ".join(filtros)

    # Conectar ao banco e buscar dados com nomes das colunas
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(query, valores)
    dados = cursor.fetchall()
    conn.close()

    # Converter para DataFrame
    df = pd.DataFrame(dados)

    if not df.empty:
        df["data_nascimento"] = pd.to_datetime(df["data_nascimento"]).dt.strftime('%d/%m/%Y')
        df["cpf"] = df["cpf"].apply(formatar_cpf)

    # Salvar como Excel
    os.makedirs("dados", exist_ok=True)
    caminho_excel = os.path.join("dados", "alunos.xlsx")
    df.to_excel(caminho_excel, index=False)

    return send_file(caminho_excel, as_attachment=True)

# --- Rota 7: Exportar PDF com tabela formatada ---
@app.route('/exportar/pdf')
def exportar_pdf():
    from fpdf import FPDF
    from psycopg2.extras import RealDictCursor

    class PDFComRodape(FPDF):
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 9)
            self.set_text_color(100, 100, 100)
            self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', align='R')

    nome = request.args.get('nome', '').strip()
    data_nascimento = request.args.get('data_nascimento', '').strip()
    cpf = request.args.get('cpf', '').strip()
    numero_caixa = request.args.get('numero_caixa', '').strip()
    ordem = request.args.get('ordem', 'nome')
    direcao = request.args.get('direcao', 'asc')

    if ordem not in ['nome', 'data_nascimento', 'cpf', 'numero_caixa']:
        ordem = 'nome'
    if direcao not in ['asc', 'desc']:
        direcao = 'asc'

    filtros = []
    valores = []

    if nome:
        filtros.append("nome ILIKE %s")
        valores.append(f"%{nome}%")
    if data_nascimento:
        try:
            data_sql = datetime.strptime(data_nascimento, '%d/%m/%Y').strftime('%Y-%m-%d')
            filtros.append("data_nascimento = %s")
            valores.append(data_sql)
        except:
            pass
    if cpf:
        filtros.append("cpf = %s")
        valores.append(cpf)
    if numero_caixa:
        filtros.append("numero_caixa = %s")
        valores.append(numero_caixa)

    query = "SELECT nome, data_nascimento, cpf, numero_caixa FROM alunos"
    if filtros:
        query += " WHERE " + " AND ".join(filtros)
    query += f" ORDER BY {ordem} {direcao}"

    # PostgreSQL: usar RealDictCursor
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(query, valores)
    alunos = cursor.fetchall()
    conn.close()

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
        nome = aluno['nome'] or ''
        nasc = formatar_data(aluno['data_nascimento']) if aluno['data_nascimento'] else ''
        cpf_val = formatar_cpf(aluno['cpf']) if aluno['cpf'] else ''
        caixa = str(aluno['numero_caixa']) if aluno['numero_caixa'] else ''

        dados = [nome, nasc, cpf_val, caixa]
        for i in range(len(dados)):
            pdf.cell(col_widths[i], 10, dados[i], border=1, align=aligns[i], fill=fill)
        pdf.ln()
        fill = not fill

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
