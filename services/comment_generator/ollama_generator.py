import requests
from .generator_interface import CommentGeneratorInterface
from core.logger import logger


class OllamaGenerator(CommentGeneratorInterface):
    """
    Gerador de comentários utilizando a API local do Ollama.
    Recebe todos os parâmetros de segurança via construtor para evitar
    valores hardcoded e permitir configuração via config.json / env vars.
    """

    DEFAULT_SYSTEM_PROMPT = (
        "Você é um usuário brasileiro real assistindo a um vídeo de um canal que você gosta. "
        "Escreva um comentário curto, casual e em português natural do Brasil. "
        "REGRAS: Responda APENAS com o comentário. Máximo de 15 palavras. "
        "PROIBIDO: usar hashtags (#), usar aspas, saudações formais ou palavras complexas."
    )

    DEFAULT_OPTIONS = {
        "temperature": 0.8,
        "num_predict": 100,
        "num_ctx": 1024,
        "top_k": 40,
        "top_p": 0.9,
    }

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model: str = "phi3",
        timeout: int = 60,
        system_prompt: str = None,
        options: dict = None,
    ):
        self.ollama_url = ollama_url
        self.model = model
        self.timeout = timeout
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self.options = {**self.DEFAULT_OPTIONS, **(options or {})}

    def generate(self, video_title: str, video_description: str = "") -> str:
        logger.info(
            f"Gerando comentário via Ollama | modelo={self.model} | "
            f"timeout={self.timeout}s | num_predict={self.options.get('num_predict')} | "
            f"num_ctx={self.options.get('num_ctx')} | vídeo='{video_title}'"
        )

        prompt = (
            f"Aja como um inscrito brasileiro e gaúcho bastante empolgado, engajado que achou "
            f"divertido de um canal do YouTube.\n"
            f"Escreva um comentário curto (máximo 2 frases), informal e positivo sobre este vídeo.\n"
            f"Use gírias tipicamente gaúchas (Baah, Tche...) leves e engraçadas.\n"
            f"Use pelo menos 1 emoji.\n"
            f"Use hashtags que tenham relação com o título do vídeo.\n"
            f"NÃO use aspas no comentário. NÃO explique o comentário. "
            f"Não faça comentários incoerentes. Não adicione frases pela metade. Apenas gere o texto.\n\n"
            f"Título do vídeo: {video_title}"
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            # Campo 'system' é a "coleira" do modelo — instruções prioritárias que
            # o Ollama aplica antes de qualquer prompt do usuário.
            "system": self.system_prompt,
            "stream": False,
            "options": self.options,
        }

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            result = response.json()
            comment = result.get("response", "").strip()
            logger.info(f"Comentário gerado com sucesso ({len(comment)} chars)")
            # Limpa aspas caso o modelo insista em gerar
            return comment.replace('"', "").replace("'", "")

        except requests.exceptions.Timeout:
            logger.error(
                f"[Timeout] Ollama não respondeu em {self.timeout}s. "
                f"Considere reduzir num_predict ou num_ctx."
            )
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"[HTTP {e.response.status_code}] Erro do Ollama: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"[Erro] Falha na comunicação com o Ollama: {e}")
            return None
