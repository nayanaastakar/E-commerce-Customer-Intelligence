import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
options.add_argument("--hide-scrollbars")
driver = webdriver.Chrome(options=options)
driver.get("http://127.0.0.1:8501")
time.sleep(3)
tabs = driver.find_elements(By.CSS_SELECTOR, 'button[data-baseweb="tab"]')
for i, tab in enumerate(tabs):
    driver.execute_script("arguments[0].click();", tab)
    time.sleep(1)
    b = driver.execute_script('''
        var app = document.querySelector(".block-container");
        return {
            windowH: window.innerHeight,
            appBottom: app ? app.getBoundingClientRect().bottom : 0
        };
    ''')
    print(f"Tab {i+1} ({tab.text.strip()}): bottom = {b['appBottom']:.1f}px, windowH = {b['windowH']}px, gap below = {b['windowH'] - b['appBottom']:.1f}px")
driver.quit()
