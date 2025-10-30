# ✈️ AI Travel Itinerary Chatbot

An AI-powered chatbot designed to answer questions about your personal travel itinerary. This project uses natural language processing to help travelers get quick and accurate answers about their plans, such as flights, accommodations, activities, and more.

## ✨ Features

*   **Natural Language Queries:** Ask questions about your travel plans in plain English.
*   **Context-Aware:** Understands the context of your conversation, including dates, locations, and activities.
*   **Customizable:** Can be adapted to any travel itinerary.
*   **Flexible LLM Support:** Supports both local and API-based language models.
*   **Multiple Data Sources:** Can store and retrieve itinerary information from JSON files or a PostgreSQL database.

For more detailed information about the project's requirements, please refer to the [product_requirements.md](product_requirements.md) file.

## 🚀 Getting Started

### Prerequisites

*   Python 3.11.7 or higher
*   PostgreSQL

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/craigsakuma/travelroboto.git
    ```
2.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

1.  Create a `.env` file in the root of the project.
2.  Add the following environment variables to the `.env` file:

    ```
    DATABASE_URL=<your_postgresql_database_url>
    OPENAI_API_KEY=<your_openai_api_key>
    TRAVELBOT_GMAIL_CLIENT_ID=<your_gmail_client_id>
    TRAVELBOT_GMAIL_CLIENT_SECRET=<your_gmail_client_secret>
    TWILIO_ACCOUNT_SID=<your_twilio_account_sid>
    TWILIO_AUTH_TOKEN=<your_twilio_auth_token>
    TWILIO_PHONE_NUMBER=<your_twilio_phone_number>
    ```

### Running the Application

```bash
uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
```

## Usage

Once the application is running, you can interact with the chatbot through the web interface or the API.

*   **Web Interface:** Open your browser and navigate to `http://localhost:8000`.
*   **API:** The API documentation is available at `http://localhost:8000/docs`.

## ✅ Testing

This project uses `pytest` for testing.

*   **Run all tests:**
    ```bash
    pytest
    ```
*   **Run tests with coverage:**
    ```bash
    pytest --cov=app
    ```

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 📧 Contact

Craig Sakuma - craig.sakuma@gmail.com

Project Link: [https://github.com/craigsakuma/travelroboto](https://github.com/craigsakuma/travelroboto)