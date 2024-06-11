from abc import abstractmethod, ABC
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import datetime

app = Flask(__name__)

# region Configurações
app.secret_key = '4N4K1N5KYW4LK3R'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///curriculo.sqlite3'
app.app_context().push()
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=10)


# endregion

# region  Padrão de Projeto Criacional - Singleton para o BD
class Database:
    _instance = None

    def __new__(cls, app):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.db = SQLAlchemy(app)
        return cls._instance


# Criação da instância do banco de dados usando Singleton
db = Database(app).db


# endregion

# region Models
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)

    def __init__(self, email, senha):
        self.email = email
        self.senha = senha


class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

    def __init__(self, usuario_id):
        self.usuario_id = usuario_id


class DadosPessoais(BaseModel, db.Model):
    nome = db.Column(db.String(100))
    email = db.Column(db.String(100))
    titulo = db.Column(db.String(100))
    objetivo = db.Column(db.String(500))
    endereco = db.Column(db.String(200))
    site = db.Column(db.String(100))
    telefone = db.Column(db.String(20))

    def __init__(self, nome, email, titulo, objetivo, endereco, site, telefone, usuario_id):
        super().__init__(usuario_id)
        self.nome = nome
        self.email = email
        self.titulo = titulo
        self.objetivo = objetivo
        self.endereco = endereco
        self.site = site
        self.telefone = telefone


class Formacao(BaseModel, db.Model):
    curso = db.Column(db.String(100))
    instituicao = db.Column(db.String(100))
    data = db.Column(db.String(20))
    descricao = db.Column(db.String(500))

    def __init__(self, curso, instituicao, data, descricao, usuario_id):
        super().__init__(usuario_id)
        self.curso = curso
        self.instituicao = instituicao
        self.data = data
        self.descricao = descricao


class Experiencia(BaseModel, db.Model):
    cargo = db.Column(db.String(100))
    empresa = db.Column(db.String(100))
    data = db.Column(db.String(20))
    descricao = db.Column(db.String(500))

    def __init__(self, cargo, empresa, data, descricao, usuario_id):
        super().__init__(usuario_id)
        self.cargo = cargo
        self.empresa = empresa
        self.data = data
        self.descricao = descricao


class Habilidade(BaseModel, db.Model):
    nome = db.Column(db.String(100))

    def __init__(self, nome, usuario_id):
        super().__init__(usuario_id)
        self.nome = nome


# endregion

# region Padrão de Projeto Estrutural - Decorator
class Curriculo:
    def __init__(self, dadospessoais, formacao, experiencia, habilidade):
        self.dadospessoais = dadospessoais
        self.formacao = formacao
        self.experiencia = experiencia
        self.habilidade = habilidade

    def render(self):
        return render_template('curriculo.html', dadospessoais=self.dadospessoais, formacao=self.formacao, experiencia=self.experiencia,
                               habilidade=self.habilidade)


class CurriculoDecorator(Curriculo):
    def __init__(self, curriculo):
        self.curriculo = curriculo

    def render(self):
        return self.curriculo.render()


class ColorDecorator(CurriculoDecorator):
    def __init__(self, curriculo, color):
        super().__init__(curriculo)
        self.color = color

    def render(self):
        rendered = super().render()
        return rendered + f"<div style='color: {self.color};'>{super().render()}</div>"


class FontDecorator(CurriculoDecorator):
    def __init__(self, curriculo, font):
        super().__init__(curriculo)
        self.font = font

    def render(self):
        rendered = super().render()
        return rendered + f"<div style='font-family: {self.font};'>{super().render()}</div>"


class SizeDecorator(CurriculoDecorator):
    def __init__(self, curriculo, size):
        super().__init__(curriculo)
        self.size = size

    def render(self):
        rendered = super().render()
        return rendered + f"<div style='font-size: {self.size};'>{super().render()}</div>"

# endregion

# region Banco de Dados
with app.app_context():
    db.create_all()
    db.session.commit()


# endregion

# region Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        if 'usuario' in session:
            usuario = Usuario.query.filter_by(email=session['usuario']).first()
            dadospessoais = DadosPessoais.query.filter_by(usuario_id=usuario.id).first()
            formacao = Formacao.query.filter_by(usuario_id=usuario.id).order_by(Formacao.data.desc()).all()
            experiencia = Experiencia.query.filter_by(usuario_id=usuario.id).order_by(Experiencia.data.desc()).all()
            habilidade = Habilidade.query.filter_by(usuario_id=usuario.id).all()
            return render_template('index.html', usuario=usuario, dadospessoais=dadospessoais, formacao=formacao, experiencia=experiencia, habilidade=habilidade)
        return render_template('index.html')


