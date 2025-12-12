from unittest.mock import MagicMock
from app.services.rag import RagClient
import pytest
from app.models import ChromaDbResult


fake_query_raw_short = {
    "ids": [[
        "doc_001",
        "doc_002",
        "doc_003"
    ]],
    "documents": [[
        "The quick brown fox jumps over the lazy dog.",
        "A second sample document for testing the parser.",
        "Final test document with some additional content."
    ]],
    "metadatas": [[
        {"source": "unit_test", "score": 0.98},
        {"source": "unit_test", "score": 0.87},
        {"source": "unit_test", "score": 0.76}
    ]]
}

fake_query_raw_long = {
    "ids": [[
        "doc_001",
        "doc_002",
        "doc_003",
        "doc_004",
        "doc_005",
        "doc_006",
        "doc_007",
        "doc_008"
    ]],
    "documents": [[
        "The quick brown fox jumps over the lazy dog.",
        "A second sample document for testing the parser.",
        "Final test document with some additional content.",
        "Another document used to ensure list lengths stay consistent.",
        "Fifth test entry containing mock text.",
        "Sixth generated document for validating iteration.",
        "Seventh synthetic record included for completeness.",
        "Eighth and final test document."
    ]],
    "metadatas": [[
        {"source": "unit_test", "score": 0.98},
        {"source": "unit_test", "score": 0.87},
        {"source": "unit_test", "score": 0.76},
        {"source": "unit_test", "score": 0.91},
        {"source": "unit_test", "score": 0.84},
        {"source": "unit_test", "score": 0.82},
        {"source": "unit_test", "score": 0.79},
        {"source": "unit_test", "score": 0.93}
    ]]
}

fake_get_raw_short = {
    "ids": [
        "doc_001",
        "doc_002",
        "doc_003"
    ],
    "documents": [
        "The quick brown fox jumps over the lazy dog.",
        "A second sample document for testing the parser.",
        "Final test document with some additional content."
    ],
    "metadatas": [
        {"source": "unit_test", "score": 0.98},
        {"source": "unit_test", "score": 0.87},
        {"source": "unit_test", "score": 0.76}
    ]
}

fake_get_raw_long = {
    "ids": [
        "doc_001",
        "doc_002",
        "doc_003",
        "doc_004",
        "doc_005",
        "doc_006",
        "doc_007",
        "doc_008"
    ],
    "documents": [
        "The quick brown fox jumps over the lazy dog.",
        "A second sample document for testing the parser.",
        "Final test document with some additional content.",
        "Another document used to ensure list lengths stay consistent.",
        "Fifth test entry containing mock text.",
        "Sixth generated document for validating iteration.",
        "Seventh synthetic record included for completeness.",
        "Eighth and final test document."
    ],
    "metadatas": [
        {"source": "unit_test", "score": 0.98},
        {"source": "unit_test", "score": 0.87},
        {"source": "unit_test", "score": 0.76},
        {"source": "unit_test", "score": 0.91},
        {"source": "unit_test", "score": 0.84},
        {"source": "unit_test", "score": 0.82},
        {"source": "unit_test", "score": 0.79},
        {"source": "unit_test", "score": 0.93}
    ]
}

@pytest.fixture
def mock_embeddings_client():
    mock_client = MagicMock()
    # add more attributes when you need them
    return mock_client

@pytest.fixture
def rag_client(fake_configs, mock_embeddings_client):
    mock_rag_client = RagClient(configs=fake_configs)
    mock_rag_client.emb_client = mock_embeddings_client
    return mock_rag_client

def test__format_query_result_short(rag_client):
    result = rag_client._format_query_result(raw=fake_query_raw_short)
    assert len(result) == 3
    assert isinstance(result[0], ChromaDbResult)
    assert result[0].id == "doc_001"

def test__format_query_result_long(rag_client):
    result = rag_client._format_query_result(raw=fake_query_raw_long)
    assert len(result) == 8
    assert isinstance(result[0], ChromaDbResult)
    assert result[0].id == "doc_001"

def test__format_get_result_short(rag_client):
    result = rag_client._format_get_result(raw=fake_get_raw_short)
    assert len(result) == 3
    assert isinstance(result[0], ChromaDbResult)
    assert result[0].id == "doc_001"

def test__format_get_result_long(rag_client):
    result = rag_client._format_get_result(raw=fake_get_raw_long)
    assert len(result) == 8
    assert isinstance(result[0], ChromaDbResult)
    assert result[0].id == "doc_001"