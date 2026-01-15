import uvicorn
from rag_app.api.factory import create_app

def serve():
    uvicorn.run(
        "rag_app.api.main:app",
        host="0.0.0.0",
        port=8002,
    )
    
app = create_app()
