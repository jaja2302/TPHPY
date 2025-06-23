# 📮 Postman Guide - TPH Route Optimizer API

Panduan lengkap menggunakan **Postman** untuk testing dan menggunakan TPH Route Optimizer API.

## 🔧 Setup Postman

### 1. Import Collection
Download dan import collection Postman ini: [akan dibuat di bawah]

### 2. Setup Environment Variables
Buat **Environment** baru di Postman dengan variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `base_url` | `http://localhost:8000` | Base URL API |
| `admin_token` | `tph_admin_2024` | Admin API key |
| `operator_token` | `tph_operator_2024` | Operator API key |
| `reader_token` | `tph_read_2024` | Reader API key |

### 3. Setup Authorization
Untuk setiap request, tambahkan header:
```
Authorization: Bearer {{admin_token}}
```

## 🌐 Custom Port Configuration

### Update file `.env`:
```env
# Server Configuration
HOST=0.0.0.0
PORT=9999  # Your custom port here

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=bms_db
```

### Jalankan dengan custom port:
```bash
python api.py
```
Server akan start di: `http://localhost:9999`

## 📋 Postman Requests Examples

### 1. **GET** - Check Authentication
```
Method: GET
URL: {{base_url}}/auth-info
Headers:
  Authorization: Bearer {{admin_token}}
```

**Expected Response:**
```json
{
  "authenticated": true,
  "user": "TPH Admin",
  "permissions": ["read", "write", "admin"],
  "rate_limit_remaining": 99
}
```

### 2. **GET** - Optimize Route
```
Method: GET
URL: {{base_url}}/optimize-route
Headers:
  Authorization: Bearer {{reader_token}}
Params:
  dept_abbr: PKS
  divisi_abbr: DIV1
  blok_kode: BLK001
  generate_kml: true (requires admin token)
  start_index: 0
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Successfully optimized route for 5 TPH points",
  "total_points": 5,
  "route": [
    {
      "new_order": 1,
      "id": 1,
      "nomor": 1,
      "tph": "TPH001",
      "dept_abbr": "PKS",
      "divisi_abbr": "DIV1",
      "lat": -2.123456,
      "lon": 110.654321
    }
  ],
  "kml_file": "tph_route_PKS_DIV1_BLK001_20241213_143022.kml"
}
```

### 3. **POST** - Update Display Order
```
Method: POST
URL: {{base_url}}/update-order
Headers:
  Authorization: Bearer {{operator_token}}
Params:
  dept_abbr: PKS
  divisi_abbr: DIV1
  blok_kode: BLK001
```

### 4. **POST** - Update TPH Numbers (Admin Only)
```
Method: POST
URL: {{base_url}}/update-numbers
Headers:
  Authorization: Bearer {{admin_token}}
Params:
  dept_abbr: PKS
  divisi_abbr: DIV1
```

### 5. **GET** - Get Raw TPH Data
```
Method: GET
URL: {{base_url}}/tph-data
Headers:
  Authorization: Bearer {{reader_token}}
Params:
  dept_abbr: PKS
  divisi_abbr: DIV1
```

### 6. **GET** - Download KML File
```
Method: GET
URL: {{base_url}}/download-kml/tph_route_PKS_DIV1_BLK001_20241213_143022.kml
Headers:
  Authorization: Bearer {{admin_token}}
```

## 🔑 Testing Different Permission Levels

### Read Permission Test (tph_read_2024):
✅ `/auth-info` - Check auth
✅ `/optimize-route` - Get optimized route (without KML)  
✅ `/tph-data` - Get raw data
❌ `/update-order` - Should return 403
❌ `/update-numbers` - Should return 403

### Write Permission Test (tph_operator_2024):
✅ `/auth-info` - Check auth
✅ `/optimize-route` - Get optimized route (without KML)
✅ `/tph-data` - Get raw data  
✅ `/update-order` - Update display order
❌ `/update-numbers` - Should return 403
❌ `/download-kml/*` - Should return 403

### Admin Permission Test (tph_admin_2024):
✅ All endpoints accessible
✅ Can generate KML files
✅ Can download KML files
✅ Can update TPH numbers

## 🚨 Error Testing

### 1. Test Invalid API Key:
```
Headers:
  Authorization: Bearer invalid_key
Expected: 401 Unauthorized
```

### 2. Test Rate Limiting:
Send 101+ requests dalam 1 jam:
```
Expected: 429 Too Many Requests
```

### 3. Test Invalid Parameters:
```
Params:
  dept_abbr: "invalid@#$%characters"
Expected: 400 Bad Request
```

## 📊 Postman Collection JSON

