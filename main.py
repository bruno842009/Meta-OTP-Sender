# -*- coding: utf-8 -*-
"""Meta OTP Sender - نقطة الدخول"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import *
from file_reader import load_numbers, save_result
from proxy_manager import load_proxies_from_file
from api_bot import process_number
from logger import logger, log_start, log_finish


def main():
    show_logo()

    print(f"{GREEN}[●]{WHITE} تحميل الأرقام...")
    numbers = load_numbers("Number_List.txt")

    if not numbers:
        print(f"{RED}❌ لا توجد أرقام!")
        print(f"{WHITE}أضف أرقاماً في ملف Number_List.txt")
        logger.warning("لا توجد أرقام في Number_List.txt")
        return

    print(f"{GREEN}[●]{WHITE} عدد الأرقام: {len(numbers)}")

    proxies = load_proxies_from_file("proxies.txt")
    print(f"{GREEN}[●]{WHITE} عدد البروكسيات: {len(proxies)}")

    # عدد الخيوط
    try:
        threads = int(input(f"{GREEN}[●]{WHITE} عدد الخيوط (افتراضي 5): ").strip() or "5")
    except:
        threads = 5

    # عدد مرات إعادة OTP
    try:
        resend = int(input(f"{GREEN}[●]{WHITE} مرات إعادة OTP (افتراضي 1): ").strip() or "1")
    except:
        resend = 1

    print(f"\n{GREEN}{LINE}")
    print(f"  بدء المعالجة...")
    print(f"{LINE}{RESET}\n")

    # تسجيل بدء التشغيل
    log_start(len(numbers), len(proxies))
    logger.info(f"⚙️  عدد الخيوط: {threads}")
    logger.info(f"⚙️  مرات إعادة OTP: {resend}")

    success = 0
    failed = 0
    errors = 0

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {}

        for i, number in enumerate(numbers):
            proxy = proxies[i % len(proxies)] if proxies else None
            future = executor.submit(process_number, number, proxy, resend)
            futures[future] = number

        for future in as_completed(futures):
            number = futures[future]
            try:
                ok, msg = future.result()

                if ok:
                    success += 1
                    print(f"{GREEN}✅ {number} — {msg}{RESET}")
                    save_result(number, "Success_Numbers.txt")
                    logger.info(f"✅ نجح: {number} — {msg}")
                else:
                    failed += 1
                    print(f"{RED}❌ {number} — {msg}{RESET}")
                    save_result(number, "Failed_Numbers.txt")
                    logger.warning(f"❌ فشل: {number} — {msg}")

            except Exception as e:
                errors += 1
                print(f"{RED}⚠️  {number} — خطأ: {e}{RESET}")
                logger.error(f"⚠️  خطأ: {number} — {e}")

    # تسجيل النهاية
    log_finish(success, failed, errors)

    print(f"\n{GREEN}{LINE}")
    print(f"  📊 النتائج:")
    print(f"  ✅ نجح: {success}")
    print(f"  ❌ فشل: {failed}")
    print(f"  ⚠️  أخطاء: {errors}")
    print(f"{LINE}{RESET}")
    print(f"{CYAN}  📁 السجلات: logs/{RESET}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⏹️  تم الإيقاف{RESET}")
        logger.info("⏹️  تم إيقاف الأداة يدوياً")
    except Exception as e:
        print(f"\n{RED}❌ خطأ غير متوقع: {e}{RESET}")
        logger.exception(f"❌ خطأ غير متوقع: {e}")
