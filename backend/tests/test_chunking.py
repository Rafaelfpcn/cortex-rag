from app.services.chunking_service import RecursiveTextChunker

def test_recursive_chunking_size_and_overlap():
    chunker = RecursiveTextChunker(chunk_size=100, chunk_overlap=20)
    text = "Este é o primeiro parágrafo longo de teste corporativo.\n\nEste é o segundo parágrafo que adiciona mais informações essenciais ao manual."

    chunks = chunker.split_text(text)
    assert len(chunks) >= 2
    assert chunks[0]["chunk_index"] == 0
    assert "metadata" in chunks[0]
    assert chunks[0]["metadata"]["estimated_page"] == 1
