from datetime import datetime
import os
import time
import requests
from PIL import Image
import tinify
import configparser

conifig = configparser.ConfigParser()
if os.path.exists('config.ini'):
    conifig.read('config.ini')
    tinify.key = conifig['tinify']['api_key']
elif os.getenv('TINIFY_API_KEY') is not None:
    tinify.key = os.getenv('TINIFY_API_KEY')
else:
    tinify.key = "here set your API key"

def convert_to_png(path='.'):
    """
    Convert all non-PNG images in the specified directory to PNG format.
    The original files are kept, and new PNG files are created with the same name.
    
    :param path: The file or directory to process. Default is the current directory.
    """
    # Check if the path is a file or a directory
    if os.path.isfile(path):
        files_to_convert = [path]
    elif os.path.isdir(path):
        files_to_convert = [os.path.join(path, filename) for filename in os.listdir(path)]
    else:
        print("Invalid path specified. Please provide a valid file or directory path.")
        return

    # Process each file
    for file_path in files_to_convert:
        _, extension = os.path.splitext(file_path)
        
        # Check if the file is not in PNG format
        if extension.lower() != '.png':
            try:
                with Image.open(file_path) as img:
                    new_filename = os.path.splitext(os.path.basename(file_path))[0] + '.png'
                    new_file_path = os.path.join(os.path.dirname(file_path), new_filename)
                    
                    # Save the image in PNG format
                    img.save(new_file_path, 'PNG')
                    print(f"Converted {os.path.basename(file_path)} to {new_filename}")
            except IOError:
                # Skip the file if it's not an image
                continue

def get_end_date():
    """
    Get the current date in YYYY-MM-DD format.
    
    :return: Current date as a string.
    """
    return datetime.now().strftime("%Y-%m-%d")

def download_image(url, filename):
    """
    Download an image from a URL and save it to a file.
    
    :param url: The URL of the image to download.
    :param filename: The filename to save the downloaded image.
    :return: True if the download was successful, False otherwise.
    """
    for attempt in range(3):
        try:
            response = requests.get(url)
            response.raise_for_status()
            with open(filename, 'wb') as file:
                file.write(response.content)
            return True
        except requests.RequestException:
            if attempt < 2:
                time.sleep(1)
            else:
                print(f"Failed to download: {url}")
                return False

def process_date(date):
    """
    Fetch data from the given date and download the associated image.
    
    :param date: The date in YYYY-MM-DD format.
    :return: The filename of the downloaded image, or None if download failed.
    """
    base_url = "https://open.iciba.com/dsapi/"
    params = {
        "file": "json",
        "date": date
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        image_url = data.get("fenxiang_img")
        if image_url:
            file_extension = os.path.splitext(image_url)[1]
            filename = f"{data['dateline']}{file_extension}"
            
            if download_image(image_url, filename):
                print(f"Downloaded: {filename}")
                return filename
        else:
            print(f"No image URL for date: {date}")
            return None
    
    except requests.RequestException as e:
        print(f"Failed to fetch data for date: {date}. Error: {e}")
        return None

def compress_image(image_path):
    """
    Compress a single image using the Tinify API.
    
    :param image_path: The path to the image file to be compressed.
    """
    if not os.path.isfile(image_path):
        print(f"File not found: {image_path}")
        return
    
    try:
        source = tinify.from_file(image_path)
        source.to_file(image_path)
        print(f"Compressed {os.path.basename(image_path)} and saved to the same location.")
    except tinify.errors.AccountError:
        print("Verify your API key and account limit.")
    except tinify.errors.ClientError:
        print("Check your source image and request options.")
    except tinify.errors.ServerError:
        print("Temporary issue with the Tinify API.")
    except tinify.errors.ConnectionError:
        print("A network connection error occurred.")
    except Exception as e:
        print(f"An error occurred: {e}")     

if __name__ == "__main__":
    filename = process_date(get_end_date())
    if filename:
        convert_to_png(filename)
        compress_image(filename)