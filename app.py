from flask import Flask, render_template, request, session
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
    id = db.Column('id', db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True)
    senha = db.Column(db.String(20))

    def __init__(self, email, senha):
        self.email = email
        self.senha = senha


class DadosPessoais(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    nome = db.Column(db.String(128))
    titulo = db.Column(db.String(128))
    objetivo = db.Column(db.String(512))
    endereco = db.Column(db.String(128))
    site = db.Column(db.String(128))
    telefone = db.Column(db.String(128))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    usuario = db.relationship('Usuario', foreign_keys=usuario_id)

    def __init__(self, nome, titulo, objetivo, endereco, site, telefone, usuario_id):
        self.nome = nome
        self.titulo = titulo
        self.objetivo = objetivo
        self.endereco = endereco
        self.site = site
        self.telefone = telefone
        self.usuario_id = usuario_id


class Formacao(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    curso = db.Column(db.String(128))
    instituicao = db.Column(db.String(128))
    data = db.Column(db.String(128))
    descricao = db.Column(db.String(512))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    usuario = db.relationship('Usuario', foreign_keys=usuario_id)

    def __init__(self, curso, instituicao, data, descricao, usuario_id):
        self.curso = curso
        self.instituicao = instituicao
        self.data = data
        self.descricao = descricao
        self.usuario_id = usuario_id


class Experiencia(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    cargo = db.Column(db.String(128))
    empresa = db.Column(db.String(128))
    data = db.Column(db.String(128))
    descricao = db.Column(db.String(512))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    usuario = db.relationship('Usuario', foreign_keys=usuario_id)

    def __init__(self, cargo, empresa, data, descricao, usuario_id):
        self.cargo = cargo
        self.empresa = empresa
        self.data = data
        self.descricao = descricao
        self.usuario_id = usuario_id


class Habilidade(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    nome = db.Column(db.String(128))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    usuario = db.relationship('Usuario', foreign_keys=usuario_id)

    def __init__(self, nome, usuario_id):
        self.nome = nome
        self.usuario_id = usuario_id


# endregion

# region Banco de Dados
with app.app_context():
    db.create_all()
    db.session.commit()


# endregion

@app.route('/', methods=['GET', 'POST'])
def index():
    # Retorna a página inicial do site - Sem usuário logado
    if (request.method == 'GET') and ('usuario' not in session):
        return render_template('index.html')

    # Retorna a página inicial do site - Com usuário logado
    elif (request.method == 'GET') and ('usuario' in session):
        usuario = Usuario.query.filter_by(email=session['usuario']).first()
        formacoes = Formacao.query.filter_by(usuario_id=usuario.id).all()
        experiencias = Experiencia.query.filter_by(usuario_id=usuario.id).all()
        habilidades = Habilidade.query.filter_by(usuario_id=usuario.id).all()
        return render_template('index.html', usuario=usuario, formacoes=formacoes, experiencias=experiencias,
                               habilidades=habilidades)
    return render_template('index.html')


# region Region Auth
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(email=email, senha=senha).first()
        if usuario:
            session['usuario'] = email
            return render_template('index.html', mensagem='Login realizado com sucesso.', tipo='success',
                                   usuario=usuario)
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
        return render_template('index.html', mensagem='Você não está logado. Acesso direto não é permitido.', tipo='danger')


# endregion
if __name__ == '__main__':
    db.create_all()
    app.run()
