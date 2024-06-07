from abc import ABC, abstractmethod

from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# region Configurações
app.secret_key = '4N4K1N5KYW4LK3R'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///curriculo.sqlite3'
db = SQLAlchemy(app)
app.app_context().push()


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


class CurriculoBuilder:
    def __init__(self, usuario_id):
        self.usuario_id = usuario_id
        self.dados_pessoais = None
        self.formacoes = []
        self.experiencias = []
        self.habilidades = []

    def add_dados_pessoais(self, nome, email, titulo, objetivo, endereco, site, telefone):
        self.dados_pessoais = DadosPessoais(nome, email, titulo, objetivo, endereco, site, telefone, self.usuario_id)s

    def add_formacao(self, curso, instituicao, data, descricao):
        formacao = Formacao(curso, instituicao, data, descricao, self.usuario_id)
        self.formacoes.append(formacao)

    def add_experiencia(self, cargo, empresa, data, descricao):
        experiencia = Experiencia(cargo, empresa, data, descricao, self.usuario_id)
        self.experiencias.append(experiencia)

    def add_habilidade(self, nome):
        habilidade = Habilidade(nome, self.usuario_id)
        self.habilidades.append(habilidade)

    def build(self):
        return {
            'dados_pessoais': self.dados_pessoais,
            'formacoes': self.formacoes,
            'experiencias': self.experiencias,
            'habilidades': self.habilidades
        }
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
    if request.method == 'GET':
        if 'usuario' not in session:
            return render_template('index.html', mensagem='Você não está logado. Acesso direto não é permitido.',
                                   tipo='danger')
        else:
            usuario = Usuario.query.filter_by(email=session['usuario']).first()
            dadospessoais = DadosPessoais.query.filter_by(usuario_id=usuario.id).first()
            formacao = Formacao.query.filter_by(usuario_id=usuario.id).order_by(Formacao.data.desc()).all()
            experiencia = Experiencia.query.filter_by(usuario_id=usuario.id).order_by(Experiencia.data.desc()).all()
            habilidade = Habilidade.query.filter_by(usuario_id=usuario.id).all()
            return render_template('curriculo.html', usuario=usuario, dadospessoais=dadospessoais, formacao=formacao, experiencia=experiencia, habilidade=habilidade)


@app.route('/add_dadospessoais', methods=['GET', 'POST'])
def add_dadospessoais():
    # Verifica se o usuário está logado
    if 'usuario' not in session:
        return render_template('index.html', mensagem='Você não está logado.', tipo='danger')

    # Verifica se o método é GET
    if request.method == 'GET':
        return redirect('/')

    # Consulta o usuário logado e cria um CurriculoBuilder(função que monta o currículo)
    usuario = Usuario.query.filter_by(email=session['usuario']).first()
    curriculo_builder = CurriculoBuilder(usuario.id)
    curriculo_builder.set_dados_pessoais(request.form.get('nome'), request.form.get('email'), request.form.get('titulo'), request.form.get('objetivo'),
                                         request.form.get('endereco'), request.form.get('site'), request.form.get('telefone'))
    dados_pessoais, _, _, _ = curriculo_builder.build()
    dados_pessoais_existente = DadosPessoais.query.filter_by(usuario_id=usuario.id).first()
    if dados_pessoais_existente:
        dados_pessoais_existente.nome = dados_pessoais.nome
        dados_pessoais_existente.email = dados_pessoais.email
        dados_pessoais_existente.titulo = dados_pessoais.titulo
        dados_pessoais_existente.objetivo = dados_pessoais.objetivo
        dados_pessoais_existente.endereco = dados_pessoais.endereco
        dados_pessoais_existente.site = dados_pessoais.site
        dados_pessoais_existente.telefone = dados_pessoais.telefone
    else:
        db.session.add(dados_pessoais)
    db.session.commit()

    return redirect('/')


