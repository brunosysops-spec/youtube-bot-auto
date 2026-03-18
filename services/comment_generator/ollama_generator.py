import requests
from .generator_interface import CommentGeneratorInterface
from core.logger import logger

class OllamaGenerator(CommentGeneratorInterface):
    """
    Gerador de comentários utilizando a API local do Ollama.
    """

    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "phi3"):
        self.ollama_url = ollama_url
        self.model = model

    def generate(self, video_title: str, video_description: str = "") -> str:
        logger.info(f"Gerando comentário via Ollama ({self.model}) para: {video_title}")
        try:
            prompt = f"""
            Aja como um inscrito brasileiro e gaucho bastante empolgado, engajado que achou divertido de um canal do YouTube.
            Escreva um comentário curto (máximo 2 frases), informal e positivo sobre este vídeo.
            Use gírias tipicamente gauchas (Baah, Tche..., e etc...) leves e engraçadas. 
            Use pelo menos 1 emoji.
            Use hashtags que tenha relação com o titulo do video.
            NÃO use aspas no comentário. NÃO explique o comentário. Não faça comentarios incoerentes. Não adicione frases pela metade. Apenas gere o texto.
            
            Título do vídeo: {video_title}
            """
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.8,
                    "num_predict": 60
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate", 
                json=payload, 
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                comment = result.get('response', '').strip()
                # Limpa aspas caso o modelo insista em gerar
                return comment.replace('"', '').replace("'", "")
            else:
                logger.error(f"Erro no Ollama: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erro na conexão com Ollama: {str(e)}")
            return None
