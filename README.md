
![Email Auto Subscriber Banner](https://i.pinimg.com/originals/5d/2c/44/5d2c44694918947aede42306cb7154d0.gif)

# Email Auto Subscriber

A powerful multi-threaded email subscription automation tool built with Selenium and Python. This tool can automatically subscribe to multiple newsletter services with configurable threading and proxy support.

## Disclaimer

**EDUCATIONAL USE ONLY**

This tool is created for educational and research purposes only. The developers are not responsible for any misuse of this software. We have no intent to promote spamming or unwanted email subscriptions. Use this tool at your own risk and ensure you comply with all applicable laws and terms of service of the websites you interact with.

## Features

- **Multi-threaded Processing**: Up to 25 concurrent threads for maximum speed
- **Proxy Support**: Rotate through multiple proxies to avoid rate limiting
- **Dual Environment Support**: Works on both Replit and GitHub Codespaces
- **Beast Mode**: Optimized for 1 subscription per second throughput
- **URL Verification System**: Test and verify subscription URLs before using them
- **Performance Tracking**: Real-time statistics and success rate monitoring
- **Headless Browser**: Runs silently in the background without GUI
- **Auto-retry Logic**: Intelligent retry mechanism for failed attempts
- **Configurable Timeouts**: Adjustable page load and element timeouts
- **JSON Configuration**: Easy URL and field configuration management

## How It Works

1. **URL Management**: Add subscription URLs and configure input field selectors
2. **Verification Mode**: Test unverified URLs to ensure they work correctly
3. **Beast Mode Attack**: Run high-speed subscription campaigns with multiple threads
4. **Performance Monitoring**: Track success rates and subscription speed
5. **Proxy Rotation**: Automatically rotate through configured proxy servers

## Setup Guide for GitHub Codespaces

### 1. Install Firefox and Geckodriver

```bash
# Update package list
sudo apt update

# Install Firefox
sudo apt install -y firefox

# Download and install Geckodriver
wget https://github.com/mozilla/geckodriver/releases/latest/download/geckodriver-v0.33.0-linux64.tar.gz
tar -xzf geckodriver-v0.33.0-linux64.tar.gz
sudo mv geckodriver /usr/local/bin/
sudo chmod +x /usr/local/bin/geckodriver

# Clean up
rm geckodriver-v0.33.0-linux64.tar.gz
```

### 2. Install Python Dependencies

```bash
pip install selenium webdriver-manager python-dotenv
```

### 3. Configure Environment

Create a `.env` file with your email list:

```bash
echo 'EMAILS=email1@example.com,email2@example.com,email3@example.com' > .env
```

### 4. Run the Application

```bash

# For GitHub Codespaces version
python gitmain.py
```

## Usage Instructions

1. **Add URLs**: Start by adding subscription URLs to the system
2. **Configure Fields**: Set up input field selectors for email, submit buttons, etc.
3. **Verify URLs**: Test unverified URLs to ensure they work properly
4. **Configure Beast Settings**: Set thread count, timeouts, and proxy settings
5. **Launch Beast Mode**: Run the high-speed subscription campaign

## Performance Optimization

### Beast Mode Configuration
- **Threads**: 5-25 concurrent threads (recommended: 15)
- **Timeouts**: 5-15 seconds page load timeout
- **Proxies**: Multiple proxy servers for load distribution
- **Target Rate**: 1 subscription per second

### Speed Optimizations
- Disabled images and CSS loading
- Minimal JavaScript execution
- Aggressive browser caching disabled
- Parallel driver pool creation
- Ultra-fast typing simulation

## File Structure

```
├── gitmain.py        # GitHub Codespaces optimized version
├── requirements.txt  # Python dependencies
├── .env             # Email configuration
├── email_subscription.json  # URL and field configuration
└── README.md        # This file
```

## Configuration Files

### Email Configuration (.env)
```
EMAILS=email1@domain.com,email2@domain.com,email3@domain.com
```

### URL Configuration (email_subscription.json)
```json
{
  "url": "https://example.com/newsletter",
  "verified": true,
  "input_fields": {
    "email": [{"name": "email"}],
    "submit": [{"class": "subscribe-btn"}],
    "checkboxes": [],
    "radios": [],
    "wait": 2
  }
}
```

## Performance Statistics

The tool provides real-time performance metrics:
- Total subscription attempts
- Success/failure rates
- Subscriptions per second
- Overall completion time
- Thread utilization

## Contributing

Feel free to contribute by:
- Adding support for new website types
- Improving performance optimizations
- Enhancing error handling
- Adding new features

## Credits

**Development Team:**
- **Lead Developer**: [@B3nT3X](https://github.com/B3nT3X)
- **Debug Developer**: [@cracker666user](https://github.com/cracker666user)

**Community:**
- **Telegram Channel**: [@skittle_gg](https://t.me/skittle_gg)

## License

This project is provided as-is for educational purposes. Please use responsibly and in accordance with all applicable laws and website terms of service.

---

**Remember**: Always respect website terms of service and use this tool responsibly. Happy learning!
