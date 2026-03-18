import json
import os
from datetime import datetime
from typing import Dict, Any
from core.logger import logger
from .history_repository_interface import HistoryRepository

class JsonHistoryRepository(HistoryRepository):
    """
    Implementação baseada em arquivo para armazenar o histórico de comentários.
    Unifica a antiga lógica do 'all_comments_history.json' e 'comment_history.json' 
    que estava duplicada entre os scripts.
    """

    def __init__(self, filename: str):
        self.filename = filename

    def _load_history(self) -> Dict[str, Any]:
        try:
            if os.path.exists(self.filename):
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Erro ao carregar histórico local ({self.filename}): {str(e)}")
            return {}

    def _save_history(self, history: Dict[str, Any]):
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar histórico em {self.filename}: {str(e)}")

    def has_comment(self, video_id: str) -> bool:
        history = self._load_history()
        return video_id in history

    def register_comment(self, video_id: str, comment_id: str, video_title: str = "", comment_text: str = ""):
        history = self._load_history()
        
        # Consolida os detalhes como nome do vídeo e o comentário inteiro 
        # presentes em (all_comments_history) e o status do outro script
        history[video_id] = {
            "comment_id": comment_id,
            "video_title": video_title or "Título não disponível",
            "comment_text": comment_text or "Texto não registrado",
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
        
        self._save_history(history)
        logger.debug(f"Histórico atualizado para vídeo {video_id}.")
        
    def get_all_comments(self) -> Dict[str, Any]:
        return self._load_history()
