import qrcode
import os
from PIL import Image

# Ссылка на форму опроса из дополнения к ТЗ
FEEDBACK_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdhZcExx6LSIXxk0ub55mSu-WIh23WYdGG9HY5EZhLDo7P8eA/viewform?usp=sf_link"

def generate_qr(request_id, save_path="qr_codes"):
    """
    Генерирует QR-код со ссылкой на форму обратной связи.
    Сохраняет изображение в папку save_path с именем request_<ID>.png.
    Возвращает полный путь к сохранённому файлу.
    """
    os.makedirs(save_path, exist_ok=True)
    qr = qrcode.make(FEEDBACK_URL)
    file_name = f"request_{request_id}.png"
    full_path = os.path.join(save_path, file_name)
    qr.save(full_path)
    return full_path