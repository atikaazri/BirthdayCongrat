# 🔧 BDVoucher Technical Documentation

## 📋 System Overview

BDVoucher is a birthday voucher management system designed for cafes and restaurants. It provides automated birthday messaging via WhatsApp, QR code generation, and voucher redemption through multiple interfaces.

## 🏗️ Architecture

### Core Components

1. **Main Server (`app.py`)**
   - Central Flask application
   - Handles API endpoints for voucher operations
   - Manages automatic messaging scheduler
   - Port: 5000 (configurable)

2. **Cafe Interface (`cafe_interface.py`)**
   - Public-facing voucher redemption interface
   - Mobile-friendly birthday-themed UI
   - In-page camera for QR code scanning
   - Image upload with auto-scan
   - Manual voucher code entry
   - Port: 5001 (configurable)

3. **Admin Interface (`admin_interface.py`)**
   - Management dashboard for administrators
   - Voucher history and statistics
   - Employee management
   - System monitoring
   - Port: 5002 (configurable)

4. **Database Layer (`database.py`)**
   - Centralized data operations
   - CSV file management
   - Voucher lifecycle management
   - Employee data handling

5. **Configuration (`config.py`)**
   - Environment-based configuration
   - WhatsApp API settings
   - Server port configuration
   - Voucher validity settings

## 🔄 Data Flow

### Voucher Creation Process
```
Employee Birthday Detected → Create Voucher → Generate QR Code → Send WhatsApp Message
```

### Voucher Redemption Process
```
QR Code Scan/Upload/Manual Entry → Validate Voucher → Update Status → Clean Up Resources
```

## 📊 Data Storage

### CSV Files
- **`data/employees.csv`**: Employee information (ID, name, phone, date of birth)
- **`data/voucher_history.csv`**: Complete voucher lifecycle tracking
- **`data/qrcodes/`**: Generated QR code images (PNG format)

### Data Structure
```csv
# employees.csv
employee_id,employee_name,phone_number,date_of_birth
EMP001,John Doe,+1234567890,1990-05-15

# voucher_history.csv
timestamp,voucher_code,employee_id,employee_name,status
2025-10-21T10:00:00,ABC123DEF456,EMP001,John Doe,created
2025-10-21T11:00:00,ABC123DEF456,EMP001,John Doe,redeemed
```

## 🔐 Security Features

### Voucher Code Generation
- **Algorithm**: UUID4-based generation
- **Format**: 12-character alphanumeric codes
- **Uniqueness**: Guaranteed by UUID4
- **Example**: `A1B2C3D4E5F6`

### Data Validation
- Voucher code format validation (12 chars, alphanumeric)
- Employee ID validation
- Date format validation
- File type validation for image uploads

## 📱 WhatsApp Integration

### Service Provider
- **Provider**: UltraMsg API
- **Features**: Image + text messages
- **Authentication**: Instance ID + Token

### Message Format
```
Happy Birthday {employee_name}!

From all of us at {cafe_name}, we hope you have a wonderful day! 
As a special birthday treat, here's a voucher for a {voucher_reward} worth {voucher_value}.

Location: {cafe_location}
Valid for: {validity_period}

Enjoy your special day!
```

## 🎨 User Interface

### Cafe Interface Features
- **Design**: Birthday-themed with pink/purple gradients
- **Responsive**: Mobile-first design
- **Animations**: Floating emojis, smooth transitions
- **Accessibility**: High contrast, large touch targets

### Camera Integration
- **In-Page Preview**: HTML5 video element
- **Backend Processing**: OpenCV + pyzbar
- **Real-time Detection**: Live QR code scanning
- **Auto-Validation**: Immediate voucher processing

## ⚙️ Configuration

