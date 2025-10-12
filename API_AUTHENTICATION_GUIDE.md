# Hướng dẫn sử dụng API Authentication

## Tổng quan
Hệ thống authentication sử dụng JWT (JSON Web Token) với refresh token để duy trì đăng nhập.

## Các API Endpoints

### 1. Đăng ký tài khoản
**POST** `/accounts/signup/`

**Request Body:**
```json
{
    "username": "string",
    "password": "string",
    "password_confirm": "string",
    "role": "PATIENT|DOCTOR|ADMIN",
    "first_name": "string",
    "last_name": "string"
}
```

**Response:**
```json
{
    "message": "Đăng ký thành công!",
    "user": {
        "id": 1,
        "username": "user123",
        "role": "PATIENT",
        "first_name": "John",
        "last_name": "Doe"
    },
    "tokens": {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}
```

### 2. Đăng nhập
**POST** `/accounts/login/`

**Request Body:**
```json
{
    "username": "string",
    "password": "string"
}
```

**Response:**
```json
{
    "message": "Đăng nhập thành công!",
    "user": {
        "id": 1,
        "username": "user123",
        "email": "user@example.com",
        "phone": "0123456789",
        "role": "PATIENT",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": true,
        "date_joined": "2024-01-01T00:00:00Z"
    },
    "tokens": {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}
```

### 3. Làm mới Access Token
**POST** `/accounts/refresh/`

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Hoặc từ Cookie:**
```
Cookie: refreshToken=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Response:**
```json
{
    "message": "Token được làm mới thành công!",
    "tokens": {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}
```

### 4. Đăng xuất
**POST** `/accounts/logout/`

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Hoặc từ Cookie:**
```
Cookie: refreshToken=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Response:**
```json
{
    "message": "Đăng xuất thành công!"
}
```

### 5. Đặt lại mật khẩu
**POST** `/accounts/reset-token/`

**Request Body:**
```json
{
    "token": "string",
    "new_password": "string"
}
```

**Response:**
```json
{
    "message": "Mật khẩu đã được đặt lại thành công!"
}
```

## Cấu hình JWT

### Token Lifetime
- **Access Token**: 60 phút
- **Refresh Token**: 7 ngày

### Cách sử dụng Access Token
Thêm vào header của request:
```
Authorization: Bearer <access_token>
```

## Luồng Authentication

1. **Đăng nhập**: Gọi `/accounts/login/` để lấy access token và refresh token
2. **Sử dụng API**: Gửi access token trong header Authorization
3. **Token hết hạn**: Khi access token hết hạn, gọi `/accounts/refresh/` để lấy token mới
4. **Đăng xuất**: Gọi `/accounts/logout/` để vô hiệu hóa refresh token

## Xử lý lỗi

### Lỗi thường gặp:

1. **401 Unauthorized**: Token không hợp lệ hoặc đã hết hạn
2. **400 Bad Request**: Dữ liệu request không hợp lệ
3. **500 Internal Server Error**: Lỗi server

### Ví dụ response lỗi:
```json
{
    "message": "Refresh token không hợp lệ!",
    "error": "INVALID_REFRESH_TOKEN",
    "detail": "Token is blacklisted"
}
```

## Bảo mật

1. **Lưu trữ token an toàn**: Không lưu token trong localStorage, sử dụng httpOnly cookies
2. **HTTPS**: Luôn sử dụng HTTPS trong production
3. **Token rotation**: Refresh token được tự động tạo mới mỗi lần refresh
4. **Blacklist**: Refresh token cũ bị blacklist sau khi tạo mới

## Ví dụ sử dụng với JavaScript

```javascript
// Đăng nhập
const login = async (username, password) => {
    const response = await fetch('/accounts/login/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    
    if (response.ok) {
        // Lưu tokens
        localStorage.setItem('access_token', data.tokens.access);
        localStorage.setItem('refresh_token', data.tokens.refresh);
        return data;
    }
    
    throw new Error(data.message);
};

// Làm mới token
const refreshToken = async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    
    const response = await fetch('/accounts/refresh/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh: refreshToken })
    });
    
    const data = await response.json();
    
    if (response.ok) {
        localStorage.setItem('access_token', data.tokens.access);
        localStorage.setItem('refresh_token', data.tokens.refresh);
        return data;
    }
    
    throw new Error(data.message);
};

// Gọi API với token
const callAPI = async (url, options = {}) => {
    const accessToken = localStorage.getItem('access_token');
    
    const response = await fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
        }
    });
    
    // Nếu token hết hạn, thử refresh
    if (response.status === 401) {
        try {
            await refreshToken();
            // Thử lại request
            return callAPI(url, options);
        } catch (error) {
            // Redirect to login
            window.location.href = '/login';
        }
    }
    
    return response;
};
```
