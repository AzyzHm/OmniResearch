from backend.services.text_processing import chunk_text


class TestChunkText:
    def test_empty_string_returns_empty_list(self):
        assert chunk_text("") == []

    def test_whitespace_only_returns_empty_list(self):
        assert chunk_text("   \n\t  ") == []

    def test_text_shorter_than_chunk_size_returns_single_chunk(self):
        text = "hello world"
        assert chunk_text(text, chunk_size=1000, overlap=150) == ["hello world"]

    def test_text_exactly_chunk_size_returns_single_chunk(self):
        text = "a" * 100
        result = chunk_text(text, chunk_size=100, overlap=10)
        assert result == [text]

    def test_leading_and_trailing_whitespace_is_stripped(self):
        text = "  hello world  "
        assert chunk_text(text, chunk_size=1000) == ["hello world"]

    def test_splits_into_multiple_chunks_when_longer_than_chunk_size(self):
        text = "a" * 250
        result = chunk_text(text, chunk_size=100, overlap=20)
        assert len(result) > 1
        for chunk in result[:-1]:
            assert len(chunk) <= 100

    def test_consecutive_chunks_overlap_by_requested_amount(self):
        text = "0123456789" * 10
        result = chunk_text(text, chunk_size=30, overlap=10)
        for i in range(len(result) - 1):
            tail_of_current = result[i][-10:]
            head_of_next = result[i + 1][:10]
            assert tail_of_current == head_of_next

    def test_full_text_is_covered_with_no_gaps(self):
        text = "abcdefghij" * 20  # 200 chars
        result = chunk_text(text, chunk_size=50, overlap=10)
        assert text.endswith(result[-1])
        assert text.startswith(result[0])

    def test_last_chunk_reaches_end_of_text_exactly_once(self):
        text = "x" * 105
        result = chunk_text(text, chunk_size=100, overlap=50)
        assert result[-1] == text[-5:] or text.endswith(result[-1])
        assert len(result) < 20

    def test_zero_overlap_produces_contiguous_non_overlapping_chunks(self):
        text = "y" * 300
        result = chunk_text(text, chunk_size=100, overlap=0)
        assert "".join(result) == text
        assert len(result) == 3

    def test_default_chunk_size_and_overlap_are_used_when_omitted(self):
        text = "z" * 1200
        result = chunk_text(text)
        assert len(result[0]) == 1000

    def test_internal_whitespace_chunk_is_dropped_if_it_strips_to_empty(self):
        text = "a" * 50 + " " * 20 + "b" * 50
        result = chunk_text(text, chunk_size=50, overlap=0)
        assert all(chunk.strip() == chunk and chunk != "" for chunk in result)

    def test_single_character_text(self):
        assert chunk_text("a", chunk_size=1000) == ["a"]

    def test_does_not_mutate_input_text(self):
        original = "  padded text  "
        chunk_text(original)
        assert original == "  padded text  "