Simpan sebagai `TPH_API_Collection.json`:

```json
{
  "info": {
    "name": "TPH Route Optimizer API",
    "description": "Secure API for TPH route optimization",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Authentication",
      "item": [
        {
          "name": "Check Auth Info",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{admin_token}}"
              }
            ],
            "url": {
              "raw": "{{base_url}}/auth-info",
              "host": ["{{base_url}}"],
              "path": ["auth-info"]
            }
          }
        }
      ]
    },
    {
      "name": "Route Optimization",
      "item": [
        {
          "name": "Optimize Route",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization", 
                "value": "Bearer {{reader_token}}"
              }
            ],
            "url": {
              "raw": "{{base_url}}/optimize-route?dept_abbr=PKS&divisi_abbr=DIV1&blok_kode=BLK001",
              "host": ["{{base_url}}"],
              "path": ["optimize-route"],
              "query": [
                {"key": "dept_abbr", "value": "PKS"},
                {"key": "divisi_abbr", "value": "DIV1"},
                {"key": "blok_kode", "value": "BLK001"}
              ]
            }
          }
        },
        {
          "name": "Optimize Route with KML (Admin)",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{admin_token}}"
              }
            ],
            "url": {
              "raw": "{{base_url}}/optimize-route?dept_abbr=PKS&divisi_abbr=DIV1&generate_kml=true",
              "host": ["{{base_url}}"],
              "path": ["optimize-route"],
              "query": [
                {"key": "dept_abbr", "value": "PKS"},
                {"key": "divisi_abbr", "value": "DIV1"},
                {"key": "generate_kml", "value": "true"}
              ]
            }
          }
        }
      ]
    },
    {
      "name": "Database Updates",
      "item": [
        {
          "name": "Update Display Order",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{operator_token}}"
              }
            ],
            "url": {
              "raw": "{{base_url}}/update-order?dept_abbr=PKS&divisi_abbr=DIV1",
              "host": ["{{base_url}}"],
              "path": ["update-order"],
              "query": [
                {"key": "dept_abbr", "value": "PKS"},
                {"key": "divisi_abbr", "value": "DIV1"}
              ]
            }
          }
        },
        {
          "name": "Update TPH Numbers (Admin Only)",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{admin_token}}"
              }
            ],
            "url": {
              "raw": "{{base_url}}/update-numbers?dept_abbr=PKS&divisi_abbr=DIV1",
              "host": ["{{base_url}}"],
              "path": ["update-numbers"],
              "query": [
                {"key": "dept_abbr", "value": "PKS"},
                {"key": "divisi_abbr", "value": "DIV1"}
              ]
            }
          }
        }
      ]
    },
    {
      "name": "Data Retrieval",
      "item": [
        {
          "name": "Get TPH Data",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{reader_token}}"
              }
            ],
            "url": {
              "raw": "{{base_url}}/tph-data?dept_abbr=PKS",
              "host": ["{{base_url}}"],
              "path": ["tph-data"],
              "query": [
                {"key": "dept_abbr", "value": "PKS"}
              ]
            }
          }
        }
      ]
    }
  ]
}
```

## 🔧 Environment Variables untuk Postman

```json
{
  "id": "tph-api-env",
  "name": "TPH API Environment",
  "values": [
    {
      "key": "base_url",
      "value": "http://localhost:8000",
      "enabled": true
    },
    {
      "key": "admin_token", 
      "value": "tph_admin_2024",
      "enabled": true
    },
    {
      "key": "operator_token",
      "value": "tph_operator_2024", 
      "enabled": true
    },
    {
      "key": "reader_token",
      "value": "tph_read_2024",
      "enabled": true
    }
  ]
}
```

## 🎯 Quick Testing Steps

1. **Start API:**
   ```bash
   python api.py
   ```

2. **Import Collection & Environment** ke Postman

3. **Test Authentication:**
   - Run "Check Auth Info" dengan admin_token
   - Verify permissions returned

4. **Test Route Optimization:**
   - Run "Optimize Route" dengan reader_token
   - Check route data returned

5. **Test Permissions:**
   - Try admin endpoints dengan reader_token (should fail)
   - Try write endpoints dengan operator_token (should work)

6. **Test Rate Limiting:**
   - Send multiple requests quickly
   - Watch for 429 errors

## 💡 Tips Postman

- Gunakan **Environment Variables** untuk mudah switch API keys
- Setup **Tests** tab untuk auto-validation responses
- Gunakan **Pre-request Scripts** untuk dynamic data
- Save responses as **Examples** untuk documentation

Sekarang Anda bisa testing API dengan mudah menggunakan Postman! 🚀 