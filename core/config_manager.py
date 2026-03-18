import os
import json
from .logger import logger

class ConfigManager:
    """
    Gerencia as configurações da aplicação lendo variáveis de ambiente primeiro
    e fazendo fallback num arquivo `config.json` local (para desenvolvimento).
    """

    def __init__(self, config_file=None):
        if config_file is None:
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            config_file = os.path.join(root_dir, 'config.json')
        self.config_file = config_file
        self.config = self._load_local_config()
        self._override_with_env_vars()

    def _load_local_config(self) -> dict:
        """Carrega do config.json se ele existir locais."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Erro ao carregar {self.config_file}: {str(e)}")
            return {}

    def _override_with_env_vars(self):
        """Sobrescreve opções com base nas variáveis do ambiente (K8s)"""
        if 'ollama' not in self.config:
            self.config['ollama'] = {}
        if 'options' not in self.config['ollama']:
            self.config['ollama']['options'] = {}

        if os.environ.get('OLLAMA_URL'):
            self.config['ollama']['url'] = os.environ.get('OLLAMA_URL')

        if os.environ.get('OLLAMA_MODEL'):
            self.config['ollama']['model'] = os.environ.get('OLLAMA_MODEL')

        if os.environ.get('OLLAMA_TIMEOUT'):
            self.config['ollama']['timeout'] = int(os.environ.get('OLLAMA_TIMEOUT'))

        if os.environ.get('OLLAMA_NUM_PREDICT'):
            self.config['ollama']['options']['num_predict'] = int(os.environ.get('OLLAMA_NUM_PREDICT'))

        if os.environ.get('OLLAMA_NUM_CTX'):
            self.config['ollama']['options']['num_ctx'] = int(os.environ.get('OLLAMA_NUM_CTX'))

        # Suporte para secrets ou json de credentials do Google passado inline ou via volume montado:
        # No K8s os certificados geralmente são injetados como um arquivo montado no Pod.
        self.credentials_path = os.environ.get('GOOGLE_CREDENTIALS_FILE', None)

    def get_enabled_channels(self):
        """Retorna todos os canais configurados."""
        channels = self.config.get("channels", [])
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

        enabled_channels = []
        for c in channels:
            if c.get("enabled", True):
                if c.get("credentials_file") and not os.path.isabs(c["credentials_file"]):
                    c["credentials_file"] = os.path.join(root_dir, c["credentials_file"])
                enabled_channels.append(c)
        return enabled_channels

    def get_ollama_config(self):
        """Retorna configurações do Ollama com defaults seguros."""
        defaults = {
            "enabled": True,
            "url": "http://localhost:11434",
            "model": "phi3",
            "timeout": 60,
            "system_prompt": (
                "Você é um bot brasileiro e gaúcho com humor leve e positivo. "
                "Responda APENAS com o comentário, sem explicações, sem aspas e sem saudações. "
                "Máximo de 2 frases."
            ),
            "options": {
                "temperature": 0.8,
                "num_predict": 100,
                "num_ctx": 1024,
                "top_k": 40,
                "top_p": 0.9
            }
        }
        config = self.config.get("ollama", {})
        # Merge: valores do config.json sobrescrevem os defaults
        merged = {**defaults, **config}
        merged["options"] = {**defaults["options"], **config.get("options", {})}
        return merged

    def get_storage_type(self) -> str:
        """Define onde o bot deve salvar a persistência (json, redis, etc)"""
        # Ex: Definir "redis" no K8s, "json" localmente
        return os.environ.get("STORAGE_TYPE", "json")
        
    def get_history_file(self) -> str:
        """Retorna num o local o caminho base do arquivo de histórico JSON."""
        default_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), "comment_history.json")
        return os.environ.get("HISTORY_FILE_PATH", default_path)
