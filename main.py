# main.py
import os
import json
import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
import uvicorn

app = FastAPI(title="NumApis Checker", description="Check mobile number details")

# Templates directory
templates = Jinja2Templates(directory="templates")

# API endpoint
API_BASE_URL = "https://numapis.beastaccuserrr.workers.dev/"
API_KEY = "PAPAKIAPI"  # The API key from the URL

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page"""
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "result": None, "error": None}
    )

@app.post("/search", response_class=HTMLResponse)
async def search_number(
    request: Request,
    number: str = Form(...),
    pin: str = Form(...)
):
    """Search for a mobile number with PIN and return results"""
    error = None
    result = None
    
    # Validate number
    if not number or not number.isdigit() or len(number) != 10:
        error = "Invalid mobile number! Please enter a valid 10-digit number."
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "result": None, "error": error}
        )
    
    # Validate PIN
    if not pin or not pin.isdigit() or len(pin) != 4:
        error = "Invalid PIN! Please enter a valid 4-digit PIN."
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "result": None, "error": error}
        )
    
    # Check if PIN matches (hardcoded for now - you can change this)
    VALID_PIN = "8815"  # The PIN you mentioned
    
    if pin != VALID_PIN:
        error = "Invalid PIN! Access denied."
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "result": None, "error": error}
        )
    
    try:
        # Make API request
        async with httpx.AsyncClient(timeout=30.0) as client:
            api_url = f"{API_BASE_URL}?apikey={API_KEY}&number={number}"
            response = await client.get(api_url)
            
            if response.status_code != 200:
                error = f"API Error: Status code {response.status_code}"
                return templates.TemplateResponse(
                    "index.html",
                    {"request": request, "result": None, "error": error}
                )
            
            data = response.json()
            
            # Check if the API response indicates success and has results
            if data.get("success"):
                api_result = data.get("result", {})
                status = api_result.get("status")
                
                if status == "success" and api_result.get("count", 0) > 0:
                    # Data found
                    result = {
                        "status": "found",
                        "queried_number": api_result.get("queried_number"),
                        "timestamp": api_result.get("timestamp"),
                        "count": api_result.get("count", 0),
                        "records": api_result.get("results", [])
                    }
                elif status == "no_results" or api_result.get("count", 0) == 0:
                    # No data found
                    result = {
                        "status": "not_found",
                        "queried_number": api_result.get("queried_number", number),
                        "message": "No records found for this number"
                    }
                else:
                    # Other API response
                    error = "Unexpected API response format"
            else:
                error = "API returned unsuccessful response"
                
    except httpx.TimeoutException:
        error = "Request timeout! Please try again."
    except httpx.RequestError as e:
        error = f"Network error: {str(e)}"
    except json.JSONDecodeError:
        error = "Invalid response from API"
    except Exception as e:
        error = f"An unexpected error occurred: {str(e)}"
    
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "result": result, "error": error}
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
