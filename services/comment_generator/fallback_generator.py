import random
from .generator_interface import CommentGeneratorInterface
from core.logger import logger

class FallbackGenerator(CommentGeneratorInterface):
    """
    Simples gerador baseado em listas estáticas, usado caso o Ollama 
    falhe ou não esteja disponível.
    """
    
    def __init__(self):
        self.templates = [
            "Muito bom o vídeo! {emoji}",
            "Conteúdo top demais! {emoji} {reaction}",
            "Sempre mandando bem! {reaction}",
            "Vídeo excelente! {emoji}",
            "Curti muito! {reaction} {emoji}"
        ]
        self.reactions = ["Show!", "Incrível!", "Sensacional!", "Brabo!", "Top!"]
        self.emojis = ["👏", "🔥", "🚀", "💪", "👍", "😎"]

    def generate(self, video_title: str, video_description: str = "") -> str:
        logger.debug(f"Gerando comentário fallback para: {video_title}")
        template = random.choice(self.templates)
        reaction = random.choice(self.reactions)
        emoji = random.choice(self.emojis)
        
        text = template.format(reaction=reaction, emoji=emoji)
        return text
