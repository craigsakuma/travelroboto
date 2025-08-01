# TravelBot Tests

This directory contains unit tests for the TravelBot application.

## Running Tests

### Prerequisites
Make sure you have the required testing dependencies installed:
```bash
pip install pytest pytest-mock
```

### Running All Tests
To run all tests in the tests directory:
```bash
python -m pytest tests/ -v
```

### Running Specific Test Files
To run tests for a specific module:
```bash
python -m pytest tests/test_ask_question.py -v
```

### Test Coverage
To run tests with coverage reporting (requires pytest-cov):
```bash
pip install pytest-cov
python -m pytest tests/ --cov=app --cov-report=html
```

## Test Structure

### `test_ask_question.py`
Comprehensive unit tests for the `ask_question` function in `app.chatbot.conversation`:

- **TestFormatHistory**: Tests the `format_history` helper function
  - Empty message lists
  - Single human/AI messages
  - System message handling (ignored)
  - Complete conversation formatting
  - Special characters and edge cases

- **TestAskQuestion**: Tests the main `ask_question` function
  - Basic functionality with mocked LangChain dependencies
  - Empty conversation history handling
  - Complex conversation scenarios
  - Return value format validation
  - Integration with `format_history`
  - Edge cases (empty strings, whitespace, missing keys)

- **TestIntegration**: Integration tests simulating full conversation flows

### Mocking Strategy
The tests use `unittest.mock` and `pytest-mock` to:
- Mock the LangChain `question_chain` to avoid external API calls
- Mock conversation memory for controlled test scenarios
- Isolate the functions under test from external dependencies

This ensures tests are:
- Fast (no network calls)
- Reliable (no external service dependencies)
- Deterministic (controlled test data)
- Suitable for CI/CD pipelines

## Test Results
All 16 tests pass successfully, covering:
- 6 tests for `format_history` function
- 9 tests for `ask_question` function  
- 1 integration test for full conversation flow

The tests achieve comprehensive coverage of both happy path scenarios and edge cases.
