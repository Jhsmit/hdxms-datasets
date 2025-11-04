from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import files, validation, generation

app = FastAPI(
    title="HDX-MS Dataset Builder API",
    description="API for creating HDX-MS datasets",
    version="0.1.0"
)

# Configure CORS - permissive for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include routers
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(validation.router, prefix="/api/validate", tags=["validation"])
app.include_router(generation.router, prefix="/api/generate", tags=["generation"])


@app.get("/")
async def root():
    return {
        "message": "HDX-MS Dataset Builder API",
        "docs": "/docs",
        "version": "0.1.0"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
