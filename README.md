# aegis - Supply Chain Risk Analysis Tool

This tool monitors, analyzes, and predicts supply chain risks caused by geopolitical events.

## Tech Stack
- **Backend:** FastAPI  
- **Frontend:** Streamlit  
- **API Integration:** News APIs, OpenAI GPT API  
- **Database:** TinyDB  

## Running the Project

> 💡 Make sure you have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed.

### Setup

1. Create a `.env` file in the `backend/` folder with the following content:
   ```env
   NEWS_API_KEY=<your_news_api_key>
   OPENAI_API_KEY=<your_openai_api_key>
   ```

2. Build and run the project:
   ```bash
   docker-compose up --build
   ```

3. Once running, the app will be available at:
   [http://localhost:8501](http://localhost:8501)

### Starting & Stopping the App

To stop the running containers:
```bash
docker-compose down
```

To restart the app later, run:
```bash
docker-compose up
```
