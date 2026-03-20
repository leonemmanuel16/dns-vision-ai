# DNS Vision AI v0.1.0 - Portable Edition

AI-powered video analytics platform for Windows.

## 🚀 Quick Start

1. **Extract** this package to a folder (e.g., `C:\DNSVisionAI`)
2. **Double-click** `start.bat` to run
3. **Open browser** to http://localhost:3000 (dashboard)
4. **Configure cameras** in `data\config\cameras.env`

## 📋 Requirements

- **Windows 10/11** (64-bit)
- **Python 3.8+** installed with pip
- **4GB RAM** minimum, 8GB recommended
- **Internet connection** for dependency installation

### Python Installation
If you don't have Python:
1. Download from https://python.org/downloads/
2. **Check "Add Python to PATH"** during installation
3. Restart your computer
4. Run `start.bat` again

## ⚙️ Configuration

### Adding Cameras
Edit `data\config\cameras.env`:
```
CAMERA_FRONT_DOOR_IP=192.168.1.100
CAMERA_FRONT_DOOR_USER=admin  
CAMERA_FRONT_DOOR_PASS=password123
```

### Motion Detection Settings
Edit `data\config\.env`:
- `MOTION_THRESHOLD=8000` (lower = more sensitive)
- `COOLDOWN_SECONDS=15` (time between alerts)

### GPU Acceleration (Optional)
For NVIDIA GPUs:
```cmd
pip uninstall torch torchvision
pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu118
```

## 🎛️ Usage

### Dashboard
- **URL:** http://localhost:3000
- **Features:** Live view, events, configuration

### API Documentation  
- **URL:** http://localhost:8000/docs
- **Features:** REST API, webhooks, integrations

### Logs & Data
- **Events:** `data\events\`
- **Logs:** `data\logs\`  
- **Configuration:** `data\config\`

## 🔧 Troubleshooting

### Common Issues

**"Python is not installed"**
- Install Python from python.org
- Make sure "Add to PATH" was checked

**"Module not found errors"**  
- Run: `pip install -r requirements.txt`
- Check internet connection

**"Port already in use"**
- Close other applications using ports 3000, 8000
- Or change ports in `data\config\.env`

**High CPU usage**
- Increase `MOTION_THRESHOLD` in config
- Reduce camera resolution
- Add GPU acceleration

### Getting Help

- **Documentation:** https://github.com/leonemmanuel16/dns-vision-ai
- **Issues:** Create GitHub issue
- **Commercial Support:** contact@dnsit.com.mx

## 📁 Directory Structure

```
DNSVisionAI-Portable/
├── start.bat              # Main launcher
├── requirements.txt       # Python dependencies  
├── app/                   # Application code
│   ├── services/          # Backend services
│   └── config/            # Default config
├── data/                  # User data
│   ├── events/            # Motion events
│   ├── config/            # User configuration
│   └── logs/              # Application logs
└── README.md              # This file
```

## 🔒 Security Notes

- Change default camera passwords
- Run on trusted networks only
- Consider firewall rules for production
- Regular security updates recommended

## ⚡ Performance Tips

- **CPU:** Intel Core i5+ or AMD Ryzen 5+ recommended
- **RAM:** 8GB+ for multiple cameras  
- **Storage:** SSD recommended for event storage
- **Network:** Gigabit Ethernet for HD cameras

---

**DNS Vision AI v0.1.0**  
© 2026 DNS Data Network Solutions  
https://dnsit.com.mx