### Environment Variables
```bash
# Basic Settings
CAFE_NAME=Hey Hey Cafe
CAFE_LOCATION=Muscat, Oman
VOUCHER_REWARD=FREE Drink
VOUCHER_VALUE=$15

# Voucher Expiry
VOUCHER_EXPIRY_MODE=hours
VOUCHER_VALIDITY_HOURS=24

# WhatsApp Settings
MESSAGING_SERVICE=ultramsg
ULTRAMSG_INSTANCE_ID=your_instance_id
ULTRAMSG_TOKEN=your_token

# Auto-Messaging
AUTO_MESSAGING_ENABLED=True
AUTO_MESSAGING_TIME=09:00
AUTO_MESSAGING_TIMEZONE=Asia/Muscat

# Server Ports
PORT=5000
CAFE_PORT=5001
ADMIN_PORT=5002
```

## 🔧 API Endpoints

### Main Server (`app.py`)
- `GET /`: Main dashboard
- `POST /send-birthday`: Manual birthday message sending
- `POST /test-auto-messaging`: Test automatic messaging

### Cafe Interface (`cafe_interface.py`)
- `GET /`: Cafe redemption interface
- `POST /start-camera-scan`: Start camera scanning
- `POST /stop-camera-scan`: Stop camera scanning
- `GET /check-camera-scan`: Check scan status
- `POST /scan-image`: Scan uploaded image
- `POST /redeem`: Redeem voucher

### Admin Interface (`admin_interface.py`)
- `GET /`: Admin dashboard
- `GET /api/vouchers`: Get all vouchers
- `GET /api/history`: Get voucher history
- `GET /api/stats`: Get system statistics

## 🧪 Testing

### Final Testing Script (`final_testing.py`)
- **Purpose**: Complete system testing
- **Features**:
  - Sends WhatsApp messages immediately
  - Creates vouchers and QR codes
  - Starts all servers
  - Provides detailed results

### Manual Testing
1. **Camera Scanning**: Point camera at QR code
2. **Image Upload**: Upload QR code image
3. **Manual Entry**: Enter voucher code directly
4. **Error Handling**: Test invalid codes, expired vouchers

## 🚀 Deployment

### Production Setup
1. **Environment Configuration**: Set up `.env` file
2. **WhatsApp API**: Configure UltraMsg credentials
3. **Server Deployment**: Deploy main server (`app.py`)
4. **Cafe Interface**: Deploy to public server
5. **Admin Interface**: Keep on local/secure server

### Monitoring
- **Logs**: Check server logs for errors
- **Voucher History**: Monitor redemption patterns
- **WhatsApp Delivery**: Track message delivery status

## 🔍 Troubleshooting

### Common Issues
1. **Camera Not Working**: Check browser permissions
2. **QR Code Not Detected**: Ensure good lighting and focus
3. **WhatsApp Messages Not Sent**: Verify API credentials
4. **Voucher Not Found**: Check voucher history CSV

### Debug Mode
- Set `DEBUG=True` in configuration
- Check browser console for JavaScript errors
- Monitor server logs for Python errors

## 📈 Performance Considerations

### Optimization
- **Image Cleanup**: Automatic QR code image deletion after redemption
- **CSV Caching**: Employee data cached in memory
- **Threading**: Camera scanning runs in separate thread
- **Responsive Design**: Optimized for mobile devices

### Scalability
- **File-based Storage**: Suitable for small to medium businesses
- **Modular Design**: Easy to extend with database backend
- **API-first**: Ready for mobile app integration

## 🔮 Future Enhancements

### Potential Improvements
1. **Database Backend**: PostgreSQL/MySQL integration
2. **Mobile App**: Native mobile application
3. **Analytics**: Detailed reporting and analytics
4. **Multi-language**: Internationalization support
5. **Cloud Deployment**: Docker containerization
6. **API Documentation**: OpenAPI/Swagger documentation

### Integration Possibilities
- **POS Systems**: Integration with point-of-sale systems
- **CRM Systems**: Customer relationship management
- **Email Marketing**: Email campaign integration
- **Social Media**: Social media birthday posts
