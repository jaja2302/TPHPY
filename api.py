from fastapi import FastAPI, HTTPException, Query, Depends, Security, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from typing import List, Dict, Optional
import asyncio
import json
import os
import time
import hashlib
import secrets
from datetime import datetime, timedelta
from pydantic import BaseModel
from collections import defaultdict
import re

# Import config
from config import HOST, PORT

# Import from main.py
from main import (
    TPH, get_tph_data, nearest_neighbor_from_tph_number, 
    update_tph_numbers_partial, create_kml,
    init_db, close_db
)

# Security Configuration
API_KEYS = {
    "tph_admin_2024": {"name": "TPH Admin", "permissions": ["read", "write", "admin"]},
    "tph_read_2024": {"name": "TPH Reader", "permissions": ["read"]},
    "tph_operator_2024": {"name": "TPH Operator", "permissions": ["read", "write"]}
}

# Rate limiting storage (in production, use Redis)
request_counts = defaultdict(list)
RATE_LIMIT_REQUESTS = 100  # requests per window
RATE_LIMIT_WINDOW = 3600   # 1 hour in seconds

# Security dependencies
security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API key from Authorization header"""
    api_key = credentials.credentials
    if api_key not in API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return API_KEYS[api_key]

def check_permission(required_permission: str):
    """Check if API key has required permission"""
    def permission_checker(user_info: dict = Depends(verify_api_key)):
        if required_permission not in user_info["permissions"]:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {required_permission}"
            )
        return user_info
    return permission_checker

def rate_limit_check(request: Request):
    """Simple rate limiting based on IP address"""
    client_ip = request.client.host
    current_time = time.time()
    
    # Clean old requests
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]
    
    # Check rate limit
    if len(request_counts[client_ip]) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT_REQUESTS} requests per hour."
        )
    
    # Add current request
    request_counts[client_ip].append(current_time)
    return True

def validate_filters(dept_abbr: Optional[str], divisi_abbr: Optional[str], blok_kode: Optional[str]):
    """Validate input filters - Updated to allow more characters"""
    # Allow alphanumeric, underscore, dash, and common characters
    
    # Pattern: letters, numbers, underscore, dash, space
    valid_pattern = re.compile(r'^[a-zA-Z0-9_\-\s]+$')
    
    if dept_abbr and (len(dept_abbr) > 20 or not valid_pattern.match(dept_abbr)):
        raise HTTPException(status_code=400, detail="Invalid dept_abbr format")
    
    if divisi_abbr and (len(divisi_abbr) > 20 or not valid_pattern.match(divisi_abbr)):
        raise HTTPException(status_code=400, detail="Invalid divisi_abbr format")
    
    if blok_kode and (len(blok_kode) > 20 or not valid_pattern.match(blok_kode)):
        raise HTTPException(status_code=400, detail="Invalid blok_kode format")

app = FastAPI(
    title="TPH Route Optimizer API",
    description="Secure API untuk optimasi rute TPH menggunakan Nearest Neighbor Algorithm",
    version="1.2.0",
    docs_url="/docs",  # Will require API key
    redoc_url="/redoc"  # Will require API key
)

# Security Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        
        # Allow private network ranges for company use
        "http://10.*",
        "http://192.168.*",
        "https://10.*", 
        "https://192.168.*"
        "http://10.9.116.*"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# TrustedHostMiddleware disabled for private network compatibility
# For production with public domains, uncomment and configure properly:
# app.add_middleware(
#     TrustedHostMiddleware, 
#     allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
# )

# Response Models
class TPHResponse(BaseModel):
    new_order: int
    id: int
    nomor: int
    tph: str
    dept_abbr: str
    divisi_abbr: str
    lat: float
    lon: float

class OptimizedRouteResponse(BaseModel):
    success: bool
    message: str
    total_points: int
    route: List[TPHResponse]
    kml_file: Optional[str] = None

class UpdateResponse(BaseModel):
    success: bool
    message: str
    updated_count: int

class SecurityInfo(BaseModel):
    authenticated: bool
    user: str
    permissions: List[str]
    rate_limit_remaining: int

# Startup event
@app.on_event("startup")
async def startup_event():
    await init_db()
    print("🔒 API Security enabled with API key authentication")
    print("🔑 Available API keys: tph_admin_2024, tph_read_2024, tph_operator_2024")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

@app.get("/")
async def root():
    return {
        "message": "TPH Route Optimizer API - Secured",
        "version": "1.2.0",
        "security": "API Key Authentication Required",
        "endpoints": {
            "auth_info": "/auth-info",
            "optimize_route": "/optimize-route",
            "update_numbers": "/update-numbers",
            "tph_data": "/tph-data",
            "download_kml": "/download-kml/{filename}"
        },
        "documentation": "Access /docs with valid API key"
    }

@app.get("/auth-info", response_model=SecurityInfo)
async def get_auth_info(
    request: Request,
    user_info: dict = Depends(verify_api_key),
    _: bool = Depends(rate_limit_check)
):
    """Get authentication and rate limit information"""
    client_ip = request.client.host
    remaining_requests = max(0, RATE_LIMIT_REQUESTS - len(request_counts[client_ip]))
    
    return SecurityInfo(
        authenticated=True,
        user=user_info["name"],
        permissions=user_info["permissions"],
        rate_limit_remaining=remaining_requests
    )

@app.get("/optimize-route", response_model=OptimizedRouteResponse)
async def optimize_route(
    request: Request,
    dept_abbr: Optional[str] = Query(None, description="Department abbreviation"),
    divisi_abbr: Optional[str] = Query(None, description="Division abbreviation"),
    blok_kode: Optional[str] = Query(None, description="Block code"),
    generate_kml: bool = Query(False, description="Generate KML file"),
    start_tph_number: int = Query(1, description="Starting TPH number (only TPH >= this number will be reordered)"),
    auto_update: bool = Query(False, description="Automatically update TPH numbers in database"),
    user_info: dict = Depends(check_permission("read")),
    _: bool = Depends(rate_limit_check)
):
    """
    Optimize TPH route using Nearest Neighbor Algorithm starting from specific TPH number
    Requires 'read' permission for preview only
    Requires 'admin' permission for auto_update=true (updates actual TPH numbers)
    
    start_tph_number: Only TPH with nomor >= start_tph_number will be reordered
    TPH with nomor < start_tph_number remain unchanged
    """
    try:
        # Check permissions for auto_update
        if auto_update and "admin" not in user_info["permissions"]:
            raise HTTPException(
                status_code=403,
                detail="Auto update requires admin permission"
            )
        
        # Validate input filters
        validate_filters(dept_abbr, divisi_abbr, blok_kode)
        
        # Get TPH data with filters
        tph_data = await get_tph_data(dept_abbr, divisi_abbr, blok_kode)
        
        if not tph_data:
            raise HTTPException(
                status_code=404, 
                detail="No TPH data found with the specified filters"
            )
        
        # Validate start_tph_number
        if start_tph_number < 1:
            start_tph_number = 1
        
        # Apply Nearest Neighbor algorithm starting from TPH number
        ordered_tph = nearest_neighbor_from_tph_number(tph_data, start_tph_number)
        
        # Auto update database if requested
        update_msg = ""
        if auto_update:
            await update_tph_numbers_partial(ordered_tph, start_tph_number)
            update_msg = f" and TPH numbers updated (starting from nomor {start_tph_number})"
        
        # Convert to response format
        route = []
        for i, tph in enumerate(ordered_tph, 1):
            route.append(TPHResponse(
                new_order=i,
                id=tph.id,
                nomor=tph.nomor,
                tph=tph.kode_tph or "",
                dept_abbr=tph.dept_abbr,
                divisi_abbr=tph.divisi_abbr,
                lat=tph.lat,
                lon=tph.lng
            ))
        
        # Generate KML if requested (requires admin permission for file generation)
        kml_file = None
        if generate_kml:
            if "admin" not in user_info["permissions"]:
                raise HTTPException(
                    status_code=403,
                    detail="KML generation requires admin permission"
                )
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filter_text = f"{dept_abbr or 'all'}_{divisi_abbr or 'all'}_{blok_kode or 'all'}"
            kml_file = f"tph_route_{filter_text}_{timestamp}.kml"
            create_kml(ordered_tph, kml_file)
        
        return OptimizedRouteResponse(
            success=True,
            message=f"Successfully optimized route for {len(ordered_tph)} TPH points{update_msg}",
            total_points=len(ordered_tph),
            route=route,
            kml_file=kml_file
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing route: {str(e)}")

@app.post("/update-numbers", response_model=UpdateResponse)
async def update_tph_numbering(
    request: Request,
    dept_abbr: Optional[str] = Query(None, description="Department abbreviation"),
    divisi_abbr: Optional[str] = Query(None, description="Division abbreviation"),
    blok_kode: Optional[str] = Query(None, description="Block code"),
    start_tph_number: int = Query(1, description="Starting TPH number (only TPH >= this number will be reordered)"),
    user_info: dict = Depends(check_permission("admin")),  # Only admin can renumber
    _: bool = Depends(rate_limit_check)
):
    """
    Update actual TPH numbers in database based on optimized route
    Requires 'admin' permission (critical operation)
    
    start_tph_number: Only TPH with nomor >= start_tph_number will be reordered
    """
    try:
        # Validate input filters
        validate_filters(dept_abbr, divisi_abbr, blok_kode)
        
        # Get and optimize TPH data
        tph_data = await get_tph_data(dept_abbr, divisi_abbr, blok_kode)
        
        if not tph_data:
            raise HTTPException(
                status_code=404, 
                detail="No TPH data found with the specified filters"
            )
        
        if start_tph_number < 1:
            start_tph_number = 1
            
        ordered_tph = nearest_neighbor_from_tph_number(tph_data, start_tph_number)
        
        # Update TPH numbers in database
        await update_tph_numbers_partial(ordered_tph, start_tph_number)
        
        return UpdateResponse(
            success=True,
            message=f"TPH numbers updated successfully (starting from nomor {start_tph_number})",
            updated_count=len([tph for tph in ordered_tph if tph.nomor >= start_tph_number])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating TPH numbers: {str(e)}")

@app.get("/download-kml/{filename}")
async def download_kml(
    filename: str,
    request: Request,
    user_info: dict = Depends(check_permission("admin")),
    _: bool = Depends(rate_limit_check)
):
    """Download generated KML file"""
    try:
        # Validate filename (security check)
        if not filename.endswith('.kml') or '..' in filename or '/' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        file_path = os.path.join(os.getcwd(), filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/vnd.google-earth.kml+xml'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@app.get("/tph-data")
async def get_tph_raw_data(
    request: Request,
    dept_abbr: Optional[str] = Query(None, description="Department abbreviation"),
    divisi_abbr: Optional[str] = Query(None, description="Division abbreviation"),
    blok_kode: Optional[str] = Query(None, description="Block code"),
    user_info: dict = Depends(check_permission("read")),
    _: bool = Depends(rate_limit_check)
):
    """Get raw TPH data without optimization"""
    try:
        # Validate input filters
        validate_filters(dept_abbr, divisi_abbr, blok_kode)
        
        # Get TPH data with filters
        tph_data = await get_tph_data(dept_abbr, divisi_abbr, blok_kode)
        
        if not tph_data:
            raise HTTPException(
                status_code=404, 
                detail="No TPH data found with the specified filters"
            )
        
        # Convert to response format
        data = []
        for tph in tph_data:
            data.append({
                "id": tph.id,
                "nomor": tph.nomor,
                "tph": tph.kode_tph or "",
                "dept_abbr": tph.dept_abbr,
                "divisi_abbr": tph.divisi_abbr,
                "lat": tph.lat,
                "lon": tph.lng
            })
        
        return {
            "success": True,
            "message": f"Retrieved {len(data)} TPH records",
            "total_points": len(data),
            "data": data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving TPH data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT) 