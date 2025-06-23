# TPH Route Optimizer API (Secured)

🔒 **Secure API** untuk mengoptimalkan rute TPH (Tempat Pengumpulan Hasil) menggunakan algoritma Nearest Neighbor dengan fitur keamanan lengkap.

## Security Features

- ✅ **API Key Authentication** - Semua endpoint memerlukan API key yang valid
- ✅ **Permission-based Access Control** - 3 level akses (read, write, admin)  
- ✅ **Rate Limiting** - Maksimal 100 request per jam per IP
- ✅ **Input Validation** - Validasi ketat untuk mencegah injection
- ✅ **CORS Protection** - Konfigurasi CORS untuk keamanan browser
- ✅ **File Security** - Validasi filename untuk mencegah directory traversal

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Jalankan API server:
```bash
python api.py
```

Atau menggunakan uvicorn langsung:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

## Authentication

### API Keys Tersedia:

| API Key | User | Permissions | Use Case |
|---------|------|-------------|----------|
| `tph_admin_2024` | TPH Admin | read, write, admin | Full access |
| `tph_operator_2024` | TPH Operator | read, write | Normal operations |
| `tph_read_2024` | TPH Reader | read | Read-only access |

### Cara Menggunakan API Key:

```bash
# Tambahkan header Authorization dengan Bearer token
curl -H "Authorization: Bearer tph_admin_2024" \
     "http://localhost:8000/optimize-route?dept_abbr=PKS"
```

## API Endpoints

### 1. **GET `/auth-info`** 🔐
Mengecek informasi authentication dan rate limit.

**Headers Required:**
```
Authorization: Bearer your_api_key
```

**Response:**
```json
{
  "authenticated": true,
  "user": "TPH Admin",
  "permissions": ["read", "write", "admin"],
  "rate_limit_remaining": 95
}
```

### 2. **GET `/optimize-route`** 📍
Mengoptimalkan rute TPH menggunakan algoritma Nearest Neighbor.

**Permission Required:** `read`

**Parameters:**
- `dept_abbr` (optional): Kode department
- `divisi_abbr` (optional): Kode divisi  
- `blok_kode` (optional): Kode blok
- `generate_kml` (optional): Generate file KML (requires `admin` permission)
- `start_index` (optional): Index titik mulai (default: 0)

**Example:**
```bash
curl -H "Authorization: Bearer tph_read_2024" \
     "http://localhost:8000/optimize-route?dept_abbr=PKS&divisi_abbr=DIV1&blok_kode=BLK001"
```

### 3. **POST `/update-order`** ✏️
Update display order di database berdasarkan rute yang dioptimalkan.

**Permission Required:** `write`

**Example:**
```bash
curl -X POST -H "Authorization: Bearer tph_operator_2024" \
     "http://localhost:8000/update-order?dept_abbr=PKS&divisi_abbr=DIV1"
```

### 4. **POST `/update-numbers`** 🔢
Update nomor TPH di database berdasarkan rute yang dioptimalkan.

**Permission Required:** `admin` (operasi kritis!)

**Example:**
```bash
curl -X POST -H "Authorization: Bearer tph_admin_2024" \
     "http://localhost:8000/update-numbers?dept_abbr=PKS&divisi_abbr=DIV1"
```

### 5. **GET `/tph-data`** 📊
Mengambil data TPH mentah tanpa optimasi.

**Permission Required:** `read`

### 6. **GET `/download-kml/{filename}`** 📥
Download file KML yang telah di-generate.

**Permission Required:** `admin`

## Rate Limiting

- **Limit:** 100 requests per hour per IP address
- **Window:** 1 hour (3600 seconds)
- **Response:** HTTP 429 jika limit terlampaui

## Input Validation

API melakukan validasi ketat pada semua parameter:

- `dept_abbr`: Maksimal 10 karakter, hanya alphanumerik
- `divisi_abbr`: Maksimal 10 karakter, alphanumerik + underscore
- `blok_kode`: Maksimal 15 karakter, alphanumerik + underscore/dash
- `filename`: Hanya file .kml, mencegah directory traversal

## Usage Examples

### Python dengan requests:

```python
import requests

# Setup headers dengan API key
headers = {
    "Authorization": "Bearer tph_admin_2024"
}

# Cek auth info
auth_info = requests.get(
    "http://localhost:8000/auth-info", 
    headers=headers
).json()
print(f"User: {auth_info['user']}")
print(f"Remaining requests: {auth_info['rate_limit_remaining']}")

# Optimasi rute dengan KML
response = requests.get(
    "http://localhost:8000/optimize-route",
    headers=headers,
    params={
        "dept_abbr": "PKS",
        "divisi_abbr": "DIV1",
        "blok_kode": "BLK001",
        "generate_kml": True
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"Route optimized: {data['total_points']} points")
    if data['kml_file']:
        print(f"KML file: {data['kml_file']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### JavaScript/Node.js:

```javascript
const axios = require('axios');

const api = axios.create({
    baseURL: 'http://localhost:8000',
    headers: {
        'Authorization': 'Bearer tph_operator_2024'
    }
});

// Optimasi rute
api.get('/optimize-route', {
    params: {
        dept_abbr: 'PKS',
        divisi_abbr: 'DIV1'
    }
})
.then(response => {
    console.log(`Total points: ${response.data.total_points}`);
    response.data.route.forEach((point, index) => {
        console.log(`${index + 1}. TPH ${point.nomor} (${point.lat}, ${point.lon})`);
    });
})
.catch(error => {
    console.error('Error:', error.response?.data || error.message);
});
```

## Error Handling

### Common HTTP Status Codes:

- **200** - Success
- **400** - Bad Request (invalid parameters)
- **401** - Unauthorized (invalid/missing API key)
- **403** - Forbidden (insufficient permissions)
- **404** - Not Found (no data found)
- **429** - Too Many Requests (rate limit exceeded)
- **500** - Internal Server Error

### Error Response Format:
```json
{
    "detail": "Error message here"
}
```

## Security Best Practices

1. **Simpan API Key dengan Aman** - Jangan hardcode di source code
2. **Gunakan HTTPS di Production** - Enkripsi komunikasi
3. **Rotasi API Key Berkala** - Update key secara rutin
4. **Monitor Usage** - Pantau penggunaan API untuk deteksi anomali
5. **Principle of Least Privilege** - Gunakan key dengan permission minimal yang dibutuhkan

## Production Deployment

Untuk production, pastikan:

1. Ganti API keys dengan yang lebih aman
2. Setup HTTPS dengan SSL certificate  
3. Gunakan Redis untuk rate limiting storage
4. Implementasi logging dan monitoring
5. Setup firewall dan network security

## API Documentation

Setelah menjalankan server, akses dokumentasi interaktif:
- **Swagger UI:** `http://localhost:8000/docs` (require API key)
- **ReDoc:** `http://localhost:8000/redoc` (require API key)

> **Note:** Dokumentasi API juga memerlukan API key yang valid untuk diakses!

## Features

- ✅ Optimasi rute menggunakan algoritma Nearest Neighbor
- ✅ Filter berdasarkan department, divisi, dan blok
- ✅ Generate file KML untuk visualisasi di Google Earth
- ✅ Update display order atau TPH numbers di database
- ✅ RESTful API dengan dokumentasi otomatis
- ✅ Async/await untuk performa optimal
- ✅ Error handling yang baik

## Note

Pastikan file `main.py` dan module `db` sudah tersedia dan dapat diimport dengan benar. 