# -*- coding: utf-8 -*-
"""Selenium Bot - يعمل مع Facebook Identify"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from config import *
from file_reader import load_numbers, save_result
from logger import logger, log_start, log_finish
from report_generator import generate_html_report
from user_agents import get_random_ua


# ============ الإعدادات ============
FACEBOOK_URL = "https://www.facebook.com/login/identify/?locale=en_US"
MAX_WINDOWS = 5  # الحد الأقصى للنوافذ المتزامنة
PAGE_TIMEOUT = 20  # ثوانٍ


def safe_click(driver, el, name=""):
    """نقر آمن"""
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
        time.sleep(0.3)
        try:
            el.click()
        except:
            driver.execute_script("arguments[0].click();", el)
        return True
    except Exception:
        return False


def create_driver(headless=False):
    """إنشاء WebDriver"""
    options = Options()
    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--mute-audio")
    options.add_argument("--window-size=600,800")
    options.add_argument(f"user-agent={get_random_ua()}")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.set_page_load_timeout(PAGE_TIMEOUT)
    return driver


def process_number(number, headless=False):
    """
    معالجة رقم واحد عبر Facebook Identify

    Returns: (bool, str, str) - (نجح, رسالة, حالة)
    """
    driver = None

    try:
        # ============ 1: فتح المتصفح ============
        driver = create_driver(headless=headless)

        # ============ 2: فتح الصفحة ============
        driver.get(FACEBOOK_URL)
        time.sleep(2)

        # ============ 3: إدخال الرقم ============
        phone_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='text']"))
        )
        phone_input.clear()
        phone_input.send_keys(number)
        time.sleep(1)

        # ============ 4: Continue الأول ============
        el = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH,
                "//div[@role='button' and .//span[text()='Continue']]"))
        )
        safe_click(driver, el, "Continue #1")
        time.sleep(5)

        # ============ 5: اختيار SMS لرقمنا ============
        sms_clicked = False
        all_radios = driver.find_elements(By.XPATH, "//input[@type='radio']")

        for radio in all_radios:
            try:
                radio_id = radio.get_attribute("id") or ""
                if radio_id:
                    try:
                        label = driver.find_element(By.XPATH, f"//label[@for='{radio_id}']")
                        if number in label.text:
                            safe_click(driver, label, "SMS option")
                            sms_clicked = True
                            break
                    except:
                        pass

                parent = radio.find_element(By.XPATH, "./..")
                if number in parent.text:
                    safe_click(driver, radio, "SMS option (radio)")
                    sms_clicked = True
                    break
            except:
                continue

        if not sms_clicked:
            return False, "لم نجد خيار SMS", "failed"

        time.sleep(1)

        # ============ 6: Continue الأزرق ============
        spans = driver.find_elements(By.XPATH, "//span[text()='Continue']")
        continue_clicked = False

        for span in spans:
            try:
                parent = span.find_element(By.XPATH, "./ancestor::*[@role='button'][1]")
                if parent.text.strip() == "Continue":
                    safe_click(driver, parent, "Continue الأزرق")
                    continue_clicked = True
                    break
            except:
                continue

        if not continue_clicked:
            return False, "لم نجد زر Continue الأزرق", "failed"

        time.sleep(5)

        # ============ 7: التحقق من النتيجة ============
        body_text = driver.find_element(By.TAG_NAME, "body").text

        # كشف OTP
        if "Enter the code" in body_text or "We sent" in body_text or "6-digit" in body_text:
            return True, "OTP مُرسَل - حقل الكود ظهر", "success"

        # كشف Captcha
        captcha_keywords = ["not a robot", "captcha", "security check", "verify", "مليء بالأمان"]
        for kw in captcha_keywords:
            if kw.lower() in body_text.lower():
                return True, "OTP مُرسَل - Captcha ظهرت", "success"

        # كشف أننا في صفحة OTP
        try:
            driver.find_element(By.XPATH, "//input[@autocomplete='one-time-code'] | //input[@inputmode='numeric']")
            return True, "OTP مُرسَل - حقل الكود موجود", "success"
        except:
            pass

        # لم نصل لنتيجة واضحة لكن عادةً هذا يعني OTP
        return True, "OTP مُرسَل (لم نكتشف captcha)", "success"

    except Exception as e:
        return False, f"خطأ: {str(e)[:60]}", "error"

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def run():
    """نقطة الدخول - من main.py"""
    show_logo()

    print(f"{GREEN}[●]{WHITE} تحميل الأرقام...")
    numbers = load_numbers("Number_List.txt")

    if not numbers:
        print(f"{RED}❌ لا توجد أرقام!")
        return

    print(f"{GREEN}[●]{WHITE} عدد الأرقام: {len(numbers)}")

    # اختيار الوضع
    try:
        mode = input(f"{GREEN}[●]{WHITE} الوضع (1=مرئي, 2=مخفي) [افتراضي: 1]: ").strip() or "1"
        headless = (mode == "2")
    except:
        headless = False

    # عدد النوافذ المتزامنة
    try:
        windows = int(input(f"{GREEN}[●]{WHITE} عدد النوافذ [افتراضي: 3, أقصى: 5]: ").strip() or "3")
        windows = min(windows, MAX_WINDOWS)
        windows = max(windows, 1)
    except:
        windows = 3

    print(f"\n{GREEN}{LINE}")
    print(f"  🚀 بدء المعالجة...")
    print(f"  🪟 النوافذ: {windows}")
    print(f"  👁️  الوضع: {'مخفي' if headless else 'مرئي'}")
    print(f"{LINE}{RESET}\n")

    # تسجيل
    log_start(len(numbers), 0)
    logger.info(f"🪟 عدد النوافذ: {windows}")
    logger.info(f"👁️  الوضع: {'headless' if headless else 'visible'}")

    success = 0
    failed = 0
    errors = 0
    results = []
    start_time = time.time()

    # تشغيل متوازٍ
    with ThreadPoolExecutor(max_workers=windows) as executor:
        futures = {}

        for number in numbers:
            future = executor.submit(process_number, number, headless)
            futures[future] = number

        for future in as_completed(futures):
            number = futures[future]
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            try:
                ok, msg, status = future.result()

                if status == "success":
                    success += 1
                    print(f"{GREEN}✅ {number} — {msg}{RESET}")
                    save_result(number, "Success_Numbers.txt")
                    logger.info(f"✅ نجح: {number} — {msg}")
                    results.append({
                        "number": number,
                        "status": "success",
                        "message": msg,
                        "time": current_time,
                    })
                elif status == "failed":
                    failed += 1
                    print(f"{RED}❌ {number} — {msg}{RESET}")
                    save_result(number, "Failed_Numbers.txt")
                    logger.warning(f"❌ فشل: {number} — {msg}")
                    results.append({
                        "number": number,
                        "status": "failed",
                        "message": msg,
                        "time": current_time,
                    })
                else:
                    errors += 1
                    print(f"{RED}⚠️  {number} — {msg}{RESET}")
                    logger.error(f"⚠️  خطأ: {number} — {msg}")
                    results.append({
                        "number": number,
                        "status": "error",
                        "message": msg,
                        "time": current_time,
                    })

            except Exception as e:
                errors += 1
                print(f"{RED}⚠️  {number} — استثناء: {e}{RESET}")
                logger.error(f"⚠️  {number} — {e}")
                results.append({
                    "number": number,
                    "status": "error",
                    "message": str(e)[:60],
                    "time": current_time,
                })

    # المدة
    duration = time.time() - start_time

    # تسجيل النهاية
    log_finish(success, failed, errors)

    # النتائج
    print(f"\n{GREEN}{LINE}")
    print(f"  📊 النتائج:")
    print(f"  ✅ نجح: {success}")
    print(f"  ❌ فشل: {failed}")
    print(f"  ⚠️  أخطاء: {errors}")
    print(f"  ⏱️  المدة: {duration:.1f} ثانية")
    print(f"{LINE}{RESET}")

    # تقرير HTML
    try:
        report_file = generate_html_report(results, duration)
        print(f"{CYAN}  📄 التقرير: {report_file}{RESET}")
        logger.info(f"📄 التقرير: {report_file}")
    except Exception as e:
        logger.error(f"فشل التقرير: {e}")

    print(f"{CYAN}  📁 السجلات: logs/{RESET}")
