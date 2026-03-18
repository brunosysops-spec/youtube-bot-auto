from abc import ABC, abstractmethod
from typing import Dict, Any

class HistoryRepository(ABC):
    """
    Interface abstrata para persistência do histórico de vídeos comentados.
    Permite fácil transição entre JSON local e bancos como Redis/Postgres (no K8s).
    """

    @abstractmethod
    def has_comment(self, video_id: str) -> bool:
        """Retorna True se o vídeo já foi comentado."""
        pass

    @abstractmethod
    def register_comment(self, video_id: str, comment_id: str, video_title: str = "", comment_text: str = ""):
        """Registra no repositório um novo comentário bem-sucedido."""
        pass
        
    @abstractmethod
    def get_all_comments(self) -> Dict[str, Any]:
        """Retorna todos os comentários já feitos."""
        pass
