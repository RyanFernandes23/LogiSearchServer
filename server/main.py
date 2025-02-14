from fastapi import FastAPI, Body, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from duckduckgo_search import DDGS
import json
from responder import get_response
import requests
import base64
from io import BytesIO
import os
import logging
import uvicorn



app = FastAPI()

ddgs = DDGS()

# Allow your frontend origin
origins = [
    "http://192.168.29.125:3000",  # Local frontend
    "http://localhost:3000",       # Local frontend
    "https://logi-search-client-be3i8coa8-ryan-fernandes-projects.vercel.app",  # Vercel frontend
    "https://logi-search-client.vercel.app"  # Main Vercel deployment
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of allowed origins
    allow_credentials=True,  # Allow cookies and credentials
    allow_methods=["*"],     # Allow all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],     # Allow all headers
)

# PlantNet API configuration
PLANTNET_API_KEY = os.getenv('PLANTNET_API_KEY')  # Add this to your .env file
PLANTNET_API_URL = "https://my-api.plantnet.org/v2/identify/all"

@app.post("/imagelinks")
async def imagelinks(message: str = Body(..., embed=True)):
    query = message
    results = ddgs.images(query, max_results=5, safesearch="moderate")
    return results

@app.post("/textlinks")
async def textlinks(message: str = Body(..., embed=True)):
    query = message
    response = get_response(query)
    return {"response": response}

@app.post("/identify-plant")
async def identify_plant(
    file: UploadFile = File(...),
    organ: str = Form("leaf")  # Default to leaf if not specified
):
    try:
        # Read image file
        contents = await file.read()
        
        # Prepare the image for PlantNet API
        image_data = base64.b64encode(contents).decode('utf-8')
        
        # Make request to PlantNet API
        data = {
            'images': [image_data],
            'organs': [organ]  # Use the specified organ
        }
        
        params = {
            'api-key': PLANTNET_API_KEY
        }
        
        response = requests.post(
            PLANTNET_API_URL,
            json=data,
            params=params
        )
        
        if response.status_code == 200:
            result = response.json()
            # Extract relevant information
            best_match = result['results'][0] if result['results'] else None
            
            if best_match:
                return {
                    "species": best_match['species']['scientificNameWithoutAuthor'],
                    "common_names": best_match['species'].get('commonNames', []),
                    "family": best_match['species']['family']['scientificNameWithoutAuthor'],
                    "genus": best_match['species']['genus']['scientificNameWithoutAuthor'],
                    "confidence": best_match['score'],
                    "images": [img['url'] for img in best_match['images']],
                    "organ": organ  # Include the organ in the response
                }
            
        return {"error": "No plant matches found"}
        
    except Exception as e:
        logger.error(f"Plant identification error: {str(e)}")
        return {"error": f"Failed to identify plant: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1, timeout_keep_alive=30)
