# Python Version Requirements

## Required Version: Python 3.12

This project requires **Python 3.12** specifically due to compatibility requirements with the `flatlib` library used for astrological calculations.

### Why Python 3.12?

The `flatlib` library depends on `pyswisseph`, which does not currently compile with Python 3.13. Python 3.12 is the latest stable version that fully supports all dependencies.

## Installation Instructions

### macOS

#### Option 1: Using Homebrew (Recommended)
```bash
# Install Python 3.12
brew install python@3.12

# Verify installation
python3.12 --version

# Create virtual environment
cd backend
python3.12 -m venv venv
source venv/bin/activate

# Verify you're using 3.12
python --version  # Should show Python 3.12.x
```

#### Option 2: Using pyenv
```bash
# Install pyenv if not already installed
brew install pyenv

# Install Python 3.12
pyenv install 3.12.0

# Set local version for this project
cd horoskooppi_saas
pyenv local 3.12.0

# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate
```

### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt-get update

# Install Python 3.12
sudo apt-get install python3.12 python3.12-venv python3.12-dev

# Create virtual environment
cd backend
python3.12 -m venv venv
source venv/bin/activate

# Verify version
python --version  # Should show Python 3.12.x
```

### Windows

1. Download Python 3.12 from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Open Command Prompt and verify:
```cmd
python --version  # Should show Python 3.12.x
```

4. Create virtual environment:
```cmd
cd backend
python -m venv venv
venv\Scripts\activate
```

## Verifying Installation

After setting up your virtual environment, verify flatlib can be installed:

```bash
pip install flatlib==0.2.3
python -c "import flatlib; print('flatlib installed successfully!')"
```

If this works without errors, you're all set!

## Deployment

### Render.com

The `runtime.txt` file specifies Python 3.12.0 for Render.com deployments. Render will automatically use this version.

### Other Platforms

Ensure your deployment platform uses Python 3.12. Check platform-specific documentation for specifying Python versions.

## Troubleshooting

### Issue: "flatlib installation fails"
**Solution**: Make sure you're using Python 3.12, not 3.13 or earlier versions. Check with:
```bash
python --version
```

### Issue: "python3.12 command not found"
**Solution**: Python 3.12 may not be installed or not in your PATH. Use the installation instructions above for your operating system.

### Issue: "Virtual environment still uses wrong Python version"
**Solution**: Delete the existing venv and recreate it:
```bash
rm -rf backend/venv
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```


