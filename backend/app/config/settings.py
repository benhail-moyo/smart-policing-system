import os


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://crime_watch:crime_watch@localhost:5432/crime_watch",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GA_POPULATION_SIZE = int(os.getenv("GA_POPULATION_SIZE", "100"))
    GA_GENERATIONS = int(os.getenv("GA_GENERATIONS", "200"))
    GA_MUTATION_RATE = float(os.getenv("GA_MUTATION_RATE", "0.02"))
    GA_CROSSOVER_RATE = float(os.getenv("GA_CROSSOVER_RATE", "0.8"))


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


class ProductionConfig(BaseConfig):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
