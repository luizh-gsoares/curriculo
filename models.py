import re
from abc import abstractmethod, ABC
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, session, redirect, jsonify
from flask_sqlalchemy.session import Session
from openai import OpenAI
import datetime

# region Configurações
app = Flask(__name__)
app.secret_key = '4N4K1N5KYW4LK3R'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///curriculo.sqlite3'
app.app_context().push()
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=10)
# client = OpenAI(api_key='CHAVE AQUI')


# endregion

################ Models       ################
# region

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
        return render_template('curriculo.html',
                               dadospessoais=self.dadospessoais,
                               formacao=self.formacao,
                               experiencia=self.experiencia,
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
        return f"<div style='color: {self.color};'>{rendered}</div>"


class FontDecorator(CurriculoDecorator):
    def __init__(self, curriculo, font):
        super().__init__(curriculo)
        self.font = font

    def render(self):
        rendered = super().render()
        return f"<div style='font-family: {self.font};'>{rendered}</div>"


class SizeDecorator(CurriculoDecorator):
    def __init__(self, curriculo, size):
        super().__init__(curriculo)
        self.size = size

    def render(self):
        rendered = super().render()
        return f"<div style='font-size: {self.size};'>{rendered}</div>"


# endregion

# region class Padrao de Projeto Comportamental - Strategy
class ValidationStrategy(ABC):
    @abstractmethod
    def validate(self, data):
        pass


class UserValidator:
    def __init__(self, strategy: ValidationStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: ValidationStrategy):
        self._strategy = strategy

    def validate(self, data):
        return self._strategy.validate(data)


class EmailValidation(ValidationStrategy):
    def validate(self, data):
        email_regex = r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.match(email_regex, data):
            return True
        return False


class EmailAlreadyExistsValidation(ValidationStrategy):
    def validate(self, data):
        email = db.session.query(Usuario).filter(Usuario.email == data).first()
        if email:
            return False
        return True


class PasswordValidation(ValidationStrategy):
    def validate(self, data):
        # Verifica se a senha possui pelo menos 8 caracteres, uma letra maiúscula e um número
        if len(data) >= 8 and any(c.isupper() for c in data) and any(c.isdigit() for c in data):
            return True
        return False


class clearInputValidation(ValidationStrategy):
    def validate(self, data):
        if data == "":
            return False
        return True

# endregion

# region Banco de Dados
with app.app_context():
    db.create_all()
    db.session.commit()


# endregion

# endregion

################ Repositories ################
# region
class BaseRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, entity):
        self.session.add(entity)
        self.session.commit()

    def update(self):
        self.session.commit()

    def delete(self, entity):
        self.session.delete(entity)
        self.session.commit()

    def get_by_id(self, entity_class, entity_id):
        return self.session.query(entity_class).get(entity_id)

    def get_all(self, entity_class):
        return self.session.query(entity_class).all()


class DadosPessoaisRepository(BaseRepository):
    pass


class FormacaoRepository(BaseRepository):
    pass


class ExperienciaRepository(BaseRepository):
    pass


class HabilidadeRepository(BaseRepository):
    pass


class UsuarioRepository(BaseRepository):
    pass


# endregion
################ Repositories ################

################ Services ################
# region
class DadosPessoaisService:
    def __init__(self, dadospessoais_repository: DadosPessoaisRepository):
        self.dadospessoais_repository = dadospessoais_repository

    def create_dadospessoais(self, dadospessoais_data):
        dadospessoais = DadosPessoais(**dadospessoais_data)
        self.dadospessoais_repository.add(dadospessoais)

    def update_dadospessoais(self, dadospessoais_id, dadospessoais_data):
        dadospessoais = self.dadospessoais_repository.get_by_id(DadosPessoais, dadospessoais_id)
        for key, value in dadospessoais_data.items():
            setattr(dadospessoais, key, value)
        self.dadospessoais_repository.update()

    def delete_dadospessoais(self, dadospessoais_id):
        dadospessoais = self.dadospessoais_repository.get_by_id(DadosPessoais, dadospessoais_id)
        self.dadospessoais_repository.delete(dadospessoais)

    def get_dadospessoais_by_id(self, dadospessoais_id):
        return self.dadospessoais_repository.get_by_id(DadosPessoais, dadospessoais_id)

    def get_all_formacoes(self):
        return self.dadospessoais_repository.get_all(DadosPessoais)


class FormacaoService:
    def __init__(self, formacao_repository: FormacaoRepository):
        self.formacao_repository = formacao_repository

    def create_formacao(self, formacao_data):
        formacao = Formacao(**formacao_data)
        self.formacao_repository.add(formacao)

    def update_formacao(self, formacao_id, formacao_data):
        formacao = self.formacao_repository.get_by_id(Formacao, formacao_id)
        for key, value in formacao_data.items():
            setattr(formacao, key, value)
        self.formacao_repository.update()

    def delete_formacao(self, formacao_id):
        formacao = self.formacao_repository.get_by_id(Formacao, formacao_id)
        self.formacao_repository.delete(formacao)

    def get_formacao_by_id(self, formacao_id):
        return self.formacao_repository.get_by_id(Formacao, formacao_id)

    def get_all_formacoes(self):
        return self.formacao_repository.get_all(Formacao)
