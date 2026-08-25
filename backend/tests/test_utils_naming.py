from utils.naming import next_unique_name


class TestNextUniqueName:
    def test_returns_desired_when_no_collision(self):
        assert next_unique_name("Report", []) == "Report"
        assert next_unique_name("Report", ["Other"]) == "Report"

    def test_appends_suffix_on_first_collision(self):
        assert next_unique_name("Report", ["Report"]) == "Report (2)"

    def test_case_insensitive_collision(self):
        assert next_unique_name("Report", ["report"]) == "Report (2)"
        assert next_unique_name("REPORT", ["Report"]) == "REPORT (2)"

    def test_increments_past_multiple_existing_suffixes(self):
        existing = ["Report", "Report (2)", "Report (3)"]
        assert next_unique_name("Report", existing) == "Report (4)"

    def test_increments_when_renaming_an_already_suffixed_name(self):
        assert next_unique_name("Report (2)", ["Report (2)"]) == "Report (3)"

    def test_fills_gaps_by_scanning_forward(self):
        existing = ["Report", "Report (2)", "Report (4)"]
        assert next_unique_name("Report", existing) == "Report (3)"

    def test_default_new_chat_names_get_numbered(self):
        assert next_unique_name("New Chat", []) == "New Chat"
        assert next_unique_name("New Chat", ["New Chat"]) == "New Chat (2)"
        assert (
            next_unique_name("New Chat", ["New Chat", "New Chat (2)"])
            == "New Chat (3)"
        )

    def test_empty_existing_names_iterable(self):
        assert next_unique_name("Anything", []) == "Anything"