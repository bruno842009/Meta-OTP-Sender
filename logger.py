# -*- coding: utf-8 -*-
"""نظام تسجيل الأحداث"""
import os
import logging
from datetime import datetime


def setup_logger():
    """إعداد نظام تسجيل الأحداث"""
    # إنشاء مجلد logs
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # اسم الملف بتاريخ اليوم
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"app_{today}.log")

    # إعداد Logger
    logger = logging.getLogger("MetaOTP")
    logger.setLevel(logging.DEBUG)

    # حذف الـ handlers القديمة (لتجنب التكرار)
    if logger.handlers:
        logger.handlers.clear()

    # Handler للملف
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)

    # Handler للطرفية (اختياري)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Logger عام
logger = setup_logger()


def log_success(number, message=""):
    """تسجيل نجاح"""
    logger.info(f"✅ نجح: {number} - {message}")


def log_failed(number, reason=""):
    """تسجيل فشل"""
    logger.warning(f"❌ فشل: {number} - {reason}")


def log_error(number, error=""):
    """تسجيل خطأ"""
    logger.error(f"⚠️ خطأ: {number} - {error}")


def log_start(total_numbers, proxies_count):
    """تسجيل بدء التشغيل"""
    logger.info("=" * 50)
    logger.info(f"🚀 بدء تشغيل الأداة")
    logger.info(f"📊 عدد الأرقام: {total_numbers}")
    logger.info(f"🌐 عدد البروكسيات: {proxies_count}")
    logger.info("=" * 50)


def log_finish(success, failed, errors):
    """تسجيل انتهاء التشغيل"""
    logger.info("=" * 50)
    logger.info(f"🏁 انتهى التشغيل")
    logger.info(f"✅ نجح: {success}")
    logger.info(f"❌ فشل: {failed}")
    logger.info(f"⚠️ أخطاء: {errors}")
    logger.info("=" * 50)
