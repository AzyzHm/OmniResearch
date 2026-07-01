import pytest
from pydantic import ValidationError

from backend.models.auth import RegisterRequest
from backend.models.project import ProjectCreate, ProjectUpdate
from backend.models.collection import CollectionCreate
from backend.models.chat import ChatCreate, ChatUpdate, ChatMessageRequest


class TestRegisterRequest:
    def test_valid(self):
        r = RegisterRequest(username="alice", password="secret123")
        assert r.username == "alice"

    def test_username_stripped(self):
        r = RegisterRequest(username="  bob  ", password="secret123")
        assert r.username == "bob"

    def test_username_too_short(self):
        with pytest.raises(ValidationError, match="at least 3"):
            RegisterRequest(username="ab", password="secret123")

    def test_username_too_long(self):
        with pytest.raises(ValidationError, match="at most 50"):
            RegisterRequest(username="a" * 51, password="secret123")

    def test_username_invalid_chars(self):
        with pytest.raises(ValidationError, match="letters, digits"):
            RegisterRequest(username="bad user!", password="secret123")

    def test_username_allows_dash_and_underscore(self):
        r = RegisterRequest(username="my_user-name", password="secret123")
        assert r.username == "my_user-name"

    def test_password_too_short(self):
        with pytest.raises(ValidationError, match="at least 8"):
            RegisterRequest(username="alice", password="short")

    def test_password_minimum_length(self):
        r = RegisterRequest(username="alice", password="12345678")
        assert r.password == "12345678"


class TestProjectModels:
    def test_create_valid(self):
        p = ProjectCreate(name="My Project")
        assert p.name == "My Project"

    def test_create_strips_whitespace(self):
        p = ProjectCreate(name="  My Project  ")
        assert p.name == "My Project"

    def test_create_empty_name_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            ProjectCreate(name="   ")

    def test_create_name_too_long(self):
        with pytest.raises(ValidationError, match="100 characters"):
            ProjectCreate(name="x" * 101)

    def test_create_name_exactly_100(self):
        p = ProjectCreate(name="x" * 100)
        assert len(p.name) == 100

    def test_update_empty_raises(self):
        with pytest.raises(ValidationError):
            ProjectUpdate(name="")


class TestCollectionCreate:
    def test_valid_documents(self):
        c = CollectionCreate(name="Docs", type="documents")
        assert c.type == "documents"

    def test_valid_urls(self):
        c = CollectionCreate(name="Links", type="urls")
        assert c.type == "urls"

    def test_valid_text(self):
        c = CollectionCreate(name="Notes", type="text")
        assert c.type == "text"

    def test_invalid_type(self):
        with pytest.raises(ValidationError, match="one of"):
            CollectionCreate(name="Bad", type="image")

    def test_empty_name(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            CollectionCreate(name="  ", type="documents")

    def test_name_stripped(self):
        c = CollectionCreate(name="  My Col  ", type="urls")
        assert c.name == "My Col"


class TestChatModels:
    def test_create_default_name(self):
        c = ChatCreate()
        assert c.name == "New Chat"

    def test_create_blank_falls_back_to_default(self):
        c = ChatCreate(name="   ")
        assert c.name == "New Chat"

    def test_update_valid(self):
        c = ChatUpdate(name="Renamed")
        assert c.name == "Renamed"

    def test_update_empty_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            ChatUpdate(name="  ")

    def test_message_request_valid(self):
        m = ChatMessageRequest(message="Hello")
        assert m.message == "Hello"

    def test_message_request_empty_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            ChatMessageRequest(message="   ")

    def test_message_request_no_history_field(self):
        """History is now stored in DB — the request model only takes a message."""
        m = ChatMessageRequest(message="Follow-up")
        assert m.message == "Follow-up"
        assert not hasattr(m, "history")