@app.route('/add_formacao', methods=['GET', 'POST'])
def add_formacao():
    if request.method == 'GET':
        if 'usuario' not in session:
            return render_template('index.html', mensagem='Você não está logado. Acesso direto não permitido.', tipo='danger')
        else:
            return redirect('/')

    if request.method == 'POST':
        if 'usuario' not in session:
            return render_template('index.html', mensagem='Você não está logado. Acesso direto não permitido.', tipo='danger')

        usuario = Usuario.query.filter_by(email=session['usuario']).first()
        curriculo_builder = CurriculoBuilder(usuario.id)
        curriculo_builder.add_formacao(
            request.form['curso'],
            request.form['instituicao'],
            request.form['data'],
            request.form['descricao']
        )
        _, formacoes, _, _ = curriculo_builder.build()

        id = request.form.get('id')
        if id:
            formacao = Formacao.query.filter_by(id=id).first()
            formacao.curso = formacoes[0].curso
            formacao.instituicao = formacoes[0].instituicao
            formacao.data = formacoes[0].data
            formacao.descricao = formacoes[0].descricao
            db.session.commit()
        else:
            db.session.add(formacoes[0])
            db.session.commit()
        return redirect('/')
    return render_template('index.html')


@app.route('/add_experiencia', methods=['GET', 'POST'])
def add_experiencia():
    if request.method == 'GET':
        if 'usuario' not in session:
            return render_template('index.html', mensagem='Você não está logado. Acesso direto não permitido.', tipo='danger')
        else:
            return redirect('/')

    if request.method == 'POST':
        if 'usuario' not in session:
            return render_template('index.html', mensagem='Você não está logado. Acesso direto não permitido.', tipo='danger')

        usuario = Usuario.query.filter_by(email=session['usuario']).first()
        curriculo_builder = CurriculoBuilder(usuario.id)
        curriculo_builder.add_experiencia(
            request.form['cargo'],
            request.form['empresa'],
            request.form['data'],
            request.form['descricao']
        )
        _, _, experiencias, _ = curriculo_builder.build()

        id = request.form.get('id')
        if id:
            experiencia = Experiencia.query.filter_by(id=id).first()
            experiencia.cargo = experiencias[0].cargo
            experiencia.empresa = experiencias[0].empresa
            experiencia.data = experiencias[0].data
            experiencia.descricao = experiencias[0].descricao
            db.session.commit()
        else:
            db.session.add(experiencias[0])
            db.session.commit()
        return redirect('/')
    return render_template('index.html')


@app.route('/add_habilidade', methods=['GET', 'POST'])
def add_habilidade():
    if request.method == 'GET':
        if 'usuario' not in session:
            return render_template('index.html', mensagem='Você não está logado. Acesso direto não permitido.', tipo='danger')
        else:
            return redirect('/')

    if request.method == 'POST':
        if 'usuario' not in session:
            return render_template('index.html', mensagem='Você não está logado. Acesso direto não permitido.', tipo='danger')

        usuario = Usuario.query.filter_by(email=session['usuario']).first()
        curriculo_builder = CurriculoBuilder(usuario.id)
        curriculo_builder.add_habilidade(request.form['nome'])
        _, _, _, habilidades = curriculo_builder.build()

        db.session.add(habilidades[0])
        db.session.commit()
        return redirect('/')
    return render_template('index.html')


@app.route('/delete_experiencia/<id>', methods=['GET', 'POST'])
def delete_experiencia(id):
    experiencia = Experiencia.query.filter_by(id=id).first()
    db.session.delete(experiencia)
    db.session.commit()
    return redirect('/')


@app.route('/delete_formacao/<id>', methods=['GET', 'POST'])
def delete_formacao(id):
    formacao = Formacao.query.filter_by(id=id).first()
    db.session.delete(formacao)
    db.session.commit()
    return redirect('/')


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
        return render_template('index.html')
    elif 'usuario' not in session:
        return render_template('index.html',
                               mensagem='Você não está logado. Acesso direto não é permitido.',
                               tipo='danger')


# endregion

# endregion

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
