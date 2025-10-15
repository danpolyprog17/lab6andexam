#!/usr/bin/env python3
"""
Основной файл для запуска Flask приложения
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
