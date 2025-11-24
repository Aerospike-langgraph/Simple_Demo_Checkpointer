# LangGraph + Aerospike + Ollama Checkpointing Demo

This project is a small demo that shows how to use:

- **LangGraph** for chat + tool calling
- **Aerospike** as a LangGraph **checkpoint store**
- **Ollama** (Llama) as the **LLM backend**
- **FastAPI** to expose a simple `/chat` API

The cool part:  
Even if you stop/restart the **app** container, the conversation continues because state is stored in **Aerospike**, not in the container.

---

## Services

`docker-compose.yml` runs:

- `aerospike` – Aerospike server (`3000–3002`)
- `tools` – Aerospike tools helper container (for `aql`, etc.)
- `ollama` – Ollama server (`11434`)
- `app` – FastAPI + LangGraph demo app (`8000`)

The `app` uses:

- `AEROSPIKE_HOST=aerospike`
- `AEROSPIKE_PORT=3000`
- `OLLAMA_BASE_URL=http://ollama:11434`

If you want to use the Aerospike checkpointer **outside Docker** (e.g., in a local virtualenv), you can install it directly from Git:

```bash
pip install git+https://github.com/Aerospike-langgraph/checkpointer.git
```

## 1. Build the app image

From the folder containing `docker-compose.yml`:

```bash
docker compose build
```
## 2. Start all services

```bash
docker compose up -d
```
This will start all the services. Can check if containers are running using

```bash
docker ps
```

## 3. Pull a model into Ollama

```bash
docker exec -it ollama bash
ollama pull llama3
```
Choosing the LLM Model:

The app uses the model specified by the environment variable OLLAMA_MODEL.
You can set this inside the app service in docker-compose.yml:

Just update OLLAMA_MODEL to the model you want to use. (In docker yml file inside service environment)

## 4. Use the Chat API

The FastAPI app exposes:
Endpoint: POST /chat
Body:
```json
{
  "thread_id": "<string>",
  "message": "<user message>"
}
```
Start a conversation:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "demo-1",
    "message": "Hello"
  }'
```

Can continue using same thread or create multiple threads.



