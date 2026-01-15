# rag_app

## About

This is an app for retrieval-augmented generation (RAG)-enhanced chat with an LLM on the General Data Protection Regulation (GDPR). Partly, it is intended to demo what I can do with Python; partly it's to build an app to help my wife with her work.

Originally, I tried to use Open-WebUI for this, but the RAG and tool-calling options were too opinionated and black-boxy, so I rolled my own. Right now, this app is tightly-coupled in several ways that would make it hard for someone who is not me to use it:

* It calls a separate REST API for embeddings. That one is [also on my GitHub](https://github.com/pjkrupa/transformer), but it's nothing special, it's just a FastAPI endpoint that uses the `sentence_transformers` library. I'm running it separately because the models can be large. I might roll it into `rag_app` in the future and include an option for calling OpenAI or Gemini embeddings.

* For the vector database, you need to run a separate Chroma server.

* That Chroma server needs to have collections in its database. For mine, I scraped and chunked the GDPR and all the recommendations and guidelines issued by the European Data Protection Board (EDPB). It took a lot of work. You can also do this work, if you want.

* The `app.tool_handler` module and `tools.registry` define tools and logic that are specific to how I injested the data into Chroma.

## Installation

If you want to install `rag_app` anyway, clone the repo and set a `configs.yaml` file to your specifications (see examples in the `configurations` folder). Create an `.env` file defining `CONFIGS_PATH` (path to your `configs.yaml` file) and `API_KEY` (key for your LLM provider, leave blank if there is none). Then: 

    cd rag_app
    uv venv
    source .venv/bin/activate
    uv pip install .

Then to start the `uvicorn` server running on port 8002:

    rag-app-serve

Visit `http://localhost:8002` and chat away! But tool calling/RAG won't work unless the embeddings and Chroma servers are running. 

## Looking ahead

My roadmap includes eventually decoupling the specifics of the Chroma database from the `rag_app` logic. This would make it possible to use this app for any RAG-related tasks on any subject, with any Chroma corpus, as defined by the user.

For the moment though, I am focusing on fleshing out logging and testing.

In the meantime, feel free to play with it or make suggestions.

I did not use any code generation tools to build this. However, I did use ChatGPT for debugging, retrieving documentation, and rubber ducky-type help.