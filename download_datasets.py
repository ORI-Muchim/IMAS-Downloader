from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from browsermobproxy import Server
from pydub import AudioSegment
from mutagen.mp4 import MP4
import os
import requests
import time

def convert_audio(original_file_path, download_path):
    try:
        audio = AudioSegment.from_file(original_file_path, format="m4a")
        original_metadata = MP4(original_file_path)

        title = original_metadata.tags.get('\xa9nam')
        
        if title:
            file_name = f"{title[0]}.wav"
        else:
            file_name = os.path.splitext(os.path.basename(original_file_path))[0] + ".wav"

        wav_path = os.path.join(download_path, file_name)

        audio.export(wav_path, format="wav")
        
        print(f"Converted to WAV: {wav_path}")
        os.remove(original_file_path)
        print(f"Deleted original file: {original_file_path}")
    except Exception as e:
        print(f"Error converting {original_file_path}: {e}")

bmp_path = 'C:\\browsermob-proxy\\bin\\browsermob-proxy'
server = Server(bmp_path, options={'port': 8090})
server.start()
proxy = server.create_proxy()

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument(f'--proxy-server={proxy.proxy}')
chrome_options.add_argument('--ignore-certificate-errors')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

download_path = './assets'
if not os.path.exists(download_path):
    os.makedirs(download_path)

url = 'https://shinycolors.enza.fun/'
driver.get(url)

try:
    downloaded_files = []
    while True:
        proxy.new_har("audio_downloads", options={'captureHeaders': True, 'captureContent': True})

        time.sleep(10)

        audio_files = [entry['request']['url'] for entry in proxy.har['log']['entries'] 
                       if any(ext in entry['request']['url'] for ext in ['.m4a', '.mp3']) 
                       and entry['request']['url'] not in downloaded_files]
        
        for file_url in audio_files:
            file_name = file_url.split('/')[-1].split('?')[0]
            audio_file_path = os.path.join(download_path, file_name)

            if file_url not in downloaded_files:
                response = requests.get(file_url, stream=True)
                if response.status_code == 200:
                    with open(audio_file_path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    downloaded_files.append(file_url)
                    print(f'Downloaded: {audio_file_path}')

                    convert_audio(audio_file_path, download_path)
                else:
                    print(f'Failed to download {file_name}. Status code: {response.status_code}')
            else:
                print(f'File already exists, skipping: {audio_file_path}')
except KeyboardInterrupt:
    print("Script interrupted by user. Exiting.")
finally:
    driver.quit()
    server.stop()
