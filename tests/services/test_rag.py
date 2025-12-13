from unittest.mock import MagicMock
from app.services.rag import RagClient
import pytest, requests
from app.models import ChromaDbResult, MessageDocuments, Message, RerankResponse, RerankItem
from app.core.errors import RagClientFailedError


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

def test_chroma_query_success(rag_client):
    fake_msg_docs = MessageDocuments(
        message=Message(
            role="user",
            content="fake content"
        )
    )

    fake_chromadb_results = [ChromaDbResult(id="id", document="document", metadata={"meta": "data"})]
    fake_rerank_response = RerankResponse(query="query", results=[RerankItem(id="id", score=1.1)])
    print(type(fake_rerank_response))
    rag_client.emb_client.embed = MagicMock(return_value=[1.1, 2.2, 3.3])
    rag_client._query = MagicMock(return_value=fake_chromadb_results)
    rag_client.emb_client.rerank = MagicMock(return_value=fake_rerank_response)
    rag_client._filter_results = MagicMock(return_value=fake_chromadb_results)
    
    arguments = {"query_text": "query text",}
    collection = "gdpr"
    tool_call_id = "1234"
    result = rag_client.chroma_query(
        arguments=arguments,
        collection=collection,
        tool_call_id=tool_call_id
    )

    rag_client.emb_client.embed.assert_called_once_with(text="query text")
    rag_client._query.assert_called_once_with(query_embedding=[1.1, 2.2, 3.3], collection=collection)
    rag_client.emb_client.rerank.assert_called_once_with(query_text="query text", results=fake_chromadb_results)
    rag_client._filter_results.assert_called_once_with(results=fake_chromadb_results, reranked=fake_rerank_response.results)
    assert isinstance(result, MessageDocuments)

def test_chroma_query_handle_resp_error(rag_client):
    rag_client.emb_client.embed = MagicMock(
        side_effect=requests.HTTPError("500")
    )
    
    rag_client._query = MagicMock()
    rag_client.emb_client.rerank = MagicMock()
    rag_client._filter_results = MagicMock()
    with pytest.raises(RagClientFailedError) as exc:
        arguments = {"query_text": "query text",}
        collection = "gdpr"
        tool_call_id = "1234"
        result = rag_client.chroma_query(
            arguments=arguments,
            collection=collection,
            tool_call_id=tool_call_id
        )
    
    rag_client._query.assert_not_called()
    rag_client.emb_client.rerank.assert_not_called()
    rag_client._filter_results.assert_not_called()

    # exception chaining preserved
    assert isinstance(exc.value.__cause__, requests.HTTPError)
