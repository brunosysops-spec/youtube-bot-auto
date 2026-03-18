import logging
import sys
import os

def setup_logger(name: str = 'YouTubeBot'):
    """
    Configures a standard logger optimized for 12-Factor App (Kubernetes).
    Outputs all logs to stdout/stderr.
    """
    logger = logging.getLogger(name)
    
    # Define o nível de log baseado em variável de ambiente (padrão INFO)
    log_level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(log_level)
    
    # Evita adicionar múltiplos handlers caso logger seja invocado várias vezes
    if not logger.handlers:
        # Handler para stdout (padrão K8s)
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Formato limpo e consistente
        formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s', 
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger

# Instância global configurada
logger = setup_logger()
