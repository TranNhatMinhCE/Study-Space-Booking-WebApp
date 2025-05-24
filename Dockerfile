# Sử dụng Python image
FROM python:3.11-slim

# Đặt thư mục làm việc trong container
WORKDIR /app

# Sao chép file yêu cầu vào container
COPY requirements.txt .

# Cài đặt các thư viện Python
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào container
COPY . /app

WORKDIR /app/BE

# Thiết lập biến môi trường
ENV PYTHONUNBUFFERED=1

# Mở cổng 8000
EXPOSE 8000

# Lệnh chạy server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]