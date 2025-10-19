"""
FastAPI - RESTful API for voucher management and birthday processing
Usage: uvicorn api:app --reload --port 8000
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import csv
from typing import List, Optional
from config import Config
from vouchers import create_voucher, redeem_voucher, get_all_vouchers, get_voucher
from send_birthday import generate_qr_code, get_birthday_today, load_employees

app = FastAPI(
    title=f"{Config.CAFE_NAME} - Birthday Voucher API",
    version="1.0",
    description="RESTful API for voucher management and birthday processing"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============= Models =============
class VoucherResponse(BaseModel):
    employee_id: str
    employee_name: str
    created_at: str
    redeemed: bool
    redeemed_at: Optional[str] = None


class RedeemRequest(BaseModel):
    code: str


class GenerateVoucherRequest(BaseModel):
    employee_id: str
    employee_name: str


class BirthdayWishRequest(BaseModel):
    csv_file: str


# ============= Routes =============
@app.get("/")
def root():
    return {
        "message": f"{Config.CAFE_NAME} - Birthday Voucher API",
        "cafe": Config.CAFE_NAME,
        "location": Config.CAFE_LOCATION,
        "endpoints": {
            "vouchers": "/vouchers",
            "redeem": "POST /redeem",
            "generate": "POST /generate",
            "birthday": "POST /birthday-wishes",
            "config": "/config",
            "health": "/health"
        }
    }


@app.get("/config")
def get_config():
    """Get current configuration"""
    return Config.to_dict()


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/vouchers", response_model=dict)
def get_vouchers():
    """Get all vouchers with QR codes"""
    vouchers = get_all_vouchers()
    
    # Add QR codes to each voucher
    for code, voucher_data in vouchers.items():
        try:
            qr_code = generate_qr_code(code)
            voucher_data['qr_code'] = qr_code
        except Exception as e:
            voucher_data['qr_code'] = f"Error generating QR code: {str(e)}"
    
    return vouchers


@app.get("/vouchers/{code}")
def get_voucher_by_code(code: str):
    """Get voucher by code with QR code"""
    voucher = get_voucher(code)
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    # Add QR code to the voucher
    try:
        qr_code = generate_qr_code(code)
        voucher['qr_code'] = qr_code
    except Exception as e:
        voucher['qr_code'] = f"Error generating QR code: {str(e)}"
    
    return voucher


@app.post("/redeem", response_model=dict)
def redeem(request: RedeemRequest):
    """Redeem a voucher"""
    success, result = redeem_voucher(request.code)
    
    if not success:
        raise HTTPException(status_code=400, detail=result)
    
    return {
        "success": True,
        "employee_id": result['employee_id'],
        "employee_name": result['employee_name'],
        "redeemed_at": result['redeemed_at']
    }


@app.post("/generate", response_model=dict)
def generate_voucher(request: GenerateVoucherRequest):
    """Generate a voucher manually"""
    # Generate QR code first
    today = datetime.now().strftime('%Y%m%d')
    expected_code = f"{request.employee_id}_{today}"
    qr_image = generate_qr_code(expected_code)
    
    # Create voucher with QR code data
    code = create_voucher(request.employee_id, request.employee_name, qr_image)
    
    return {
        "code": code,
        "employee_id": request.employee_id,
        "employee_name": request.employee_name,
        "qr_code": qr_image,
        "created_at": datetime.now().isoformat()
    }


@app.post("/birthday-wishes", response_model=dict)
def send_birthday_wishes_api(request: BirthdayWishRequest):
    """Process birthday wishes from CSV (demo only - returns data without sending)"""
    try:
        employees = load_employees(request.csv_file)
        birthdays = get_birthday_today(employees)
        
        if not birthdays:
            return {"message": "No birthdays today", "count": 0}
        
        result = []
        for emp in birthdays:
            # Use configurable column names
            emp_id = emp.get(Config.CSV_COLUMNS['employee_id'], emp[Config.CSV_COLUMNS['employee_name']])
            # Generate QR code first
            today = datetime.now().strftime('%Y%m%d')
            expected_code = f"{emp_id}_{today}"
            qr = generate_qr_code(expected_code)
            
            # Create voucher with QR code data
            code = create_voucher(emp_id, emp[Config.CSV_COLUMNS['employee_name']], qr)
            
            result.append({
                "name": emp[Config.CSV_COLUMNS['employee_name']],
                "phone": emp[Config.CSV_COLUMNS['phone_number']],
                "voucher_code": code,
                "qr_code": qr,
                "status": "generated"
            })
        
        return {
            "message": f"Generated {len(result)} birthday vouchers",
            "count": len(result),
            "vouchers": result
        }
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSV file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print(f"Starting FastAPI at http://localhost:{Config.FASTAPI_PORT}")
    print(f"Docs: http://localhost:{Config.FASTAPI_PORT}/docs")
    uvicorn.run(app, host="0.0.0.0", port=Config.FASTAPI_PORT)