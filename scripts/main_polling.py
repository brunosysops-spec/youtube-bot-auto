import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
from core.config_manager import ConfigManager
from core.logger import logger
from storage.json_history import JsonHistoryRepository
from services.rss_feed import RssFeedService
from services.youtube_api import YouTubeService
from services.comment_generator.factory import CommentGeneratorFactory

def run_polling_bot():
    try:
        logger.info("Iniciando execução do bot (Polling Mode)...")
        
        # 1. Configuração Centralizada
        config_manager = ConfigManager()
        
        # 2. Inicializa o Repositório de Histórico (JSON local por enquanto)
        repo_file = config_manager.get_history_file()
        history_repo = JsonHistoryRepository(repo_file)

        # 3. Gerador de Comentários (via Factory - decide entre Ollama ou Fallback)
        comment_generator = CommentGeneratorFactory.create(config_manager)

        # 4. Processa canais habilitados
        for channel in config_manager.get_enabled_channels():
            channel_id = channel["channel_id"]
            channel_name = channel.get("name", channel_id)
            creds_file = channel.get("credentials_file")
            
            logger.info(f"Processando canal: {channel_name} ({channel_id})")
            
            try:
                # Inicializa serviços do canal
                rss_service = RssFeedService(channel_id)
                youtube_service = YouTubeService(creds_file)
                
                # Busca o vídeo mais recente do Feed RSS
                video_info = rss_service.get_latest_video_info()
                if not video_info:
                    logger.warning(f"Nenhum vídeo retornado no Feed RSS para {channel_name}")
                    continue
                
                video_id = video_info['id']
                title = video_info.get('title', 'Sem Título')
                
                # Verifica se o vídeo já foi comentado
                if history_repo.has_comment(video_id):
                    logger.info(f"Vídeo '{title}' ({video_id}) já possui comentário. Pulando.")
                    continue
                
                # Se não possui, gera o comentário
                logger.info(f"Tentando comentar no vídeo inédito: {title}")
                comment_text = comment_generator.generate(video_title=title)
                
                # Caso a geração falhe e retorne None
                if not comment_text:
                    logger.error(f"Falha ao gerar o texto do comentário para {video_id}.")
                    continue
                
                # Posta o comentário na API do YouTube
                comment_id = youtube_service.post_comment(video_id, comment_text)
                
                if comment_id:
                    # Persiste o sucesso se temos um ID
                    history_repo.register_comment(
                        video_id=video_id,
                        comment_id=comment_id,
                        video_title=title,
                        comment_text=comment_text
                    )
                    logger.info(f"Sucesso total. Comentário salvo para {video_id}.")
                else:
                    logger.error(f"Falha reportada pela API do YouTube para o vídeo {video_id}.")
            
            except Exception as e:
                logger.error(f"Erro ao processar o canal {channel_name}: {str(e)}")
            
            # Aguarda alguns segundos entre canais para evitar block de rede
            time.sleep(5)
            
    except Exception as e:
        logger.error(f"Erro Crítico Geral na Aplicação (Polling): {str(e)}")

if __name__ == "__main__":
    # Em um ambiente 12-Factor, deixamos o K8s agendar o polling (CronJob) 
    # ou rodamos em um loop for infinito com sleep. 
    # Optando por uma execução corrida padrão para adaptar no Entrypoint / CronJob K8s
    run_polling_bot()
