"""
Unit tests for the ask_question function in app.chatbot.conversation.

This module tests:
- ask_question function behavior with mocked dependencies
- format_history function for proper SMS-style formatting
- Integration between ask_question and format_history
- Edge cases and error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from app.chatbot.conversation import ask_question, format_history


class TestFormatHistory:
    """Test cases for the format_history function."""
    
    def test_format_history_empty_list(self):
        """Test formatting an empty message list."""
        result = format_history([])
        assert result == ""
    
    def test_format_history_single_human_message(self):
        """Test formatting a single human message."""
        messages = [HumanMessage(content="Hello")]
        result = format_history(messages)
        assert result == "You: Hello"
    
    def test_format_history_single_ai_message(self):
        """Test formatting a single AI message."""
        messages = [AIMessage(content="Hi there!")]
        result = format_history(messages)
        assert result == "TravelBot: Hi there!\n----------"
    
    def test_format_history_system_message_ignored(self):
        """Test that system messages are ignored in formatting."""
        messages = [
            SystemMessage(content="System instruction"),
            HumanMessage(content="Hello")
        ]
        result = format_history(messages)
        assert result == "You: Hello"
    
    def test_format_history_conversation_flow(self):
        """Test formatting a complete conversation."""
        messages = [
            HumanMessage(content="What's the weather?"),
            AIMessage(content="It's sunny today!"),
            HumanMessage(content="Thanks!"),
            AIMessage(content="You're welcome!")
        ]
        expected = (
            "You: What's the weather?\n"
            "TravelBot: It's sunny today!\n"
            "----------\n"
            "You: Thanks!\n"
            "TravelBot: You're welcome!\n"
            "----------"
        )
        result = format_history(messages)
        assert result == expected
    
    def test_format_history_unknown_message_type(self):
        """Test handling of unknown message types."""
        # Create a mock message with a custom type
        mock_message = Mock()
        mock_message.content = "Custom content"
        mock_message.type = "custom"
        
        messages = [mock_message]
        result = format_history(messages)
        assert result == "Custom: Custom content"


class TestAskQuestion:
    """Test cases for the ask_question function."""
    
    @pytest.fixture
    def mock_question_chain(self):
        """Fixture to provide a mocked question_chain."""
        with patch('app.chatbot.conversation.question_chain') as mock_chain:
            # Mock the predict method
            mock_chain.predict.return_value = "Mocked AI response"
            
            # Mock the memory and its load_memory_variables method
            mock_memory = Mock()
            mock_chain.memory = mock_memory
            
            yield mock_chain
    
    def test_ask_question_basic_functionality(self, mock_question_chain):
        """Test basic ask_question functionality."""
        # Setup mock memory to return sample conversation
        sample_history = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!")
        ]
        mock_question_chain.memory.load_memory_variables.return_value = {
            "chat_history": sample_history
        }
        
        # Call the function
        result_history, result_clear = ask_question("Hello")
        
        # Verify the question_chain was called correctly
        mock_question_chain.predict.assert_called_once_with(question="Hello")
        mock_question_chain.memory.load_memory_variables.assert_called_once_with({})
        
        # Verify return values
        expected_history = "You: Hello\nTravelBot: Hi there!\n----------"
        assert result_history == expected_history
        assert result_clear == ""
    
    def test_ask_question_empty_history(self, mock_question_chain):
        """Test ask_question with empty conversation history."""
        # Setup mock memory to return empty history
        mock_question_chain.memory.load_memory_variables.return_value = {
            "chat_history": []
        }
        
        # Call the function
        result_history, result_clear = ask_question("First question")
        
        # Verify the function was called
        mock_question_chain.predict.assert_called_once_with(question="First question")
        
        # Verify return values
        assert result_history == ""
        assert result_clear == ""
    
    def test_ask_question_complex_conversation(self, mock_question_chain):
        """Test ask_question with a complex conversation history."""
        # Setup mock memory with complex conversation
        complex_history = [
            HumanMessage(content="What flights do we have?"),
            AIMessage(content="You have flights on March 15th and March 22nd."),
            HumanMessage(content="What time is the first flight?"),
            AIMessage(content="The first flight departs at 8:30 AM."),
            SystemMessage(content="System message - should be ignored")
        ]
        mock_question_chain.memory.load_memory_variables.return_value = {
            "chat_history": complex_history
        }
        
        # Call the function
        result_history, result_clear = ask_question("Thanks for the info")
        
        # Verify the function was called
        mock_question_chain.predict.assert_called_once_with(question="Thanks for the info")
        
        # Verify the formatted history (system message should be ignored)
        expected_history = (
            "You: What flights do we have?\n"
            "TravelBot: You have flights on March 15th and March 22nd.\n"
            "----------\n"
            "You: What time is the first flight?\n"
            "TravelBot: The first flight departs at 8:30 AM.\n"
            "----------"
        )
        assert result_history == expected_history
        assert result_clear == ""
    
    def test_ask_question_with_special_characters(self, mock_question_chain):
        """Test ask_question with special characters in messages."""
        # Setup mock memory with special characters
        special_history = [
            HumanMessage(content="What's the hotel's address?"),
            AIMessage(content="It's at 123 Main St. & 5th Ave, Suite #100!")
        ]
        mock_question_chain.memory.load_memory_variables.return_value = {
            "chat_history": special_history
        }
        
        # Call the function
        result_history, result_clear = ask_question("Question with émojis 🏨")
        
        # Verify the function handles special characters
        mock_question_chain.predict.assert_called_once_with(question="Question with émojis 🏨")
        
        expected_history = (
            "You: What's the hotel's address?\n"
            "TravelBot: It's at 123 Main St. & 5th Ave, Suite #100!\n"
            "----------"
        )
        assert result_history == expected_history
        assert result_clear == ""
    
    def test_ask_question_return_tuple_format(self, mock_question_chain):
        """Test that ask_question always returns a tuple with correct format."""
        # Setup mock memory
        mock_question_chain.memory.load_memory_variables.return_value = {
            "chat_history": [HumanMessage(content="Test")]
        }
        
        # Call the function
        result = ask_question("Test question")
        
        # Verify return type and structure
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)  # formatted history
        assert result[1] == ""  # clear string for UI
    
    @patch('app.chatbot.conversation.format_history')
    def test_ask_question_calls_format_history(self, mock_format_history, mock_question_chain):
        """Test that ask_question properly calls format_history."""
        # Setup mocks
        sample_history = [HumanMessage(content="Test")]
        mock_question_chain.memory.load_memory_variables.return_value = {
            "chat_history": sample_history
        }
        mock_format_history.return_value = "Formatted output"
        
        # Call the function
        result_history, result_clear = ask_question("Test")
        
        # Verify format_history was called with the correct history
        mock_format_history.assert_called_once_with(sample_history)
        assert result_history == "Formatted output"
    
    def test_ask_question_handles_missing_chat_history_key(self, mock_question_chain):
        """Test ask_question handles missing chat_history key gracefully."""
        # Setup mock memory without chat_history key
        mock_question_chain.memory.load_memory_variables.return_value = {}
        
        # This should raise a KeyError, which is expected behavior
        with pytest.raises(KeyError):
            ask_question("Test question")
    
    def test_ask_question_with_empty_string(self, mock_question_chain):
        """Test ask_question with empty string input."""
        # Setup mock memory
        mock_question_chain.memory.load_memory_variables.return_value = {
            "chat_history": []
        }
        
        # Call with empty string
        result_history, result_clear = ask_question("")
        
        # Verify the function was called with empty string
        mock_question_chain.predict.assert_called_once_with(question="")
        assert result_history == ""
        assert result_clear == ""
    
    def test_ask_question_with_whitespace_only(self, mock_question_chain):
        """Test ask_question with whitespace-only input."""
        # Setup mock memory
        mock_question_chain.memory.load_memory_variables.return_value = {
            "chat_history": []
        }
        
        # Call with whitespace
        result_history, result_clear = ask_question("   \n\t   ")
        
        # Verify the function was called with the whitespace string
        mock_question_chain.predict.assert_called_once_with(question="   \n\t   ")
        assert result_clear == ""


class TestIntegration:
    """Integration tests for ask_question and related functions."""
    
    @patch('app.chatbot.conversation.question_chain')
    def test_full_conversation_flow(self, mock_question_chain):
        """Test a complete conversation flow simulation."""
        # Simulate a conversation building up over multiple calls
        conversation_states = [
            # First question
            [HumanMessage(content="Hello")],
            # After first response
            [
                HumanMessage(content="Hello"),
                AIMessage(content="Hi! How can I help with your trip?")
            ],
            # After second question
            [
                HumanMessage(content="Hello"),
                AIMessage(content="Hi! How can I help with your trip?"),
                HumanMessage(content="What flights do I have?")
            ],
            # After second response
            [
                HumanMessage(content="Hello"),
                AIMessage(content="Hi! How can I help with your trip?"),
                HumanMessage(content="What flights do I have?"),
                AIMessage(content="You have a flight on March 15th at 8:30 AM.")
            ]
        ]
        
        questions = ["Hello", "What flights do I have?"]
        
        for i, question in enumerate(questions):
            # Setup mock for this iteration
            mock_question_chain.memory.load_memory_variables.return_value = {
                "chat_history": conversation_states[i * 2 + 1]  # Get the "after response" state
            }
            
            # Call ask_question
            history, clear = ask_question(question)
            
            # Verify the call
            mock_question_chain.predict.assert_called_with(question=question)
            assert clear == ""
            assert isinstance(history, str)
