from typing import Optional
from .generator_interface import CommentGeneratorInterface
from .ollama_generator import OllamaGenerator
from .fallback_generator import FallbackGenerator
from core.logger import logger
from core.config_manager import ConfigManager

class CommentGeneratorFactory:
    """
    Fábrica responsável por instanciar o gerador adequado (Ollama ou Fallback).
    Injeta dependências necessárias (URL do Ollama, etc) a partir da configuração central.
    """
    
    @staticmethod
    def create(config_manager: ConfigManager) -> CommentGeneratorInterface:
        ollama_config = config_manager.get_ollama_config()
        
        if ollama_config.get("enabled", True):
            url = ollama_config.get("url", "http://localhost:11434")
            model = ollama_config.get("model", "phi3")
            timeout = ollama_config.get("timeout", 60)
            system_prompt = ollama_config.get("system_prompt", None)
            options = ollama_config.get("options", {})
            logger.debug(
                f"Instanciando OllamaGenerator | url={url} | model={model} | "
                f"timeout={timeout}s | options={options}"
            )
            return OllamaGenerator(
                ollama_url=url,
                model=model,
                timeout=timeout,
                system_prompt=system_prompt,
                options=options,
            )
            
        logger.debug("Ollama desabilitado. Instanciando FallbackGenerator.")
        return FallbackGenerator()