@app.route('/curriculo', methods=['GET', 'POST'])
def curriculo():
    # Verifica se a sessão de customizações existe, se não, cria uma nova com os valores padrão
    if 'customizations' not in session:
        session['customizations'] = [
            ('color', '#000000'),
            ('font', 'Times New Roman, sans-serif'),
            ('size', '16px')
        ]

    # Recupera o usuário logado
    usuario = Usuario.query.filter_by(email=session['usuario']).first()
    dadospessoais = DadosPessoais.query.filter_by(usuario_id=usuario.id).first()
    formacao = Formacao.query.filter_by(usuario_id=usuario.id).order_by(Formacao.data.desc()).all()
    experiencia = Experiencia.query.filter_by(usuario_id=usuario.id).order_by(Experiencia.data.desc()).all()
    habilidade = Habilidade.query.filter_by(usuario_id=usuario.id).all()
    
    # Cria o currículo
    curriculo = Curriculo(dadospessoais, formacao, experiencia, habilidade)

    return render_template('curriculo.html', usuario=usuario, dadospessoais=dadospessoais, formacao=formacao, experiencia=experiencia, habilidade=habilidade,
                           scustomizations=session['customizations'])


@app.route('/customizacao/<tipo>', methods=['GET', 'POST'])
def customizacao(tipo):
    if 'customizations' not in session:
        session['customizations'] = []

    # Adiciona a customização na sessão de acordo com o tipo, mas não permite duplicidade de customizações
    if tipo == 'color':
        session['customizations'] = [custom for custom in session['customizations'] if custom[0] != 'color']
        session['customizations'].append(('color', request.form['color']))
    elif tipo == 'font':
        session['customizations'] = [custom for custom in session['customizations'] if custom[0] != 'font']
        session['customizations'].append(('font', request.form['font']))
    elif tipo == 'size':
        session['customizations'] = [custom for custom in session['customizations'] if custom[0] != 'size']
        session['customizations'].append(('size', request.form['size']))

    # Marca a sessão como modificada para que as alterações sejam salvas
    session.modified = True

    # caso teste
    print(session['customizations'])

    # Redireciona para a página inicial
    return redirect('/')


@app.route('/reset_customizacao', methods=['POST'])
def reset_customizacao():
    # Remove as customizações da sessão
    session.pop('customizations', None)
    return redirect('/')


@app.route('/add_dadospessoais', methods=['GET', 'POST'])
def add_dadospessoais():
    if request.method == 'GET':
        if 'usuario' not in session:
            return render_template('index.html', mensagem='Você não está logado.', tipo='danger')
        else:
            return redirect('/')

    if request.method == 'POST':
        if 'usuario' not in session:
            return render_template('index.html', mensagem='Você não está logado.', tipo='danger')
        else:
            # Recupera o usuário logado
            usuario = Usuario.query.filter_by(email=session['usuario']).first()

            # Adiciona os dados pessoais do usuário
            nome = request.form['nome']
            email = request.form['email']
            titulo = request.form['titulo']
            objetivo = request.form['objetivo']
            endereco = request.form['endereco']
            site = request.form['site']
            telefone = request.form['telefone']

            # Verifica se o usuário já possui dados pessoais cadastrados
            dadospessoais = DadosPessoais.query.filter_by(usuario_id=usuario.id).first()

            # Se existente, atualiza os dados e evita duplicidade
            if dadospessoais:
                dadospessoais.nome = nome
                dadospessoais.email = email
                dadospessoais.titulo = titulo
                dadospessoais.objetivo = objetivo
                dadospessoais.endereco = endereco
                dadospessoais.site = site
                dadospessoais.telefone = telefone
                db.session.commit()

            # Senão, cria um novo registro
            else:
                dadospessoais = DadosPessoais(nome, email, titulo, objetivo, endereco, site, telefone, usuario.id)
                db.session.add(dadospessoais)
                db.session.commit()

            return redirect('/')

        return render_template('index.html')


@app.route('/add_experiencia', methods=['GET', 'POST'])
def add_experiencia():
    if request.method == 'GET':
        if 'usuario' not in session:
            return render_template('index.html', mensagem='Você não está logado. Acesso direto não permitido.',
                                   tipo='danger')
        else:
            return redirect('/')

    if request.method == 'POST':
        if 'usuario' not in session:
            return render_template('index.html', mensagem='Você não está logado. Acesso direto não permitido.',
                                   tipo='danger')

        elif 'usuario' in session:
            # Recupera o usuário logado
            usuario = Usuario.query.filter_by(email=session['usuario']).first()

            # Adiciona a experiência do usuário
            id = request.form.get('id')
            cargo = request.form['cargo']
            empresa = request.form['empresa']
            data = request.form['data']
            descricao = request.form['descricao']

            # Verifica se a experiência já existe pelo id
            if id:
                experiencia = Experiencia.query.filter_by(id=id).first()
                experiencia.cargo = cargo
                experiencia.empresa = empresa
                experiencia.data = data
                experiencia.descricao = descricao
                db.session.commit()
                return redirect('/')
            else:
                experiencia = Experiencia(cargo, empresa, data, descricao, usuario.id)
                db.session.add(experiencia)
                db.session.commit()
                return redirect('/')
        return render_template('index.html')


