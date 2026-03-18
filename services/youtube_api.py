from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from core.logger import logger

class YouTubeService:
    """
    Isola a comunicação com a API do YouTube (Google API).
    """

    def __init__(self, credentials_file: str):
        self.credentials_file = credentials_file
        self.youtube = self._build_client()

    def _build_client(self):
        try:
            logger.debug(f"Carregando credenciais de: {self.credentials_file}")
            creds = Credentials.from_authorized_user_file(
                self.credentials_file, 
                scopes=["https://www.googleapis.com/auth/youtube.force-ssl"]
            )
            return build("youtube", "v3", credentials=creds)
        except Exception as e:
            logger.error(f"Erro ao inicializar API do YouTube: {str(e)}")
            raise

    def get_video_title(self, video_id: str) -> str:
        """Busca o título do vídeo pela API."""
        try:
            response = self.youtube.videos().list(
                part="snippet",
                id=video_id
            ).execute()
            
            if response.get("items"):
                return response["items"][0]["snippet"]["title"]
            return None
        except Exception as e:
            logger.error(f"Erro ao obter título do vídeo {video_id}: {str(e)}")
            return None

    def post_comment(self, video_id: str, comment_text: str) -> str:
        """
        Publica um comentário num vídeo e retorna o comment_id.
        Em caso de erro, retorna None.
        """
        try:
            response = self.youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {
                            "snippet": {
                                "textOriginal": comment_text
                            }
                        }
                    }
                }
            ).execute()
            
            comment_id = response.get('id')
            logger.debug(f"Sucesso. Comment ID: {comment_id} no Vídeo {video_id}")
            return comment_id
            
        except Exception as e:
            logger.error(f"Erro Google API ao postar comentário no {video_id}: {str(e)}")
            return None
