import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.config_manager import ConfigManager
from core.logger import logger
from storage.json_history import JsonHistoryRepository
from services.youtube_api import YouTubeService
from services.comment_generator.factory import CommentGeneratorFactory

def get_all_videos(youtube_service: YouTubeService, channel_id: str, max_results=1000) -> list:
    """Busca a lista de todos os vídeos da playlist de Uploads do canal"""
    videos = []
    next_page_token = None
    
    try:
        # Pega a Playlist de Uploads associada ao canal via YouTube API (nativo)
        channel_response = youtube_service.youtube.channels().list(
            part='contentDetails',
            id=channel_id
        ).execute()
        
        if not channel_response.get('items'):
            logger.error(f"Canal não encontrado na API: {channel_id}")
            return []
            
        uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        while True:
            playlist_response = youtube_service.youtube.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token
            ).execute()
            
            for item in playlist_response.get('items', []):
                video_id = item['snippet']['resourceId']['videoId']
                title = item['snippet']['title']
                videos.append({
                    'id': video_id,
                    'title': title
                })
                
            next_page_token = playlist_response.get('nextPageToken')
            if not next_page_token or len(videos) >= max_results:
                break
                
        logger.info(f"Total de vídeos encontrados no canal: {len(videos)}")
        return videos
        
    except Exception as e:
        logger.error(f"Erro ao obter a lista de vídeos da PlayList Uploads: {str(e)}")
        return []

def select_channel(config_manager: ConfigManager):
    """Permite selecionar interativamente um canal configurado (Via Stdout)"""
    channels = config_manager.get_enabled_channels()
    if not channels:
        logger.error("Nenhum canal ativo encontrado nas configurações.")
        return None
        
    print("\n--- Canais Disponíveis (Backfill) ---")
    for i, c in enumerate(channels, 1):
        print(f"{i}. {c.get('name', c['channel_id'])}")
    print("0. Fornecer ID manual")
    
    try:
        choice = input(f"\nEscolha uma opção (0-{len(channels)}): ")
        if choice == "0":
            custom_id = input("Digite o YouTube Channel ID: ").strip()
            return {
                "channel_id": custom_id,
                # Fallback usando credenciais do 1º canal
                "credentials_file": channels[0]["credentials_file"] 
            }
        
        index = int(choice) - 1
        return channels[index]
    except Exception:
        logger.error("Opção Inválida.")
        return None

def print_history(history_repo: JsonHistoryRepository):
    """Exibe o histórico de comentários"""
    history = history_repo.get_all_comments()
    if not history:
        print("Histórico vazio.")
        return
        
    sorted_history = sorted(
        history.items(),
        key=lambda x: x[1].get('timestamp', ''),
        reverse=True
    )
    
    print("\n--- Histórico de Comentários ---")
    for vid, info in sorted_history:
        print(f"[{vid}] {info.get('video_title')} | {info.get('timestamp')}")
        print(f" -> {info.get('comment_text')}")
        print("-" * 40)
    print(f"Total de vídeos marcados como comentados: {len(history)}")

def run_backfill(channel_config: dict, config_manager: ConfigManager, history_repo: JsonHistoryRepository):
    channel_id = channel_config["channel_id"]
    creds_file = channel_config.get("credentials_file")
    
    youtube_service = YouTubeService(creds_file)
    generator = CommentGeneratorFactory.create(config_manager)
    
    videos = get_all_videos(youtube_service, channel_id)
    if not videos:
        return
        
    logger.info("Processando Backfill (Ctrl+C para interromper)...")
    
    try:
        for v in videos:
            vid = v['id']
            title = v['title']
            
            if history_repo.has_comment(vid):
                logger.debug(f"Pular vídeo já comentado: {title}")
                continue
                
            logger.info(f"Comentando Backfill: {title}")
            comment_text = generator.generate(video_title=title)
            
            if not comment_text:
                logger.error(f"Falha na geração para {vid}. Pulando.")
                continue
                
            comment_id = youtube_service.post_comment(vid, comment_text)
            if comment_id:
                history_repo.register_comment(vid, comment_id, title, comment_text)
                
            logger.info("Aguardando 10 segundos (Rate Limit)...")
            time.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("Backfill interrompido pelo usuário.")
    except Exception as e:
        logger.error(f"Erro inesperado no Backfill: {str(e)}")

if __name__ == "__main__":
    config_manager = ConfigManager()
    repo_file = config_manager.get_history_file()
    history_repo = JsonHistoryRepository(repo_file)
    
    # Simples flag CLI para apenas ler o histórico
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        print_history(history_repo)
        sys.exit(0)
        
    c_config = select_channel(config_manager)
    if c_config:
        run_backfill(c_config, config_manager, history_repo)