@app.route('/delete_experiencia/<id>', methods=['GET', 'POST'])
def delete_experiencia(id):
    experiencia = Experiencia.query.filter_by(id=id).first()
    db.session.delete(experiencia)
    db.session.commit()
    return redirect('/')


@app.route('/add_formacao', methods=['GET', 'POST'])
def add_formacao():
    if request.method == 'GET':
        if 'usuario' not in session:
            return render_template('index.html', mensagem='Você não está logado. Acesso direto não permitido.',
                                   tipo='danger')
        else:
            return redirect('/')

    if request.method == 'POST':
        if 'usuario' not in session:
            return render_template('index.html', mensagem='Você não está logado. Acesso direto não permitido.',
                                   tipo='danger')

        elif 'usuario' in session:
            # Recupera o usuário logado
            usuario = Usuario.query.filter_by(email=session['usuario']).first()

            # Adiciona a formação do usuário
            id = request.form.get('id')
            curso = request.form['curso']
            instituicao = request.form['instituicao']
            data = request.form['data']
            descricao = request.form['descricao']

            # Verifica se a formação já existe pelo id
            if id:
                formacao = Formacao.query.filter_by(id=id).first()
                formacao.curso = curso
                formacao.instituicao = instituicao
                formacao.data = data
                formacao.descricao = descricao
                db.session.commit()
                return redirect('/')
            else:
                formacao = Formacao(curso, instituicao, data, descricao, usuario.id)
                db.session.add(formacao)
                db.session.commit()
                return redirect('/')
        return render_template('index.html')


@app.route('/delete_formacao/<id>', methods=['GET', 'POST'])
def delete_formacao(id):
    formacao = Formacao.query.filter_by(id=id).first()
    db.session.delete(formacao)
    db.session.commit()
    return redirect('/')


@app.route('/add_habilidade', methods=['GET', 'POST'])
def add_habilidade():
    if request.method == 'GET':
        if 'usuario' not in session:
            return render_template('index.html', mensagem='Você não está logado. Acesso direto não permitido.',
                                   tipo='danger')
        else:
            return redirect('/')

    if request.method == 'POST':
        if 'usuario' not in session:
            return render_template('index.html', mensagem='Você não está logado. Acesso direto não permitido.',
                                   tipo='danger')

        elif 'usuario' in session:
            # Recupera o usuário logado
            usuario = Usuario.query.filter_by(email=session['usuario']).first()

            # Adiciona a habilidade do usuário
            nome = request.form['nome']

            habilidade = Habilidade(nome, usuario.id)
            db.session.add(habilidade)
            db.session.commit()
            return redirect('/')
        return render_template('index.html')


@app.route('/delete_habilidade/<id>', methods=['GET', 'POST'])
def delete_habilidade(id):
    habilidade = Habilidade.query.filter_by(id=id).first()
    db.session.delete(habilidade)
    db.session.commit()
    return redirect('/')


# region Region Auth
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(email=email, senha=senha).first()
        if usuario:
            session.permanent = False
            session['usuario'] = email
            return render_template('index.html',
                                   mensagem='Login realizado com sucesso.',
                                   tipo='success',
                                   usuario=usuario,
                                   dadospessoais=DadosPessoais.query.filter_by(usuario_id=usuario.id).first(),
                                   formacao=Formacao.query.filter_by(usuario_id=usuario.id).order_by(
                                       Formacao.data.desc()).all(),
                                   experiencia=Experiencia.query.filter_by(usuario_id=usuario.id).order_by(
                                       Experiencia.data.desc()).all(),
                                   habilidade=Habilidade.query.filter_by(usuario_id=usuario.id).all()
                                   )
        else:
            return render_template('index.html',
                                   mensagem='Usuário ou senha inválidos. Por favor, verifique e tente novamente.',
                                   tipo='danger')
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario:
            return render_template('index.html',
                                   mensagem='Esse email já foi cadastrado. Verifique e tente novamente.', tipo='danger')
        else:
            usuario = Usuario(email, senha)
            db.session.add(usuario)
            db.session.commit()
            session['usuario'] = email
            return render_template('index.html', usuario=usuario,
                                   mensagem='Usuário cadastrado com sucesso. Você está logado.', tipo='success')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if 'usuario' in session:
        session.pop('usuario')
        session.clear()
        return render_template('index.html')
    elif 'usuario' not in session:
        return render_template('index.html',
                               mensagem='Você não está logado. Acesso direto não é permitido.',
                               tipo='danger')


# endregion

# endregion

if __name__ == '__main__':
    db.create_all()
    session.clear()
    app.run(debug=True)
