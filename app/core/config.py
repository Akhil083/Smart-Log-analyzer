from functools import lru_cache

from pydantic import  Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file= ".env",
        env_file_encoding= "utf-8",
        case_sensitive=False,
        extra = "ignore",
    )

    #------Application Info
    app_name: str ="Smart Log Analyzer"
    app_version : str = "0.1.0"
    app_env : str = Field(defaulf="development", alias="APP_ENV")
    debug : bool = Field(default =False, alias = "DEBUG")
    api_v1_prefix : str = "/api/v1"


    #------Server Info
    host : str = Field(default = "0.0.0.0", alias = "HOST")
    port : int = Field(default =8000,alias = "PORT")
    cros_origins: list[str] = Field(default_factory = list , alias = "CROSS_ORIGINS")
    log_level: str = Field (default= "INFO", alias = "LOG_LEVEL")


    #------Database
    postgres_user:str = Field(alias="POSTGRES_USER")
    postgres_password:str = Field(alias="POSTGRES_PASSWORD")
    postgres_host:str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port:int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db:str = Field(alias="POSTGRES_DB")
    sqlalchemy_echo:bool = Field(default= False, alias="SQLALCHEMY_ECHO") 

    
    
    #-------Vector Search
    embedding_dimension: int =Field(default = 384, alias = "EMBEDDING_DIMENSIONS")

    #-------Retention days
    log_retention_days : int = 30
    alert_check_interval_minute: int = 2
    cleanup_interval_hours: int = 24


    @computed_field
    @property
    def database_url(self) -> str:
        """Async SQLAlchemy database url"""

        return (
            f"postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    

@lru_cache
def get_settings() -> Settings :
    """Return a cached Settings instance"""

    return Settings()