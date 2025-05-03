import sys
import cv2
import torch
import numpy as np
import keyboard
import time
import os
import warnings
import logging
import sqlite3
import ctypes
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QTextEdit, QGridLayout, QStatusBar,
                             QDialog, QMessageBox, QTabWidget, QFrame, QStyle)
from PySide6.QtGui import QPixmap, QImage, QFont, QColor, QIcon
from PySide6.QtCore import Qt, QTimer, Slot, QThread, Signal, QRect, QPoint, QSize
from datetime import datetime, timedelta
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl

# 245 СТРОКА ПУТЬ К МОДЕЛЬКЕ!!!
# 245 СТРОКА ПУТЬ К МОДЕЛЬКЕ!!!
# 245 СТРОКА ПУТЬ К МОДЕЛЬКЕ!!!

#сделать ini файл
def init_detection_table():
    conn = sqlite3.connect('detections.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            timestamp TEXT,
            object_type TEXT,
            confidence REAL,
            xmin INTEGER, ymin INTEGER, xmax INTEGER, ymax INTEGER
        )
    """)
    conn.commit()
    conn.close()
init_detection_table()
#сделать ini файл *если успею
warnings.filterwarnings("ignore", category=FutureWarning)
logging.getLogger().setLevel(logging.ERROR)

NUTRITION_DATA = {
    'apple': {
        'weight': 150,  
        'calories': 52, 'protein': 0.3, 'fat': 0.2, 'carbs': 13.8, 'fiber': 2.4, 'sugar': 10.4,
        'vitamins': {
            'A': 0.035, 'Beta-carotene': 0.0285, 'E': 0.39, 'K': 2.2, 'C': 7.3,
            'B1': 0.02, 'B2': 0.02, 'B3': 0.247, 'B4': 4.25, 'B5': 0.085,
            'B6': 0.065, 'B9': 2.3, 'H': 0.3, 'D': 0, 'B12': 0
        }
    },
    'banana': {
        'weight': 120,
        'calories': 89, 'protein': 1.1, 'fat': 0.3, 'carbs': 22.8, 'fiber': 2.6, 'sugar': 12.2,
        'vitamins': {
            'A': 0.003, 'Beta-carotene': 0.026, 'E': 0.1, 'K': 0.5, 'C': 8.7,
            'B1': 0.03, 'B2': 0.07, 'B3': 0.67, 'B4': 9.8, 'B5': 0.33,
            'B6': 0.37, 'B9': 20, 'H': 0.5, 'D': 0, 'B12': 0
        }
    },
    'carrot': {
        'weight': 80,
        'calories': 41, 'protein': 1.1, 'fat': 0.1, 'carbs': 9.6, 'fiber': 2.8, 'sugar': 4.7,
        'vitamins': {
            'A': 0.0, 'Beta-carotene': 8.285, 'E': 0.66, 'K': 13.2, 'C': 5.9,
            'B1': 0.066, 'B2': 0.058, 'B3': 0.983, 'B4': 8.8, 'B5': 0.273,
            'B6': 0.138, 'B9': 19, 'H': 0.6, 'D': 0, 'B12': 0
        }
    },
    'orange': {
        'weight': 130,
        'calories': 43, 'protein': 0.9, 'fat': 0.2, 'carbs': 8.3, 'fiber': 2.2, 'sugar': 8.2,
        'vitamins': {
            'A': 0.011, 'Beta-carotene': 0.071, 'E': 0.18, 'K': 0, 'C': 53.2,
            'B1': 0.087, 'B2': 0.04, 'B3': 0.282, 'B4': 8.4, 'B5': 0.25,
            'B6': 0.06, 'B9': 30, 'H': 0.1, 'D': 0, 'B12': 0
        }
    }
}

class ClickableLabel(QLabel):
    clicked = Signal(QPoint)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.detected_apples = []  # оставить для обратки
        
    def mousePressEvent(self, event):
        if hasattr(event, 'position'):
            self.clicked.emit(event.position().toPoint())
        else:
            # запаска для старых версий
            self.clicked.emit(event.pos())
        super().mousePressEvent(event)
        
    


class RoundedFrame(QFrame):
    """адаем рамку со скруг краями"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("roundedFrame")

