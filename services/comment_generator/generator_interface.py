from abc import ABC, abstractmethod

class CommentGeneratorInterface(ABC):
    """
    Interface abstrata para geradores de comentários. 
    Define como a aplicação solicitará a criação de um novo comentário.
    """

    @abstractmethod
    def generate(self, video_title: str, video_description: str = "") -> str:
        """
        Gera o texto de um comentário baseado nas informações fornecidas.
        Pode retornar string vazia ou None caso falhe.
        """
        pass
