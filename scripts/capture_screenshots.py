import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def capture_tabs():
    dest_dir = Path(r"D:\Projects\ecommerce-customer-intelligence\screenshots")
    dest_dir.mkdir(parents=True, exist_ok=True)

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--hide-scrollbars")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get("http://127.0.0.1:8501")
        # Wait for Streamlit app to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="stTabs"]'))
        )
        time.sleep(3)

        tabs_meta = [
            ("01_executive_overview.png", "Overview"),
            ("02_cohort_retention.png", "Cohort Retention"),
            ("03_rfm_churn_segmentation.png", "RFM & Churn"),
            ("04_products_pareto_analysis.png", "Products & Pareto"),
            ("05_records_explorer.png", "Records Explorer"),
            ("06_star_schema_audit.png", "Star Schema & Audit"),
        ]

        # Find tab buttons
        tab_buttons = driver.find_elements(By.CSS_SELECTOR, 'button[data-baseweb="tab"]')
        print(f"Found {len(tab_buttons)} tabs")

        for idx, (filename, label) in enumerate(tabs_meta):
            if idx < len(tab_buttons):
                btn = tab_buttons[idx]
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(2)
                out_path = dest_dir / filename
                driver.save_screenshot(str(out_path))
                print(f"Captured {label} -> {out_path.name} ({out_path.stat().st_size} bytes)")

    finally:
        driver.quit()

if __name__ == "__main__":
    capture_tabs()