class Detection_Thread(QThread):
    # сигналы для реада интерфейса
    update_frame = Signal(object)
    update_info = Signal(object)
    update_fruits = Signal(dict)  # Новый сигнал (БЫЛ APPLE_UPDATE)
    
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.running = True
        self.paused = False
        self.cap = None
        self.frame_width = 0
        self.frame_height = 0

    
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.running = True
        self.paused = False
        self.cap = None
        self.frame_width = 0
        self.frame_height = 0
    
    def run(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Не удалось открыть камеру")
            return
            
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        while self.running:
            if self.paused:
                time.sleep(0)
                continue
                
            ret, frame = self.cap.read()
            if not ret:
                print("Не удалось получить кадр")
                break
                
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # НЕ ЗАБЫТЬ ЦВЕТОКОР
            
            results = self.model(frame_rgb)  
            
            df = results.pandas().xyxy[0]  # pandas DataFrame
            
            apples = []
            bananas = []
            carrots = []
            oranges = []
            if not df.empty:
                for idx, row in df.iterrows():
                    if row['name'].lower() == 'apple' and row['confidence'] > 0.4:
                        apple_info = {
                            'xmin': int(row['xmin']), 
                            'ymin': int(row['ymin']), 
                            'xmax': int(row['xmax']), 
                            'ymax': int(row['ymax']),
                            'confidence': float(row['confidence']),
                            'type': 'apple'
                        }
                        apples.append(apple_info)
                    elif row['name'].lower() == 'banana' and row['confidence'] > 0.4:
                        banana_info = {
                            'xmin': int(row['xmin']), 
                            'ymin': int(row['ymin']), 
                            'xmax': int(row['xmax']), 
                            'ymax': int(row['ymax']),
                            'confidence': float(row['confidence']),
                            'type': 'banana'
                        }
                        bananas.append(banana_info)
                    elif row['name'].lower() == 'carrot' and row['confidence'] > 0.4:
                        carrot_info = {
                            'xmin': int(row['xmin']), 
                            'ymin': int(row['ymin']), 
                            'xmax': int(row['xmax']), 
                            'ymax': int(row['ymax']),
                            'confidence': float(row['confidence']),
                            'type': 'carrot'
                        }
                        carrots.append(carrot_info)
                    elif row['name'].lower() == 'orange' and row['confidence'] > 0.4:
                        orange_info = {
                            'xmin': int(row['xmin']), 
                            'ymin': int(row['ymin']), 
                            'xmax': int(row['xmax']), 
                            'ymax': int(row['ymax']),
                            'confidence': float(row['confidence']),
                            'type': 'orange'
                        }
                        oranges.append(orange_info)
            fruits = {'apples': apples, 'bananas': bananas, 'oranges': oranges, 'carrots': carrots}
            self.update_fruits.emit(fruits)

            
            self.update_info.emit(df)
            
            annotated_frame = frame.copy()  # кадр с анашками
            annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            
            # Рисуем рамки
            for apple in apples:
                cv2.rectangle(annotated_frame, (apple['xmin'], apple['ymin']), (apple['xmax'], apple['ymax']), (76, 175, 80), 2)
                cv2.putText(annotated_frame, "Apple!", (apple['xmin'], apple['ymin'] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (76, 175, 80), 2)
            
            for banana in bananas:
                cv2.rectangle(annotated_frame, (banana['xmin'], banana['ymin']), (banana['xmax'], banana['ymax']), (0, 165, 255), 2)
                cv2.putText(annotated_frame, "Banana!", (banana['xmin'], banana['ymin'] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            for carrot in carrots:
                cv2.rectangle(annotated_frame, (carrot['xmin'], carrot['ymin']), (carrot['xmax'], carrot['ymax']), (255, 140, 0), 2)
                cv2.putText(annotated_frame, "Carrot!", (carrot['xmin'], carrot['ymin'] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 140, 0), 2)
            for orange in oranges:
                cv2.rectangle(annotated_frame, (orange['xmin'], orange['ymin']), (orange['xmax'], orange['ymax']), (255, 102, 0), 2)
                cv2.putText(annotated_frame, "Orange!", (orange['xmin'], orange['ymin'] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 102, 0), 2)

            self.update_frame.emit(annotated_frame)
            
    
    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
    
    def toggle_pause(self):
        self.paused = not self.paused
        return self.paused

class YOLOv5DetectionApp(QMainWindow):
    def __init__(self, user_id=None, username=None):
        super().__init__()
        
        # инфа о юзере
        self.user_id = user_id
        self.username = username
        
        self.setWindowTitle(f"VitaVision - {username}" if username else "VitaVision")
        self.setGeometry(100, 100, 1000, 600)
        
        # ПУТЬ К МОДЕЛЬКЕ!!!!!!
        self.model_path = 'D:/hakaton/predfinal.pt' 
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=self.model_path)
        self.model.conf = 0.5 
    
        self.model.classes = [46, 47, 49, 51] 
        self.fruits = {'apples': [], 'bananas': [], 'oranges': [], 'carrots': []}

        self.apply_styles() #ад программиста (аплаим стили)
        self.setup_ui()
        
        # Настройка глобальной горячей клавиши для паузы (дебажное)
        keyboard.add_hotkey('p', self.toggle_pause)
        
        self.detection_thread = None
        self.apples = []
    def show_diet_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Сводка по питанию (за последние 24 часа)")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(500)
        
        layout = QVBoxLayout()
        
        # на доработку.... (сводка о питании)
        summary = self.get_user_nutrition_summary()
        
    
        title_label = QLabel("Ваша суточная сводка по питанию")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50; margin-bottom: 15px;")
        layout.addWidget(title_label)
        
        tab_widget = QTabWidget()
        
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        
        if summary["fruits"]:
            fruits_label = QLabel("Просканированные продукты:")
            fruits_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
            summary_layout.addWidget(fruits_label)
            
            fruits_text = QTextEdit()
            fruits_text.setReadOnly(True)
            fruits_html = "<ul>"
            
            for fruit, count in summary["fruits"].items():
                fruit_name = fruit.capitalize()
                fruit_weight = NUTRITION_DATA.get(fruit, {}).get("weight", 0) * count
                fruits_html += f"<li><b>{fruit_name}:</b> {count} шт. ({fruit_weight:.0f} г)</li>"
            
            fruits_html += "</ul>"
            fruits_text.setHtml(fruits_html)
            fruits_text.setMaximumHeight(120)
            summary_layout.addWidget(fruits_text)
            
            macro_label = QLabel("Макронутриенты:")
            macro_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; margin-top: 10px;")
            summary_layout.addWidget(macro_label)
            
            macro_text = QTextEdit()
            macro_text.setReadOnly(True)
            macro_html = "<table style='width:100%'>"
            macro_html += "<tr><td><b>Калории:</b></td><td>{:.1f} ккал</td></tr>".format(summary["calories"])
            macro_html += "<tr><td><b>Белки:</b></td><td>{:.2f} г</td></tr>".format(summary["protein"])
            macro_html += "<tr><td><b>Жиры:</b></td><td>{:.2f} г</td></tr>".format(summary["fat"])
            macro_html += "<tr><td><b>Углеводы:</b></td><td>{:.2f} г</td></tr>".format(summary["carbs"])
            macro_html += "<tr><td><b>Клетчатка:</b></td><td>{:.2f} г</td></tr>".format(summary["fiber"])
            macro_html += "<tr><td><b>Сахар:</b></td><td>{:.2f} г</td></tr>".format(summary["sugar"])
            macro_html += "</table>"
            macro_text.setHtml(macro_html)
            macro_text.setMaximumHeight(150)
            summary_layout.addWidget(macro_text)
        else:
            no_data_label = QLabel("За последние 24 часа вы не сканировали никаких продуктов.")
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setStyleSheet("color: #888; font-size: 14px; padding: 20px;")
            summary_layout.addWidget(no_data_label)
        
        vitamins_tab = QWidget()
        vitamins_layout = QVBoxLayout(vitamins_tab)
        
        if summary["fruits"]:
            vitamins_text = QTextEdit()
            vitamins_text.setReadOnly(True)
            vitamins_html = "<table style='width:100%'>"
            
            for vit, amount in summary["vitamins"].items():
                if amount > 0:  
                    vit_name = vit
                    if vit == "A": vit_name = "A (Ретинол)"
                    elif vit == "C": vit_name = "C (Аскорбиновая кислота)"
                    elif vit == "E": vit_name = "E (Токоферол)"
                    elif vit == "K": vit_name = "K (Филлохинон)"
                    elif vit == "B1": vit_name = "B1 (Тиамин)"
                    elif vit == "B2": vit_name = "B2 (Рибофлавин)"
                    elif vit == "B3": vit_name = "B3 (Ниацин)"
                    elif vit == "B4": vit_name = "B4 (Холин)"
                    elif vit == "B5": vit_name = "B5 (Пантотеновая кислота)"
                    elif vit == "B6": vit_name = "B6 (Пиридоксин)"
                    elif vit == "B9": vit_name = "B9 (Фолиевая кислота)"
                    elif vit == "H": vit_name = "H (Биотин)"
                    
                    vitamins_html += f"<tr><td><b>Витамин {vit_name}:</b></td><td>{amount:.2f} мг</td></tr>"
            
            vitamins_html += "</table>"
            vitamins_text.setHtml(vitamins_html)
            vitamins_layout.addWidget(vitamins_text)
            
            vitamin_info_label = QLabel("Польза этих витаминов:")
            vitamin_info_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; margin-top: 10px;")
            vitamins_layout.addWidget(vitamin_info_label)
            
            vitamin_info_text = QTextEdit()
            vitamin_info_text.setReadOnly(True)
            vitamin_info_html = "<ul>"
            
            if summary["vitamins"].get("A", 0) > 0:
                vitamin_info_html += "<li><b>Витамин A:</b> Поддерживает зрение, иммунную функцию и рост клеток.</li>"
            if summary["vitamins"].get("C", 0) > 0:
                vitamin_info_html += "<li><b>Витамин C:</b> Антиоксидант, помогает иммунной системе, усвоению железа и заживлению ран.</li>"
            if summary["vitamins"].get("E", 0) > 0:
                vitamin_info_html += "<li><b>Витамин E:</b> Антиоксидант, защищающий клетки от повреждений.</li>"
            if summary["vitamins"].get("K", 0) > 0:
                vitamin_info_html += "<li><b>Витамин K:</b> Необходим для свертывания крови и здоровья костей.</li>"
            if summary["vitamins"].get("B1", 0) > 0:
                vitamin_info_html += "<li><b>Витамин B1:</b> Помогает преобразовывать пищу в энергию и поддерживает функцию нервной системы.</li>"
            
            vitamin_info_html += "</ul>"
            vitamin_info_text.setHtml(vitamin_info_html)
            vitamins_layout.addWidget(vitamin_info_text)
        else:
            no_data_label = QLabel("Данные о витаминах отсутствуют.")
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setStyleSheet("color: #888; font-size: 14px; padding: 20px;")
            vitamins_layout.addWidget(no_data_label)
        
        recommendations_tab = QWidget()
        recommendations_layout = QVBoxLayout(recommendations_tab)
        
        recommendations_text = QTextEdit()
        recommendations_text.setReadOnly(True)
        
        if summary["fruits"]:
            recommendations_html = "<h3 style='color: #4CAF50;'>Рекомендации по питанию</h3>"
            
            if summary["calories"] < 100:
                recommendations_html += "<p>Ваше потребление фруктов <b>низкое по калориям</b>. Рассмотрите возможность добавления большего количества фруктов в рацион для лучшего питания.</p>"
            elif summary["calories"] > 500:
                recommendations_html += "<p>Ваше потребление фруктов <b>высокое по калориям</b>. Хотя фрукты полезны, следите за общим дневным потреблением калорий.</p>"
            
            if summary["vitamins"].get("C", 0) < 30:
                recommendations_html += "<p>Ваше потребление <b>витамина C</b> низкое. Рассмотрите возможность добавления в рацион большего количества цитрусовых, клубники или киви.</p>"
            
            if len(summary["fruits"]) < 3:
                recommendations_html += "<p>Старайтесь увеличить <b>разнообразие фруктов</b> в своем рационе для получения более широкого спектра питательных веществ.</p>"
        
            recommendations_html += "<h4 style='color: #FF9800;'>Общие советы</h4>"
            recommendations_html += "<ul>"
            recommendations_html += "<li>Стремитесь к употреблению не менее 2-3 различных фруктов в день</li>"
            recommendations_html += "<li>Включайте фрукты разных цветов для получения различных питательных веществ</li>"
            recommendations_html += "<li>Свежие, замороженные и сушеные фрукты учитываются в вашем ежедневном рационе</li>"
            recommendations_html += "<li>Старайтесь употреблять фрукты целиком, а не в соках, когда это возможно</li>"
            recommendations_html += "</ul>"
        else:
            recommendations_html = "<h3 style='color: #4CAF50;'>Рекомендации по питанию</h3>"
            recommendations_html += "<p>За последние 24 часа не было отсканировано ни одного фрукта. Вот некоторые общие рекомендации:</p>"
            recommendations_html += "<ul>"
            recommendations_html += "<li>Стремитесь съедать не менее 2-3 порций фруктов в день</li>"
            recommendations_html += "<li>Выбирайте разнообразные цветные фрукты для получения различных питательных веществ</li>"
            recommendations_html += "<li>Ягоды, яблоки и цитрусовые отлично подходят для ежедневного употребления</li>"
            recommendations_html += "</ul>"
        
        recommendations_text.setHtml(recommendations_html)
        recommendations_layout.addWidget(recommendations_text)
        
        tab_widget.addTab(summary_tab, "Сводка")
        tab_widget.addTab(vitamins_tab, "Витамины")
        tab_widget.addTab(recommendations_tab, "Рекомендации")
        layout.addWidget(tab_widget)
        
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.setLayout(layout)
        dialog.exec()



    @Slot(dict)
    def update_fruits(self, fruits):
        self.fruits = fruits
        
    def apply_styles(self):
        self.setStyleSheet("""
            QPushButton#startButton {
            background-color: #39e35e;
            color: black;
        }
        QPushButton#startButton:hover {
            background-color: #007f00;
            color: black;
        }
        QPushButton#stopButton {
            background-color: #f26646;
            color: white;
        }
        QPushButton#stopButton:hover {
            background-color: #c74c2c; /* темнее, не белый */
            color: black;
        }
        QPushButton#stopButton:disabled {
            background-color: #95999e;
            color: #eeeeee;
        }

        QPushButton#pauseButton {
            background-color: #5da0f5;
            color: white;
        }
        QPushButton#pauseButton:hover {
            background-color: #4178c2; /* темнее, не белый */
            color: black;
        }
        QPushButton#pauseButton:disabled {
            background-color: #95999e;
            color: #eeeeee;
        }

        QPushButton#dietButton {
            background-color: #f5d549;
            color: #333333;
        }
        QPushButton#dietButton:hover {
            background-color: #c6a91a; /* темнее, не белый */
            color: black;
        }

        QPushButton#logoutButton {
            background-color: #f26646;
            color: white;
        }
        QPushButton#logoutButton:hover {
            background-color: #8a0a21; /* темнее, не белый */
            color: black;
        }

            
            QTextEdit {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                font-family: Arial;
                font-size: 13px;
                selection-background-color: #4CAF50;
                selection-color: white;
            }
            
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            
            QFrame#roundedFrame {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                margin: 8px;
            }
            
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px;
            }
            
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #e0e0e0;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 100px;
                padding: 8px 12px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #4CAF50;
            }
            
            QTabBar::tab:hover {
                background-color: #e9e9e9;
            }
            
            QStatusBar {
                background-color: #f5f5f5;
                color: #555555;
                border-top: 1px solid #e0e0e0;
            }
        """)
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        #панелька с кнопками
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        self.start_btn = QPushButton("Запустить")
        self.start_btn.setObjectName("startButton")
        self.start_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.start_btn.setIconSize(QSize(18, 18))
        self.start_btn.clicked.connect(self.start_detection)
        
        self.pause_btn = QPushButton("Пауза (P)")
        self.pause_btn.setObjectName("pauseButton")
        self.pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.pause_btn.setIconSize(QSize(18, 18))
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("Остановить")
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_btn.setIconSize(QSize(18, 18))
        self.stop_btn.clicked.connect(self.stop_detection)
        self.stop_btn.setEnabled(False)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addStretch()  
        
        self.logout_btn = QPushButton("Выйти")
        self.logout_btn.setObjectName("logoutButton")
        self.logout_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
        self.logout_btn.setIconSize(QSize(18, 18))
        self.logout_btn.clicked.connect(self.logout)
        control_layout.addWidget(self.logout_btn)

        self.diet_btn = QPushButton("Диеты")
        self.diet_btn.setObjectName("dietButton")
        self.diet_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogInfoView))
        self.diet_btn.setIconSize(QSize(18, 18))
        self.diet_btn.clicked.connect(self.show_diet_dialog)
        control_layout.addWidget(self.diet_btn)
        
        # рамочка с видео (жертвоприношением кодера)
        video_frame = RoundedFrame()
        video_layout = QVBoxLayout(video_frame)
        video_layout.setContentsMargins(10, 10, 10, 10)
        
        #область отображения (кликабельно)
        self.video_label = ClickableLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setText("Нажмите 'Запустить' для начала обнаружения")
        self.video_label.setStyleSheet("QLabel { color: #888888; font-size: 16px; }")
        self.video_label.clicked.connect(self.handle_click)  
        video_layout.addWidget(self.video_label)
        
        
        # Статусбар
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        if self.username:
            self.statusBar.showMessage(f"Пользователь: {self.username} | Готов к работе. Нажмите 'P' для глобальной паузы.")
        else:
            self.statusBar.showMessage("Готов к работе. Нажмите 'P' для глобальной паузы.")
        
        # адаем в главный лейаут
        main_layout.addWidget(control_panel)
        main_layout.addWidget(video_frame, 3)

    def logout(self):
        
        self.stop_detection()
        
        # делитаем токен(если он есть)
        token_file = 'remember_token.dat'
        if os.path.exists(token_file):
            try:
                os.remove(token_file)
            except Exception as e:
                print(f"Ошибка при удалении токена: {e}")
                
        from login import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()

    def start_detection(self):
        if not self.detection_thread:
            self.detection_thread = Detection_Thread(self.model)
            self.detection_thread.update_frame.connect(self.update_frame)
            self.detection_thread.update_info.connect(self.update_info)
            self.detection_thread.update_fruits.connect(self.update_fruits)
            self.detection_thread.start()
            
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.statusBar.showMessage("Обнаружение запущено")
    
    def stop_detection(self):
        if self.detection_thread:
            self.detection_thread.stop()
            self.detection_thread.wait()
            self.detection_thread = None
            
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            
            self.video_label.setText("Обнаружение остановлено")
            
            self.statusBar.showMessage("Обнаружение остановлено")
        
            self.apples = []
            
        if self.username:
            self.statusBar.showMessage(f"Пользователь: {self.username} | Готов к работе. Нажмите 'P' для глобальной паузы.")
        else:
            self.statusBar.showMessage("Готов к работе. Нажмите 'P' для глобальной паузы.")
    
    def toggle_pause(self):
        if self.detection_thread:
            paused = self.detection_thread.toggle_pause()
            
            if paused:
                self.statusBar.showMessage("ПАУЗА")
                self.pause_btn.setText("Продолжить (P)")
                self.pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
                
                pause_img = np.zeros((480, 640, 3), dtype=np.uint8)
                pause_img.fill(240)  
                
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 2
                text = "ПАУЗА"
                thickness = 3
                text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
                
                text_x = (pause_img.shape[1] - text_size[0]) // 2
                text_y = (pause_img.shape[0] + text_size[1]) // 2
                
                cv2.putText(pause_img, text, (text_x, text_y), font, font_scale, (70, 70, 70), thickness)
                self.update_frame(pause_img)
                
                print("Программа ПРИОСТАНОВЛЕНА")
            else:
                self.statusBar.showMessage("Обнаружение возобновлено")
                self.pause_btn.setText("Пауза (P)")
                self.pause_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
                print("Программа ВОЗОБНОВЛЕНА")
    
    @Slot(object)
    def update_frame(self, frame):
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        self.video_label.setPixmap(pixmap.scaled(self.video_label.width(), self.video_label.height(), 
                                                Qt.KeepAspectRatio, Qt.SmoothTransformation))
    
    @Slot(object)
    def update_info(self, df):
        
        for idx, row in df.iterrows():
            object_name = row['name']
            confidence = row['confidence']
            
            color = "#4CAF50"  # Зелени
            if object_name.lower() == 'apple':
                color = "#ff9800"  # Оранжевый
            
            if confidence < 0.4:
                confidence_color = "#f44336"  # Красный для низкой уверенности
            elif confidence < 0.7:
                confidence_color = "#ff9800"  # Оранжевый для средней уверенности
            else:
                confidence_color = "#4CAF50"  # Зеленый для высокой уверенности
            
           
    
    @Slot(list)
    def update_apples(self, apples):
        """Обновляет список обнаруженных яблок"""
        self.apples = apples
        self.video_label.update_apples(apples)
    
    def handle_click(self, pos):
        try:
            if not self.fruits:
                print("No fruits detected")
                return
            
            if self.detection_thread and self.detection_thread.cap:
                frame_width = self.detection_thread.frame_width
                frame_height = self.detection_thread.frame_height
                label_width = self.video_label.width()
                label_height = self.video_label.height()
                
                scalex = label_width / frame_width
                scaley = label_height / frame_height
                scale = min(scalex, scaley)
                
                offsetx = (label_width - frame_width * scale) / 2
                offsety = (label_height - frame_height * scale) / 2
                
                framex = (pos.x() - offsetx) / scale
                framey = (pos.y() - offsety) / scale
                
                for fruittype, fruitlist in self.fruits.items():
                    for fruit in fruitlist:
                        if fruit["xmin"] <= framex <= fruit["xmax"] and fruit["ymin"] <= framey <= fruit["ymax"]:
                            print(f"Found {fruittype}!")
                            
                            self.save_clicked_fruit(fruit, fruittype)
                            
                            self.show_fruit_info_dialog(fruit, fruittype)
                            break
        except Exception as e:
            print(f"Error: {e}")


    def save_clicked_fruit(self, fruit, fruittype):
        """на доработку...."""
        try:
            
            object_type = fruittype[:-1] if fruittype.endswith('s') else fruittype
            
            conn = sqlite3.connect('detections.db')
            cursor = conn.cursor()
            
            cursor.execute('''INSERT INTO detections 
                        (user_id, timestamp, object_type, confidence, xmin, ymin, xmax, ymax) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                        (self.user_id, datetime.now().isoformat(), object_type, 
                        fruit["confidence"], fruit["xmin"], fruit["ymin"], 
                        fruit["xmax"], fruit["ymax"]))
            
            conn.commit()
            conn.close()
            
            self.statusBar.showMessage(f"{object_type.capitalize()} добавлен в ваш дневной журнал питания", 3000)
            
            
        except Exception as e:
            print("Error saving clicked fruit: %s", e)
    def add_fruit_to_journal(self, fruit, fruit_type):
        try:
            object_type = fruit_type[:-1] if fruit_type.endswith('s') else fruit_type
            
            conn = sqlite3.connect('detections.db')
            cursor = conn.cursor()
            
            cursor.execute('''INSERT INTO detections 
                        (user_id, timestamp, object_type, confidence, xmin, ymin, xmax, ymax) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                        (self.user_id, datetime.now().isoformat(), object_type, 
                        fruit["confidence"], fruit["xmin"], fruit["ymin"], 
                        fruit["xmax"], fruit["ymax"]))
            
            conn.commit()
            conn.close()
            
            product_name = object_type.capitalize()
            self.statusBar.showMessage(f"{product_name} добавлен в ваш дневной журнал питания", 3000)
            self.sound = QSoundEffect()
            sound_path = "D:/hakaton/succes1.wav" 
            self.sound.setSource(QUrl.fromLocalFile(sound_path))
            self.sound.setVolume(1.0)
            self.sound.play() 
            msg = QMessageBox(self)
            msg.setWindowTitle("Добавлено")
            msg.setText(f"{product_name} добавлен в расчет витаминов за день!")
            msg.setIcon(QMessageBox.NoIcon)  # чтоб не было звука винды
            msg.exec()
            
            
            
            
        except Exception as e:
            print(f"Error adding fruit to journal: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось добавить в журнал: {str(e)}")

    def show_fruit_info_dialog(self, fruit, fruit_type):
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Информация о фрукте")
            dialog.setMinimumWidth(450)
            dialog.setMinimumHeight(450)
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #f9f9f9;
                }
                QTabWidget::pane {
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    background-color: white;
                }
                QTabBar::tab {
                    background-color: #f0f0f0;
                    border: 1px solid #e0e0e0;
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    min-width: 100px;
                    padding: 8px 12px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: white;
                    border-bottom: 2px solid #4CAF50;
                }
                QTextEdit {
                    border: none;
                    background-color: white;
                }
                QPushButton {
                    background-color: #95999e;
                    color: white;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """)
            
            layout = QVBoxLayout()
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)
            
            header_label = QLabel()
            header_label.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; border-radius: 8px; font-size: 18px; font-weight: bold;")
            
            if fruit_type == 'apples':
                header_label.setText("Яблоко!")
                confidence_value = fruit['confidence'] * 100
            elif fruit_type == 'bananas':
                header_label.setText("Банан!")
                confidence_value = fruit['confidence'] * 100
            elif fruit_type == 'carrots':
                header_label.setText("Морковь!")
                confidence_value = fruit['confidence'] * 100
            elif fruit_type == 'oranges':
                header_label.setText("Апельсин!")
                confidence_value = fruit['confidence'] * 100

            header_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(header_label)
            
            confidence_text = f"Уверенность распознавания: {confidence_value:.1f}%"
            info_text = QLabel(confidence_text)
            info_text.setAlignment(Qt.AlignCenter)
            info_text.setStyleSheet("font-size: 14px; margin-bottom: 10px; color: #555;")
            layout.addWidget(info_text)
            
            tabs = QTabWidget()
            
            vitamins_tab = QWidget()
            vitamins_layout = QVBoxLayout(vitamins_tab)
            
            vitamins_info = QTextEdit()
            vitamins_info.setReadOnly(True)
            
            if fruit_type == 'apples':
                vitamins_info.setHtml("""
        <h3 style="color: #4CAF50; margin-top: 0;">Витамины и минералы (на 100 г яблока)</h3>
        <table style="width:100%; font-size:14px; margin-bottom:10px;">
            <tr><td><b>Витамин A (ретинол)</b></td><td>0,02–0,05 мг</td></tr>
            <tr><td><b>Бета-каротин</b></td><td>0,027–0,03 мг</td></tr>
            <tr><td><b>Витамин E (токоферол)</b></td><td>0,18–0,6 мг</td></tr>
            <tr><td><b>Витамин K (филлохинон)</b></td><td>2,2 мкг</td></tr>
            <tr><td><b>Витамин C (аскорбиновая кислота)</b></td><td>4,6–10 мг</td></tr>
            <tr><td><b>Витамин B1 (тиамин)</b></td><td>0,01–0,03 мг</td></tr>
            <tr><td><b>Витамин B2 (рибофлавин)</b></td><td>0,01–0,03 мг</td></tr>
            <tr><td><b>Витамин B3 (PP, ниацин)</b></td><td>0,094–0,4 мг</td></tr>
            <tr><td><b>Витамин B4 (холин)</b></td><td>3,4–5,1 мг</td></tr>
            <tr><td><b>Витамин B5 (пантотеновая кислота)</b></td><td>0,07–0,1 мг</td></tr>
            <tr><td><b>Витамин B6 (пиридоксин)</b></td><td>0,051–0,08 мг</td></tr>
            <tr><td><b>Витамин B9 (фолиевая кислота)</b></td><td>1,6–3,0 мкг</td></tr>
            <tr><td><b>Витамин H (биотин)</b></td><td>0,3 мкг</td></tr>
            <tr><td><b>Витамин D</b></td><td>0</td></tr>
            <tr><td><b>Витамин B12</b></td><td>0</td></tr>
        </table>
        <p style="font-size:13px; color:#555;">
            <b>Примечания:</b><br>
            - В яблоках нет витаминов D и B12, так как они характерны для продуктов животного происхождения.<br>
            - Витамин C содержится преимущественно под кожурой. Кислые сорта обычно богаче этим витамином.<br>
            - Витамин A и бета-каротин поддерживают иммунитет и здоровье зрения.<br>
            - Витамины группы B участвуют в обмене веществ, работе нервной системы и кроветворении.<br>
            - Витамин E - антиоксидант, защищающий клетки от повреждений.<br>
            - Витамин K участвует в процессе свертывания крови.<br>
            <br>
            Также в яблоках присутствуют органические кислоты (яблочная, лимонная, винная, хлорогеновая, урсоловая), пектины, клетчатка и микроэлементы (калий, железо, магний, фосфор и др.).<br>
            <b>Состав зависит от сорта, зрелости, условий хранения и региона выращивания.</b>
        </p>
    """)
            elif fruit_type == 'bananas':
                vitamins_info.setHtml("""
                <h3 style="color: #4CAF50; margin-top: 0;">Витамины и минералы (на 100 г банана)</h3>
        <table style="width:100%; font-size:14px; margin-bottom:10px;">
            <tr><td><b>Витамин A (ретинол)</b></td><td>3 мкг</td></tr>
            <tr><td><b>Бета-каротин</b></td><td>26 мкг</td></tr>
            <tr><td><b>Витамин E (токоферол)</b></td><td>0,1 мг</td></tr>
            <tr><td><b>Витамин K (филлохинон)</b></td><td>0,5 мкг</td></tr>
            <tr><td><b>Витамин C (аскорбиновая кислота)</b></td><td>8,7 мг</td></tr>
            <tr><td><b>Витамин B1 (тиамин)</b></td><td>0,03 мг</td></tr>
            <tr><td><b>Витамин B2 (рибофлавин)</b></td><td>0,07 мг</td></tr>
            <tr><td><b>Витамин B3 (PP, ниацин)</b></td><td>0,67 мг</td></tr>
            <tr><td><b>Витамин B4 (холин)</b></td><td>9,8 мг</td></tr>
            <tr><td><b>Витамин B5 (пантотеновая кислота)</b></td><td>0,33 мг</td></tr>
            <tr><td><b>Витамин B6 (пиридоксин)</b></td><td>0,37 мг</td></tr>
            <tr><td><b>Витамин B9 (фолиевая кислота)</b></td><td>20 мкг</td></tr>
            <tr><td><b>Витамин H (биотин)</b></td><td>0,5 мкг</td></tr>
            <tr><td><b>Витамин D</b></td><td>0</td></tr>
            <tr><td><b>Витамин B12</b></td><td>0</td></tr>
        </table>
        <p style="font-size:13px; color:#555;">
            <b>Примечания:</b><br>
            - В бананах нет витаминов D и B12, так как они характерны для продуктов животного происхождения.<br>
            - Бананы богаты витамином B6 (до 33% суточной нормы в одном среднем банане), а также калием, витамином C и пищевыми волокнами.<br>
            - Витамин C помогает иммунитету и защищает клетки от повреждений.<br>
            - Витамины группы B поддерживают обмен веществ, работу нервной системы и кроветворение.<br>
            - Витамин A и бета-каротин важны для зрения и иммунитета.<br>
            - В бананах содержатся антиоксиданты (например, допамин и катехины), а также органические кислоты, пектины, клетчатка и микроэлементы (калий, магний, фосфор, железо и др.).<br>
            <b>Состав зависит от сорта, зрелости и условий хранения.</b>
        </p>
        """)
            elif fruit_type == 'carrots':
                vitamins_info.setHtml("""
                <h3 style="color: #4CAF50; margin-top: 0;">Витамины и минералы (на 100 г моркови)</h3>
                <table style="width:100%; font-size:14px; margin-bottom:10px;">
                    <tr><td><b>Витамин A (ретинол)</b></td><td>0,0 мг</td></tr>
                    <tr><td><b>Бета-каротин</b></td><td>8,285 мг</td></tr>
                    <tr><td><b>Витамин E (токоферол)</b></td><td>0,66 мг</td></tr>
                    <tr><td><b>Витамин K (филлохинон)</b></td><td>13,2 мкг</td></tr>
                    <tr><td><b>Витамин C (аскорбиновая кислота)</b></td><td>5,9 мг</td></tr>
                    <tr><td><b>Витамин B1 (тиамин)</b></td><td>0,066 мг</td></tr>
                    <tr><td><b>Витамин B2 (рибофлавин)</b></td><td>0,058 мг</td></tr>
                    <tr><td><b>Витамин B3 (PP, ниацин)</b></td><td>0,983 мг</td></tr>
                    <tr><td><b>Витамин B4 (холин)</b></td><td>8,8 мг</td></tr>
                    <tr><td><b>Витамин B5 (пантотеновая кислота)</b></td><td>0,273 мг</td></tr>
                    <tr><td><b>Витамин B6 (пиридоксин)</b></td><td>0,138 мг</td></tr>
                    <tr><td><b>Витамин B9 (фолиевая кислота)</b></td><td>19 мкг</td></tr>
                    <tr><td><b>Витамин H (биотин)</b></td><td>0,6 мкг</td></tr>
                    <tr><td><b>Витамин D</b></td><td>0</td></tr>
                    <tr><td><b>Витамин B12</b></td><td>0</td></tr>
                </table>
                <p style="font-size:13px; color:#555;">
                    <b>Примечания:</b><br>
                    - Морковь - лидер по содержанию бета-каротина, предшественника витамина A.<br>
                    - Витамин C и E - антиоксиданты.<br>
                    - Витамины группы B поддерживают обмен веществ и нервную систему.<br>
                    - Витамин K важен для свертывания крови.<br>
                    <br>
                    Также содержит калий, магний, фосфор, кальций, железо, клетчатку.<br>
                    <b>Состав зависит от сорта, зрелости и условий хранения.</b>
                </p>
                """)
            elif fruit_type == 'oranges':
                vitamins_info.setHtml("""
                <h3 style="color: #4CAF50; margin-top: 0;">Витамины и минералы (на 100 г апельсина)</h3>
                <table style="width:100%; font-size:14px; margin-bottom:10px;">
                    <tr><td><b>Витамин A (ретинол)</b></td><td>0,011 мг</td></tr>
                    <tr><td><b>Бета-каротин</b></td><td>0,071 мг</td></tr>
                    <tr><td><b>Витамин E (токоферол)</b></td><td>0,18 мг</td></tr>
                    <tr><td><b>Витамин K (филлохинон)</b></td><td>0 мкг</td></tr>
                    <tr><td><b>Витамин C (аскорбиновая кислота)</b></td><td>53,2 мг</td></tr>
                    <tr><td><b>Витамин B1 (тиамин)</b></td><td>0,087 мг</td></tr>
                    <tr><td><b>Витамин B2 (рибофлавин)</b></td><td>0,04 мг</td></tr>
                    <tr><td><b>Витамин B3 (PP, ниацин)</b></td><td>0,282 мг</td></tr>
                    <tr><td><b>Витамин B4 (холин)</b></td><td>8,4 мг</td></tr>
                    <tr><td><b>Витамин B5 (пантотеновая кислота)</b></td><td>0,25 мг</td></tr>
                    <tr><td><b>Витамин B6 (пиридоксин)</b></td><td>0,06 мг</td></tr>
                    <tr><td><b>Витамин B9 (фолиевая кислота)</b></td><td>30 мкг</td></tr>
                    <tr><td><b>Витамин H (биотин)</b></td><td>0,1 мкг</td></tr>
                    <tr><td><b>Витамин D</b></td><td>0</td></tr>
                    <tr><td><b>Витамин B12</b></td><td>0</td></tr>
                </table>
                <p style="font-size:13px; color:#555;">
                    <b>Примечания:</b><br>
                    - Апельсины - один из лучших источников витамина C.<br>
                    - Витамины группы B поддерживают обмен веществ и нервную систему.<br>
                    - Витамин A и бета-каротин полезны для зрения и иммунитета.<br>
                    - Содержит много калия, кальция, магния.<br>
                    <b>Состав зависит от сорта, зрелости и условий хранения.</b>
                </p>
                """)


            
            vitamins_layout.addWidget(vitamins_info)
            
            nutrition_tab = QWidget()
            nutrition_layout = QVBoxLayout(nutrition_tab)
            
            nutrition_info = QTextEdit()
            nutrition_info.setReadOnly(True)
            
            if fruit_type == 'apples':
                nutrition_info.setHtml("""
        <h3 style="color: #4CAF50; margin-top: 0;">Пищевая ценность яблока (100 г)</h3>
        <table style="width:100%; font-size:14px; margin-bottom:10px;">
            <tr><td><b>Калорийность</b></td><td>47–52 кКал</td></tr>
            <tr><td><b>Белки</b></td><td>0,3–0,4 г</td></tr>
            <tr><td><b>Жиры</b></td><td>0,2–0,4 г</td></tr>
            <tr><td><b>Углеводы</b></td><td>9,8–13,8 г</td></tr>
            <tr><td><b>Клетчатка</b></td><td>1,8–2,4 г</td></tr>
            <tr><td><b>Сахара</b></td><td>10,4 г</td></tr>
            <tr><td><b>Вода</b></td><td>85,6–86,3 г</td></tr>
        </table>
        <p style="font-size:13px; color:#555;">
            Почти вся энергия поступает из углеводов (до 95%).<br>
            Клетчатка и пектины способствуют пищеварению.<br>
            Холестерин и трансжиры отсутствуют.
        </p>
        """)
            elif fruit_type == 'bananas':
                nutrition_info.setHtml("""
        <h3 style="color: #4CAF50; margin-top: 0;">Пищевая ценность банана (100 г)</h3>
        <table style="width:100%; font-size:14px; margin-bottom:10px;">
            <tr><td><b>Калорийность</b></td><td>88–91 кКал</td></tr>
            <tr><td><b>Белки</b></td><td>1,1 г</td></tr>
            <tr><td><b>Жиры</b></td><td>0,3–0,33 г</td></tr>
            <tr><td><b>Углеводы</b></td><td>22,8 г</td></tr>
            <tr><td><b>Клетчатка</b></td><td>2,6–3 г</td></tr>
            <tr><td><b>Сахара</b></td><td>12,2 г</td></tr>
            <tr><td><b>Вода</b></td><td>74,9 г</td></tr>
        </table>
        <p style="font-size:13px; color:#555;">
            Основная часть калорий - из углеводов (около 93%).<br>
            Клетчатки чуть больше, чем в яблоке.<br>
            Холестерин и трансжиры отсутствуют.
        </p>
        """)
            elif fruit_type == 'carrots':
                nutrition_info.setHtml("""
                <h3 style="color: #4CAF50; margin-top: 0;">Пищевая ценность моркови (100 г)</h3>
                <table style="width:100%; font-size:14px; margin-bottom:10px;">
                    <tr><td><b>Калорийность</b></td><td>35–41 кКал</td></tr>
                    <tr><td><b>Белки</b></td><td>1,1 г</td></tr>
                    <tr><td><b>Жиры</b></td><td>0,1 г</td></tr>
                    <tr><td><b>Углеводы</b></td><td>6,9–9,6 г</td></tr>
                    <tr><td><b>Клетчатка</b></td><td>2,4–2,8 г</td></tr>
                    <tr><td><b>Сахара</b></td><td>4,7 г</td></tr>
                    <tr><td><b>Вода</b></td><td>88 г</td></tr>
                </table>
                <p style="font-size:13px; color:#555;">
                    Основная часть калорий - из углеводов.<br>
                    Много клетчатки, очень мало жира.<br>
                    Холестерин и трансжиры отсутствуют.
                </p>
                """)
            elif fruit_type == 'oranges':
                nutrition_info.setHtml("""
                <h3 style="color: #4CAF50; margin-top: 0;">Пищевая ценность апельсина (100 г)</h3>
                <table style="width:100%; font-size:14px; margin-bottom:10px;">
                    <tr><td><b>Калорийность</b></td><td>43 кКал</td></tr>
                    <tr><td><b>Белки</b></td><td>0,9 г</td></tr>
                    <tr><td><b>Жиры</b></td><td>0,2 г</td></tr>
                    <tr><td><b>Углеводы</b></td><td>8,3 г</td></tr>
                    <tr><td><b>Клетчатка</b></td><td>2,2 г</td></tr>
                    <tr><td><b>Сахара</b></td><td>8,2 г</td></tr>
                    <tr><td><b>Вода</b></td><td>86,8 г</td></tr>
                </table>
                <p style="font-size:13px; color:#555;">
                    Основная часть калорий - из углеводов.<br>
                    Высокое содержание витамина C и клетчатки.<br>
                    Холестерин и трансжиры отсутствуют.
                </p>
                """)


            
            nutrition_layout.addWidget(nutrition_info)
            
            recipes_tab = QWidget()
            recipes_layout = QVBoxLayout(recipes_tab)
            
            recipes_info = QTextEdit()
            recipes_info.setReadOnly(True)
            
            if fruit_type == 'apples':
                recipes_info.setHtml("""
                <h3 style="color: #4CAF50; margin-top: 0;">Рецепты с яблоками</h3>
                <h4 style="color: #ff9800; margin-top: 15px">1. Яблочный пирог</h4>
                <p style="margin: 5px 0"><span style="font-weight: bold; color: #2196F3">Ингредиенты:</span></p>
                <ul>
                    <li>6-7 яблок</li>
                    <li>200 г муки</li>
                    <li>150 г сливочного масла</li>
                    <li>150 г сахара</li>
                    <li>3 яйца</li>
                    <li>1 ч.л. разрыхлителя</li>
                    <li>Корица по вкусу</li>
                </ul>
                <p><span style="font-weight: bold; color: #2196F3">Приготовление:</span> Смешайте масло, сахар и яйца. Добавьте муку и разрыхлитель. Нарежьте яблоки, выложите на тесто, посыпьте корицей. Выпекайте 40-45 минут при 180C.</p>
                """)
            elif fruit_type == 'bananas':
                recipes_info.setHtml("""
                <h3 style="color: #4CAF50; margin-top: 0;">Рецепты с бананами</h3>
                <h4 style="color: #ff9800; margin-top: 15px">1. Банановый смузи</h4>
                <p style="margin: 5px 0"><span style="font-weight: bold; color: #2196F3">Ингредиенты:</span></p>
                <ul>
                    <li>2 спелых банана</li>
                    <li>1 стакан молока (можно использовать растительное)</li>
                    <li>2 столовые ложки мёда</li>
                    <li>Лёд (по желанию)</li>
                </ul>
                <p><span style="font-weight: bold; color: #2196F3">Приготовление:</span> Смешайте все ингредиенты в блендере до однородной массы. Подавайте сразу.</p>

                <h4 style="color: #ff9800; margin-top: 15px">2. Банановый хлеб</h4>
                <p style="margin: 5px 0"><span style="font-weight: bold; color: #2196F3">Ингредиенты:</span></p>
                <ul>
                    <li>3 спелых банана</li>
                    <li>1/3 стакана растопленного масла</li>
                    <li>1 яйцо</li>
                    <li>1 чайная ложка ванильного экстракта</li>
                    <li>1 чайная ложка разрыхлителя</li>
                    <li>1/2 чайной ложки соли</li>
                    <li>1.5 стакана муки</li>
                </ul>
                <p><span style="font-weight: bold; color: #2196F3">Приготовление:</span> Разогрейте духовку до 180°C. Разомните бананы, смешайте с маслом и яйцом. Добавьте сухие ингредиенты. Выпекайте в форме для хлеба 50-60 минут.</p>
                """)
            elif fruit_type == 'carrots':
                recipes_info.setHtml("""
                <h3 style="color: #4CAF50; margin-top: 0;">Рецепты с морковью</h3>
                <h4 style="color: #ff9800; margin-top: 15px">1. Морковный салат</h4>
                <p style="margin: 5px 0"><span style="font-weight: bold; color: #2196F3">Ингредиенты:</span></p>
                <ul>
                    <li>2-3 моркови</li>
                    <li>1 яблоко</li>
                    <li>1 ст. л. лимонного сока</li>
                    <li>1 ч. л. мёда</li>
                </ul>
                <p><span style="font-weight: bold; color: #2196F3">Приготовление:</span> Натереть морковь и яблоко на терке, добавить лимонный сок и мёд, перемешать.</p>
                <h4 style="color: #ff9800; margin-top: 15px">2. Морковные котлеты</h4>
                <p style="margin: 5px 0"><span style="font-weight: bold; color: #2196F3">Ингредиенты:</span></p>
                <ul>
                    <li>4 моркови</li>
                    <li>1 яйцо</li>
                    <li>2 ст. л. манки</li>
                    <li>Соль по вкусу</li>
                    <li>Масло для жарки</li>
                </ul>
                <p><span style="font-weight: bold; color: #2196F3">Приготовление:</span> Морковь натереть, смешать с яйцом и манкой, посолить. Сформировать котлеты, обжарить до золотистой корочки.</p>
                """)
            elif fruit_type == 'oranges':
                recipes_info.setHtml("""
                <h3 style="color: #4CAF50; margin-top: 0;">Рецепты с апельсинами</h3>
                <h4 style="color: #ff9800; margin-top: 15px">1. Апельсиновый смузи</h4>
                <p style="margin: 5px 0"><span style="font-weight: bold; color: #2196F3">Ингредиенты:</span></p>
                <ul>
                    <li>2 апельсина</li>
                    <li>1 банан</li>
                    <li>100 мл йогурта</li>
                    <li>1 ч. л. мёда</li>
                </ul>
                <p><span style="font-weight: bold; color: #2196F3">Приготовление:</span> Очистите апельсины и банан, взбейте в блендере с йогуртом и мёдом.</p>
                <h4 style="color: #ff9800; margin-top: 15px">2. Апельсиновый салат</h4>
                <p style="margin: 5px 0"><span style="font-weight: bold; color: #2196F3">Ингредиенты:</span></p>
                <ul>
                    <li>1 апельсин</li>
                    <li>1 яблоко</li>
                    <li>1 морковь</li>
                    <li>1 ч. л. лимонного сока</li>
                </ul>
                <p><span style="font-weight: bold; color: #2196F3">Приготовление:</span> Нарежьте все ингредиенты кубиками, заправьте лимонным соком.</p>
                """)


            
            recipes_layout.addWidget(recipes_info)
            
            tabs.addTab(vitamins_tab, "Витамины")
            tabs.addTab(nutrition_tab, "Пищевая ценность")
            tabs.addTab(recipes_tab, "Рецепты")
            
            layout.addWidget(tabs)
            
            buttons_layout = QHBoxLayout()

            add_to_journal_button = QPushButton("Добавить в журнал питания")
            add_to_journal_button.setStyleSheet("""
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
            """)
            add_to_journal_button.clicked.connect(lambda: self.add_fruit_to_journal(fruit, fruit_type))
            buttons_layout.addWidget(add_to_journal_button)
            

            close_button = QPushButton("Закрыть")
            close_button.clicked.connect(dialog.accept)
            buttons_layout.addWidget(close_button)

            layout.addLayout(buttons_layout)

            
            dialog.setLayout(layout)
            dialog.exec()
        except Exception as e:
            print(f"Ошибка: {e}")
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")

    
    def closeEvent(self, event):
        self.stop_detection()
        event.accept()
    def get_user_nutrition_summary(self):
        conn = sqlite3.connect('detections.db')
        cursor = conn.cursor()
        
        onedayago = datetime.now() - timedelta(hours=24)
        cursor.execute("SELECT object_type, COUNT(*) FROM detections WHERE user_id = ? AND timestamp > ? GROUP BY object_type", 
                    (self.user_id, onedayago.isoformat()))
        
        rows = cursor.fetchall()
        conn.close()
        
        summary = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0, "fiber": 0.0, "sugar": 0.0, "vitamins": {}}
        for vit in next(iter(NUTRITION_DATA.values()))["vitamins"].keys():
            summary["vitamins"][vit] = 0.0
        
        summary["fruits"] = {}
        
        for object_type, count in rows:
            summary["fruits"][object_type] = count
            
            if object_type in NUTRITION_DATA:
                data = NUTRITION_DATA[object_type]
                multiplier = count * data["weight"] / 100.0
                
                summary["calories"] += data["calories"] * multiplier
                summary["protein"] += data["protein"] * multiplier
                summary["fat"] += data["fat"] * multiplier
                summary["carbs"] += data["carbs"] * multiplier
                summary["fiber"] += data["fiber"] * multiplier
                summary["sugar"] += data["sugar"] * multiplier
                
                for vit, val in data["vitamins"].items():
                    summary["vitamins"][vit] += val * multiplier
        
        return summary
    def format_nutrition_summary(self, summary):
        lines = []
        lines.append(f"<b>Калории:</b> {summary['calories']:.1f} кКал")
        lines.append(f"<b>Белки:</b> {summary['protein']:.2f} г")
        lines.append(f"<b>Жиры:</b> {summary['fat']:.2f} г")
        lines.append(f"<b>Углеводы:</b> {summary['carbs']:.2f} г")
        lines.append(f"<b>Клетчатка:</b> {summary['fiber']:.2f} г")
        lines.append(f"<b>Сахар:</b> {summary['sugar']:.2f} г")
        lines.append("<br><b>Витамины:</b>")
        for vit, val in summary['vitamins'].items():
            lines.append(f"{vit}: {val:.2f}")
        return "<br>".join(lines)




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YOLOv5DetectionApp()
    window.show()
    sys.exit(app.exec())
