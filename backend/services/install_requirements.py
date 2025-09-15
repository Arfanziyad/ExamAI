# Install required packages
import pip

def install_requirements():
    """Install required packages for file handling"""
    requirements = [
        'Pillow',  # For image processing
        'PyPDF2',  # For PDF handling
        'aiofiles',  # For async file operations
    ]
    for package in requirements:
        pip.main(['install', package])