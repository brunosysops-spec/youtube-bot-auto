import requests
import xml.etree.ElementTree as ET
from core.logger import logger

class RssFeedService:
    """
    Serviço responsável por ler o Feed XML do YouTube para um canal e 
    identificar qual é o vídeo mais recente.
    """
    
    def __init__(self, channel_id: str):
        self.channel_id = channel_id
        self.feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        self.session = requests.Session()
        
        # Otimização de rede para evitar travamentos
        adapter = requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=3,
            pool_maxsize=3
        )
        self.session.mount('https://', adapter)

    def get_latest_video_info(self) -> dict:
        """Obtém o ID e Título do vídeo mais recente do canal via RSS feed."""
        try:
            logger.debug(f"[{self.channel_id}] Buscando feed: {self.feed_url}")
            
            r = self.session.get(self.feed_url, timeout=30)
            r.raise_for_status()
            
            root = ET.fromstring(r.text)
            
            # Procura pela entrada mais recente
            entry = root.find("{http://www.w3.org/2005/Atom}entry")
            if entry is None:
                logger.warning(f"[{self.channel_id}] Nenhuma entrada encontrada no feed.")
                return None
                
            # Extração de ID
            video_id = None
            yt_video_id = entry.find("{http://www.youtube.com/xml/schemas/2015}videoId")
            if yt_video_id is not None:
                video_id = yt_video_id.text
            
            if not video_id:
                link = entry.find("{http://www.w3.org/2005/Atom}link")
                if link is not None:
                    href = link.get("href", "")
                    if "watch?v=" in href:
                        video_id = href.split("watch?v=")[-1]
                    elif "youtu.be/" in href:
                        video_id = href.split("youtu.be/")[-1]
            
            # Extração de Título
            title = None
            title_elem = entry.find("{http://www.w3.org/2005/Atom}title")
            if title_elem is not None:
                title = title_elem.text

            if video_id:
                logger.info(f"[{self.channel_id}] Último Vídeo RSS: {video_id} - {title}")
                return {"id": video_id, "title": title}
            else:
                logger.error(f"[{self.channel_id}] Falha ao extrair ID do vídeo do XML.")
                return None
                
        except Exception as e:
            logger.error(f"[{self.channel_id}] Erro ao processar feed RSS: {str(e)}")
            return None
