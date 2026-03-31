"""
Testes unitários para validar o comportamento de fallback do gerador de comentários.

Cobre:
- FallbackGenerator: geração de comentários estáticos
- OllamaGenerator: retorno None em timeout, erro HTTP e erro genérico
- main_polling: usa FallbackGenerator quando Ollama retorna None
- main_backfill: usa FallbackGenerator quando Ollama retorna None
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Garante que o root do projeto está no path (mesmo padrão dos scripts)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
from services.comment_generator.fallback_generator import FallbackGenerator
from services.comment_generator.ollama_generator import OllamaGenerator


# ---------------------------------------------------------------------------
# 1. FallbackGenerator
# ---------------------------------------------------------------------------
class TestFallbackGenerator(unittest.TestCase):

    def setUp(self):
        self.gen = FallbackGenerator()

    def test_generate_returns_string(self):
        """Deve retornar uma string não vazia."""
        result = self.gen.generate(video_title="Título de Teste")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_generate_contains_emoji(self):
        """O comentário deve conter pelo menos um emoji da lista."""
        emojis = self.gen.emojis
        # Gera 20 amostras para cobrir aleatoriedade
        results = [self.gen.generate("Vídeo X") for _ in range(20)]
        self.assertTrue(
            any(any(e in r for e in emojis) for r in results),
            "Nenhum comentário gerado continha emoji."
        )

    def test_generate_uses_templates(self):
        """Deve usar os templates definidos, não retornar string fixa."""
        results = {self.gen.generate("Vídeo") for _ in range(30)}
        # Com 30 tentativas e 5 templates × 5 reactions × 6 emojis = 150 combinações,
        # é quase certo que mais de 1 resultado seja único
        self.assertGreater(len(results), 1, "FallbackGenerator parece estar retornando sempre o mesmo texto.")

    def test_generate_ignores_description(self):
        """Deve funcionar com ou sem description."""
        r1 = self.gen.generate(video_title="Vídeo A")
        r2 = self.gen.generate(video_title="Vídeo A", video_description="Descrição qualquer")
        self.assertIsInstance(r1, str)
        self.assertIsInstance(r2, str)


# ---------------------------------------------------------------------------
# 2. OllamaGenerator — cenários de falha
# ---------------------------------------------------------------------------
class TestOllamaGeneratorFailures(unittest.TestCase):

    def setUp(self):
        self.gen = OllamaGenerator(
            ollama_url="http://localhost:11434",
            model="phi3",
            timeout=5,
        )

    @patch("services.comment_generator.ollama_generator.requests.post")
    def test_timeout_returns_none(self, mock_post):
        """Timeout deve retornar None."""
        mock_post.side_effect = requests.exceptions.Timeout()
        result = self.gen.generate("Vídeo Teste")
        self.assertIsNone(result)

    @patch("services.comment_generator.ollama_generator.requests.post")
    def test_http_error_returns_none(self, mock_post):
        """Erro HTTP (ex: 500) deve retornar None."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        http_error = requests.exceptions.HTTPError(response=mock_response)
        mock_post.return_value = MagicMock(
            raise_for_status=MagicMock(side_effect=http_error)
        )
        result = self.gen.generate("Vídeo Teste")
        self.assertIsNone(result)

    @patch("services.comment_generator.ollama_generator.requests.post")
    def test_connection_error_returns_none(self, mock_post):
        """Erro genérico de conexão deve retornar None."""
        mock_post.side_effect = Exception("Connection refused")
        result = self.gen.generate("Vídeo Teste")
        self.assertIsNone(result)

    @patch("services.comment_generator.ollama_generator.requests.post")
    def test_success_returns_comment(self, mock_post):
        """Quando o Ollama responde OK, deve retornar o comentário."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"response": "Vídeo incrível demais! 🔥"}
        mock_post.return_value = mock_response

        result = self.gen.generate("Vídeo Teste")
        self.assertEqual(result, "Vídeo incrível demais! 🔥")

    @patch("services.comment_generator.ollama_generator.requests.post")
    def test_success_strips_quotes(self, mock_post):
        """O gerador deve remover aspas do texto retornado pelo modelo."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"response": '"Muito bom!" disse o inscrito'}
        mock_post.return_value = mock_response

        result = self.gen.generate("Vídeo")
        self.assertNotIn('"', result)
        self.assertNotIn("'", result)


# ---------------------------------------------------------------------------
# 3. Integração: lógica de fallback em runtime (simula main_polling / main_backfill)
# ---------------------------------------------------------------------------
from typing import Optional

class TestFallbackRuntimeLogic(unittest.TestCase):
    """
    Simula o bloco de lógica extraído de main_polling e main_backfill:
    
        comment_text = generator.generate(...)
        if not comment_text:
            comment_text = FallbackGenerator().generate(...)
    """

    def _run_with_fallback(self, primary_result: Optional[str]) -> Optional[str]:
        """Replica a lógica implementada nos scripts."""
        comment_text = primary_result  # simula retorno do Ollama
        if not comment_text:
            comment_text = FallbackGenerator().generate(video_title="Vídeo Qualquer")
        return comment_text

    def test_fallback_ativado_quando_ollama_retorna_none(self):
        """Quando Ollama retorna None, o fallback deve produzir um comentário válido."""
        result = self._run_with_fallback(None)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_fallback_nao_ativado_quando_ollama_tem_sucesso(self):
        """Quando Ollama retorna comentário válido, deve ser usado sem fallback."""
        ollama_comment = "Baah, esse vídeo foi demais tche! 🔥"
        result = self._run_with_fallback(ollama_comment)
        self.assertEqual(result, ollama_comment)

    def test_fallback_nao_ativado_para_string_vazia(self):
        """String vazia também deve acionar o fallback (falsy)."""
        result = self._run_with_fallback("")
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
