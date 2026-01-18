# Publishing Topolograph SDK to PyPI

## Prerequisites

1. **PyPI Account**: Create an account at https://pypi.org/account/register/
2. **API Token**: Create an API token at https://pypi.org/manage/account/token/
   - For uploads, use a token with "Upload packages" scope
   - Save the token (format: `pypi-...`)

## Publishing Steps

### Step 1: Build the Package

```bash
# Ensure you're in the project root
cd /home/ubuntu/topolograph-sdk

# Activate virtual environment
source venv/bin/activate

# Install build tools
pip install --upgrade build twine

# Build the package
python -m build

# Verify the package
twine check dist/*
```

### Step 2: Test on TestPyPI (Recommended)

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# When prompted:
# - Username: __token__
# - Password: pypi-<your-testpypi-token>

# Test installation
pip install --index-url https://test.pypi.org/simple/ topolograph-sdk
```

### Step 3: Publish to PyPI

```bash
# Upload to PyPI
twine upload dist/*

# When prompted:
# - Username: __token__
# - Password: pypi-<your-pypi-token>
```

## Alternative: Using Environment Variables

You can set credentials as environment variables:

```bash
# For TestPyPI
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-<your-testpypi-token>
twine upload --repository testpypi dist/*

# For PyPI
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-<your-pypi-token>
twine upload dist/*
```

## Version Management

Before publishing a new version:

1. Update version in `pyproject.toml`:
   ```toml
   version = "0.1.1"  # Increment as needed
   ```

2. Rebuild:
   ```bash
   python -m build
   ```

3. Upload:
   ```bash
   twine upload dist/*
   ```

## Current Package Status

- **Version**: 0.1.0
- **Status**: Ready for publishing
- **Build Files**: `dist/topolograph_sdk-0.1.0-py3-none-any.whl` and `dist/topolograph_sdk-0.1.0.tar.gz`
- **Package Check**: ✅ PASSED

## Post-Publishing

After successful upload:

1. Verify on PyPI: https://pypi.org/project/topolograph-sdk/
2. Test installation: `pip install topolograph-sdk`
3. Update documentation if needed
