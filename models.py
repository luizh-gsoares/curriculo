import re
from abc import abstractmethod, ABC
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template
from flask_sqlalchemy.session import Session
from openai import OpenAI
import datetime

# region Configurações
app = Flask(__name__)
app.secret_key = '4N4K1N5KYW4LK3R'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///curriculo.sqlite3'
app.app_context().push()
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=30)
client = OpenAI(api_key='CHAVE_AQUI')


# endregion

################ Models       ################

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


class InputsValidator:
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
        email = usuario_service.get_usuario_by_email(data)
        if email:
            return False
        return True


class PasswordValidation(ValidationStrategy):
    def validate(self, data):
        # Verifica se a senha possui pelo menos 8 caracteres, uma letra maiúscula e um número
        if len(data) >= 8 and any(c.isupper() for c in data) and any(c.isdigit() for c in data):
            return True
        return False


class EmptyInputValidation(ValidationStrategy):
    # Verifica se o campo está vazio
    def validate(self, data):
        for key, value in data.items():
            if not value:
                return False
        return True


# endregion

# region Banco de Dados
with app.app_context():
    db.create_all()
    db.session.commit()


# endregion

################ Models       ################


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

    def get_all_by_user_id(self, entity_class, user_id):
        return self.session.query(entity_class).filter(entity_class.usuario_id == user_id).all()

    def get_by_email(self, entity_class, email):
        return self.session.query(entity_class).filter(entity_class.email == email).first()


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


class CurriculoRepository(BaseRepository):
    pass


# endregion
################ Repositories ################

################ Services ################
# region
class UsuarioService:
    def __init__(self, usuario_repository: UsuarioRepository):
        self.usuario_repository = usuario_repository

    def create_usuario(self, usuario_data):
        usuario = Usuario(**usuario_data)
        self.usuario_repository.add(usuario)

    def get_usuario_by_email(self, email):
        return self.usuario_repository.get_by_email(Usuario, email)


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

    def get_dadospessoais_by_user_id(self, user_id):
        result = self.dadospessoais_repository.get_all_by_user_id(DadosPessoais, user_id)
        if result:
            return result[0]
        return None


class ExperienciaService:
    def __init__(self, experiencia_repository: ExperienciaRepository):
        self.experiencia_repository = experiencia_repository

    def create_experiencia(self, experiencia_data):
        experiencia = Experiencia(**experiencia_data)
        self.experiencia_repository.add(experiencia)

    def update_experiencia(self, experiencia_id, experiencia_data):
        experiencia = self.experiencia_repository.get_by_id(Experiencia, experiencia_id)
        for key, value in experiencia_data.items():
            setattr(experiencia, key, value)
        self.experiencia_repository.update()

    def delete_experiencia(self, experiencia_id):
        experiencia = self.experiencia_repository.get_by_id(Experiencia, experiencia_id)
        self.experiencia_repository.delete(experiencia)

    def get_experiencia_by_id(self, experiencia_id):
        return self.experiencia_repository.get_by_id(Experiencia, experiencia_id)

    def get_experiencia_by_user_id(self, user_id):
        return self.experiencia_repository.get_all_by_user_id(Experiencia, user_id)


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

    def get_formacao_by_user_id(self, user_id):
        return self.formacao_repository.get_all_by_user_id(Formacao, user_id)


class HabilidadeService:
    def __init__(self, habilidade_repository: HabilidadeRepository):
        self.habilidade_repository = habilidade_repository

    def create_habilidade(self, habilidade_data):
        habilidade = Habilidade(**habilidade_data)
        self.habilidade_repository.add(habilidade)

    def delete_habilidade(self, habilidade_id):
        habilidade = self.habilidade_repository.get_by_id(Habilidade, habilidade_id)
        self.habilidade_repository.delete(habilidade)

    def get_habilidade_by_id(self, habilidade_id):
        return self.habilidade_repository.get_by_id(Habilidade, habilidade_id)

    def get_habilidade_by_user_id(self, user_id):
        return self.habilidade_repository.get_all_by_user_id(Habilidade, user_id)


class CurriculoService:
    def __init__(self, usuario_repository, dadospessoais_repository, formacao_repository, experiencia_repository,
                 habilidade_repository):
        self.usuario_repository = usuario_repository
        self.dadospessoais_repository = dadospessoais_repository
        self.formacao_repository = formacao_repository
        self.experiencia_repository = experiencia_repository
        self.habilidade_repository = habilidade_repository

    def get_curriculo(self, user_id):
        dadospessoais = self.dadospessoais_repository.get_all_by_user_id(DadosPessoais, user_id)
        formacao = self.formacao_repository.get_all_by_user_id(Formacao, user_id)
        experiencia = self.experiencia_repository.get_all_by_user_id(Experiencia, user_id)
        habilidade = self.habilidade_repository.get_all_by_user_id(Habilidade, user_id)

        return {
            # Retorna o primeiro dado pessoal, fiz assim para evitar erros de index
            'dadospessoais': dadospessoais[0] if dadospessoais else None,
            'formacao': formacao,
            'experiencia': experiencia,
            'habilidade': habilidade
        }


# endregion
################ Services ################

# Inicialização dos Repositories
usuario_repository = UsuarioRepository(db.session)
dadospessoais_repository = DadosPessoaisRepository(db.session)
experiencia_repository = ExperienciaRepository(db.session)
formacao_repository = FormacaoRepository(db.session)
habilidade_repository = HabilidadeRepository(db.session)
curriculo_repository = CurriculoRepository(db.session)

# Inicialização dos Services
usuario_service = UsuarioService(UsuarioRepository(db.session))
dadospessoais_service = DadosPessoaisService(DadosPessoaisRepository(db.session))
experiencia_service = ExperienciaService(ExperienciaRepository(db.session))
formacao_service = FormacaoService(FormacaoRepository(db.session))
habilidade_service = HabilidadeService(HabilidadeRepository(db.session))
curriculo_service = CurriculoService(usuario_repository, dadospessoais_repository, formacao_repository,
                                     experiencia_repository, habilidade_repository)
