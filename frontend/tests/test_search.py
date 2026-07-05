import frontend.services.search as search

class TestSearchWeb:
    def test_calls_correct_endpoint_with_defaults(self, mock_call):
        stub = mock_call(search, return_value={"results": [{"url": "https://example.com"}]})
        result = search.search_web("tok", "tavily", "python testing")
        stub.assert_called_once_with(
            "POST", "/search/web",
            token="tok",
            json={
                "engine": "tavily",
                "query": "python testing",
                "num_results": 10,
                "search_depth": "basic",
            },
        )
        assert result == [{"url": "https://example.com"}]

    def test_custom_params_forwarded(self, mock_call):
        stub = mock_call(search, return_value={"results": []})
        search.search_web("tok", "exa", "rust vs go", num_results=3, search_depth="advanced")
        stub.assert_called_once_with(
            "POST", "/search/web",
            token="tok",
            json={
                "engine": "exa",
                "query": "rust vs go",
                "num_results": 3,
                "search_depth": "advanced",
            },
        )

    def test_none_response_falls_back_to_empty_list(self, mock_call):
        mock_call(search, return_value=None)
        assert search.search_web("tok", "tavily", "anything") == []

    def test_missing_results_key_falls_back_to_empty_list(self, mock_call):
        mock_call(search, return_value={})
        assert search.search_web("tok", "tavily", "anything") == []


class TestAddSearchResultItems:
    def test_calls_correct_endpoint(self, mock_call):
        stub = mock_call(search, return_value={"added": [], "skipped": []})
        items = [{"url": "https://example.com", "title": "Example", "content": "text"}]
        search.add_search_result_items("tok", "col-1", items)
        stub.assert_called_once_with(
            "POST", "/collections/col-1/items/from-search",
            token="tok", json={"items": items},
        )