# 🎉 BDVoucher - Birthday Voucher Management System

A simple, clean birthday voucher system for cafes and restaurants with WhatsApp integration and QR code scanning.

## 🌟 Features

- **📱 WhatsApp Integration**: Send birthday wishes with QR codes via WhatsApp (UltraMsg)
- **🔗 QR Code Scanning**: Real-time QR code scanning with camera for voucher redemption
- **🔐 Secure Voucher Codes**: Cryptographically secure random voucher codes (BDV + 8 random chars)
- **💾 CSV Data Storage**: Simple file-based employee data management
- **🌐 Web Interface**: Clean, responsive web UI for voucher management
- **⚙️ Configurable**: Easy configuration via environment variables
- **🔄 Real-time Updates**: Live voucher status and redemption tracking
- **📊 System Status**: Live system statistics and voucher history

## 🏗️ Architecture

```
BDVoucher/
├── prog/                 # Program files
│   ├── cafe_interface.py    # Cafe interface (public deployment)
│   ├── admin_interface.py   # Admin interface (local server)
│   ├── config.py           # Configuration settings
│   ├── voucher_system.py   # Voucher management & data handling
│   ├── whatsapp_service.py # WhatsApp messaging service
│   └── final_testing.py    # Comprehensive testing
├── data/                 # Data files (CSV)
│   ├── employees.csv     # Employee data
│   └── voucher_history.csv # Voucher history
├── docs/                 # Documentation
│   └── DEPLOYMENT_GUIDE.md
├── requirements.txt      # Python dependencies
└── readme.MD            # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- WhatsApp Business API access (UltraMsg)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd BDVoucher
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   # Create .env file with your settings
   # See Configuration section below
   ```

### Configuration

Create a `.env` file with the following variables:

```env
# Cafe Information
CAFE_NAME=Hey Hey Cafe
CAFE_LOCATION=Muscat, Oman
VOUCHER_REWARD=FREE Drink
VOUCHER_VALUE=$15
VOUCHER_VALIDITY_HOURS=24

# WhatsApp Messaging (UltraMsg)
MESSAGING_SERVICE=ultramsg
ULTRAMSG_INSTANCE_ID=your_instance_id_here
ULTRAMSG_TOKEN=your_token_here

# Server Settings
PORT=5000
DEBUG=True
```

## 🎯 Usage

### 1. Test the System
```bash
cd prog
python final_testing.py
```

### 2. Deploy Cafe Interface (Public)
```bash
cd prog
python cafe_interface.py
```
Access at: http://localhost:5000

### 3. Deploy Admin Interface (Local Server)
```bash
cd prog
python admin_interface.py
```
Access at: http://localhost:5000

### 4. Interface Features

#### Cafe Interface (Public Deployment)
- **QR Code Scanner**: Use camera to scan voucher QR codes
- **Manual Entry**: Enter voucher codes manually
- **Simple Design**: Clean, staff-friendly interface

#### Admin Interface (Local Server)
- **All Cafe Features**: QR scanning and manual entry
- **System Statistics**: Live system status and metrics
- **Employee Management**: View and manage employee data
- **Voucher History**: Complete transaction tracking
- **Birthday Wishes**: Send WhatsApp messages to birthday employees

## 📱 WhatsApp Integration

### UltraMsg Setup
1. Create account at [UltraMsg](https://ultramsg.com)
2. Get your Instance ID and Token
3. Configure in `.env`:
   ```env
   MESSAGING_SERVICE=ultramsg
   ULTRAMSG_INSTANCE_ID=your_instance_id
   ULTRAMSG_TOKEN=your_token
   ```

## 🗄️ Data Storage

### CSV Storage
- Simple file-based storage in `data/` directory
- No additional setup required
- Perfect for small to medium datasets
- Easy to backup and manage

### Employee Data Format
```csv
employee_id,employee_name,phone_number,date_of_birth
EMP001,John Doe,+1234567890,1990-01-15
EMP002,Jane Smith,+1234567891,1985-12-03
```

## 🔧 API Endpoints

### Core Endpoints
- `GET /` - Main web interface
- `GET /status` - System status and statistics
- `GET /history` - Voucher transaction history
- `POST /redeem` - Redeem a voucher
- `POST /send-birthday` - Send birthday wishes

## 🎨 Web Interface Features

### QR Code Scanner
- **Camera Integration**: Real-time QR code scanning
- **Manual Entry**: Type voucher codes manually
- **Auto-redemption**: Automatically redeem scanned codes
- **Mobile-responsive**: Works on all devices

### System Management
- **Birthday Detection**: Automatically find today's birthdays
- **WhatsApp Integration**: Send birthday wishes with QR codes
- **Live Statistics**: Real-time system status
- **Voucher History**: Complete transaction tracking

## 🧪 Testing

Run the comprehensive test suite:
```bash
cd prog
python final_testing.py
```

The test system will:
- Test CSV data loading and birthday detection
- Test secure voucher creation and redemption
- Send actual WhatsApp messages with QR codes
- Test web interface and API endpoints
- Verify QR code scanning functionality
- Provide comprehensive system status

## 📊 Data Structure

### Employee Data
```csv
employee_id,employee_name,phone_number,date_of_birth
EMP001,John Doe,+1234567890,1990-01-15
```

### Voucher Data
- **Secure Codes**: BDV + 8 random characters (e.g., BDV3K9M2X7)
- **QR Code Data**: Base64 encoded QR images
- **Expiration**: Configurable validity period
- **Status**: Created, redeemed, expired

## 🔒 Security Features

- **Cryptographically Secure Codes**: Using Python's `secrets` module
- **Input Validation**: All user inputs are validated
- **Environment Protection**: Sensitive data in environment variables
- **Error Handling**: Comprehensive error logging and handling

## 🚀 Deployment

### Development
```bash
python app.py
```

### Production
See `docs/DEPLOYMENT_GUIDE.md` for detailed production deployment instructions including:
- Systemd service configuration
- Nginx reverse proxy setup
- SSL certificate configuration
- Docker containerization
- Kubernetes deployment

## 📈 Monitoring

- **Live System Status**: Real-time statistics
- **Voucher Tracking**: Complete redemption history
- **Error Logging**: Comprehensive logging system
- **Health Checks**: Built-in system health monitoring

## 🆘 Support

For support and questions:
- Check the documentation in `/docs`
- Review the deployment guide
- Test the system with `python test_simple.py`

## 🔄 Version History

- **v2.0.0** - Simplified and Enhanced
  - QR code scanning with camera
  - Secure voucher codes
  - All-in-one application
  - Simplified architecture
  - Enhanced security

## 🎯 Key Features

- ✅ **QR Code Scanning**: Real-time camera-based scanning
- ✅ **Secure Vouchers**: Cryptographically secure random codes
- ✅ **WhatsApp Integration**: Automated birthday wishes
- ✅ **Simple Setup**: Single file application
- ✅ **Mobile Ready**: Responsive web interface
- ✅ **Easy Testing**: Comprehensive test suite

---
