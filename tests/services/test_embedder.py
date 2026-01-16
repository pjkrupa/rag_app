import pytest, logging
from unittest.mock import patch, MagicMock
from rag_app.app.core.config import Configurations
from rag_app.app.services.embeddings import EmbeddingsClient
from rag_app.app.models import *

@pytest.fixture
def embeder(fake_configs):
    return EmbeddingsClient(configs=fake_configs)

def test_embedder_output(embeder):
    fake_embedding = [0.1, 0.2, 0.3]
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"embedding": fake_embedding}
    mock_resp.status_code = 200
    with patch("rag_app.app.services.embeddings.requests.post", return_value=mock_resp):
        result = embeder.embed("test text")
    assert result == fake_embedding