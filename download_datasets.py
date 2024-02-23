from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from browsermobproxy import Server
import os
import requests
import time

bmp_path = 'C:\\browsermob-proxy\\bin\\browsermob-proxy'
server = Server(bmp_path, options={'port': 8090})
server.start()
proxy = server.create_proxy()

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument(f'--proxy-server={proxy.proxy}')
chrome_options.add_argument('--ignore-certificate-errors')  # Ignore SSL certificate errors

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

download_path = './assets'
if not os.path.exists(download_path):
    os.makedirs(download_path)

url = 'https://shinycolors.enza.fun/'
driver.get(url)

try:
    downloaded_files = []
    while True:
        proxy.new_har("m4a_downloads", options={'captureHeaders': True, 'captureContent': True})

        time.sleep(10)

        m4a_files = [entry['request']['url'] for entry in proxy.har['log']['entries'] if '.m4a' in entry['request']['url'] and entry['request']['url'] not in downloaded_files]
        
        for file_url in m4a_files:
            file_name = file_url.split('/')[-1].split('?')[0]
            file_path = os.path.join(download_path, file_name)

            if file_name not in downloaded_files:
                response = requests.get(file_url, stream=True)
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    downloaded_files.append(file_url)
                    print(f'Downloaded: {file_path}')
                else:
                    print(f'Failed to download {file_name}. Status code: {response.status_code}')
            else:
                print(f'File already exists, skipping: {file_path}')
except KeyboardInterrupt:
    print("Script interrupted by user. Exiting.")
finally:
    driver.quit()
    server.stop()
