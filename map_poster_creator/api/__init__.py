"""
FastAPI application for creating map posters from polygon coordinates.
"""

from fastapi import FastAPI

from map_poster_creator.api.endpoints import register_endpoints

app = FastAPI(
    title="Map Poster Creator API",
    description="API for creating map posters from polygon coordinates",
    version="0.8.0",
)

# Register all endpoints
register_endpoints(app)

# Make app available for uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

