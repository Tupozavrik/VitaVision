from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QSplashScreen
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property, QSize, QRect
from PySide6.QtGui import QColor, QPainter, QPainterPath, QFont, QPixmap, QPen

class NotificationDialog(QDialog):
    def __init__(self, parent=None, title="", message="", success=True):
        super().__init__(parent, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setFixedSize(400, 300)
        self.success = success
        self.opacity = 0.0
        
        # Для анимации появления
        self._opacity = 0.0
        
        # Настройка окна
        self.setWindowTitle(title)
        self.setWindowOpacity(1.0)  # Полностью непрозрачное окно
        # Отключаем прозрачность фона
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        # Создаем лейаут
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignCenter)
        
        # Главный текст (заголовок)
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.title_label.setStyleSheet(f"color: {'#4CAF50' if success else '#f44336'};")
        
        # Сообщение
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setFont(QFont("Arial", 12))
        self.message_label.setStyleSheet("color: #555555;")
        self.message_label.setWordWrap(True)
        
        # Кнопка закрытия - центрируем
        self.close_button = QPushButton("OK")
        self.close_button.setFixedSize(120, 40)
        self.close_button.setFont(QFont("Arial", 12))
        self.close_button.setCursor(Qt.PointingHandCursor)
        
        # Добавляем виджеты в лейаут
        layout.addWidget(self.title_label)
        layout.addWidget(self.message_label)
        
        # Центрируем кнопку с помощью отдельного лейаута
        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)
        
        # Настройка анимации
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.finished.connect(self.setup_close_timer)
        
        # Запуск анимации при показе
        QTimer.singleShot(100, self.animation.start)
    
    def get_opacity(self):
        return self._opacity
    
    def set_opacity(self, opacity):
        self._opacity = opacity
        self.setWindowOpacity(opacity)
    
    # Свойство для анимации прозрачности
    opacity = Property(float, get_opacity, set_opacity)
    
    def setup_close_timer(self):
        # Авто-закрытие через 3 секунды
        QTimer.singleShot(3000, self.start_close_animation)
    
    def start_close_animation(self):
        # Анимация закрытия
        self.close_animation = QPropertyAnimation(self, b"opacity")
        self.close_animation.setDuration(500)
        self.close_animation.setStartValue(1.0)
        self.close_animation.setEndValue(0.0)
        self.close_animation.setEasingCurve(QEasingCurve.InCubic)
        self.close_animation.finished.connect(self.close)
        self.close_animation.start()
    
    def paintEvent(self, event):
        # Кастомная отрисовка с закругленными углами
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Настройка цвета фона
        bg_color = QColor("#808080")
        
        # Создаем путь с закругленными углами
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 15, 15)
        
        # Рисуем фон
        painter.fillPath(path, bg_color)
        
        # Рисуем значок (галочка или крестик)
        painter.save()
        if self.success:
            # Рисуем зеленую галочку
            painter.setPen(QColor("#4CAF50"))
            painter.setBrush(QColor("#4CAF50"))
            
            # Круг
            center_x = self.width() // 2
            center_y = 60
            radius = 30
            painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
            
            painter.setPen(QColor("#FFFFFF"))
            painter.setBrush(QColor("#FFFFFF"))
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Рисуем галочку
            check_path = QPainterPath()
            check_path.moveTo(center_x - 15, center_y)
            check_path.lineTo(center_x - 5, center_y + 10)
            check_path.lineTo(center_x + 15, center_y - 10)

            painter.setPen(QPen(Qt.white, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawPath(check_path)
            
            # ДОБАВИТЬ КОД ДЛЯ ГАЛОЧКИ, ЕСЛИ БУДУ УСПЕВАТЬ!!!
             # ДОБАВИТЬ КОД ДЛЯ ГАЛОЧКИ, ЕСЛИ БУДУ УСПЕВАТЬ!!!
              # ДОБАВИТЬ КОД ДЛЯ ГАЛОЧКИ, ЕСЛИ БУДУ УСПЕВАТЬ!!!
               # ДОБАВИТЬ КОД ДЛЯ ГАЛОЧКИ, ЕСЛИ БУДУ УСПЕВАТЬ!!!
                # ДОБАВИТЬ КОД ДЛЯ ГАЛОЧКИ, ЕСЛИ БУДУ УСПЕВАТЬ!!!
                 # ДОБАВИТЬ КОД ДЛЯ ГАЛОЧКИ, ЕСЛИ БУДУ УСПЕВАТЬ!!!
                  # ДОБАВИТЬ КОД ДЛЯ ГАЛОЧКИ, ЕСЛИ БУДУ УСПЕВАТЬ!!!
                   # ДОБАВИТЬ КОД ДЛЯ ГАЛОЧКИ, ЕСЛИ БУДУ УСПЕВАТЬ!!!
                    # ДОБАВИТЬ КОД ДЛЯ ГАЛОЧКИ, ЕСЛИ БУДУ УСПЕВАТЬ!!!
                     # ДОБАВИТЬ КОД ДЛЯ ГАЛОЧКИ, ЕСЛИ БУДУ УСПЕВАТЬ!!!
                      # ДОБАВИТЬ КОД ДЛЯ ГАЛОЧКИ, ЕСЛИ БУДУ УСПЕВАТЬ!!!
                       # ДОБАВИТЬ КОД ДЛЯ ГАЛОЧКИ, ЕСЛИ БУДУ УСПЕВАТЬ!!!
                       
        else:
            # Рисуем красный крестик
            painter.setPen(QColor("#f44336"))
            painter.setBrush(QColor("#f44336"))
            
            # Круг 
            center_x = self.width() // 2
            center_y = 60  # Было 80, сделали 60, чтобы поднять выше
            radius = 30
            painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
            
            # Крестик (белый)
            painter.setPen(QColor("#FFFFFF"))
            painter.setBrush(QColor("#FFFFFF"))
            
            # Рисуем крестик
            cross_size = 15
            painter.drawLine(center_x - cross_size, center_y - cross_size, 
                            center_x + cross_size, center_y + cross_size)
            painter.drawLine(center_x + cross_size, center_y - cross_size, 
                            center_x - cross_size, center_y + cross_size)
        
        painter.restore()


class AnimatedSplashScreen(QSplashScreen):
    def __init__(self, username):
        pixmap = QPixmap(400, 400)
        pixmap.fill(Qt.transparent)
        super().__init__(pixmap)
        
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.progress = 0
        self.username = username
        self.loading_texts = ["Подготовка компонентов", 
                              "Загрузка модулей распознавания", 
                              "Калибровка камеры", 
                              "Инициализация нейросети", 
                              "Запуск VitaVision"]
        self.current_text_index = 0
        self.dots_count = 0
        self.dot_timer = 0
        self.logo_opacity = 0
        self.logo_increasing = True
        
        # Таймер для обновления анимации и прогресса
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(80)  # Обновление каждые 80 мс
    
    def update_progress(self):
        # Обновляем прогресс
        self.progress += 1
        
        # Обновляем счетчик точек (для анимации "...")
        self.dot_timer += 1
        if self.dot_timer >= 5:
            self.dot_timer = 0
            self.dots_count = (self.dots_count + 1) % 4
        
        # Обновляем текст загрузки
        if self.progress % 20 == 0 and self.progress > 0:
            self.current_text_index = min(self.current_text_index + 1, len(self.loading_texts) - 1)
        
        # Пульсация логотипа
        if self.logo_increasing:
            self.logo_opacity += 5
            if self.logo_opacity >= 255:
                self.logo_opacity = 255
                self.logo_increasing = False
        else:
            self.logo_opacity -= 5
            if self.logo_opacity <= 100:
                self.logo_opacity = 100
                self.logo_increasing = True
        
        # Обновляем изображение
        self.repaint()
        
        # Когда достигнем 100%, останавливаем таймер
        if self.progress >= 100:
            self.timer.stop()
            QTimer.singleShot(500, self.finish_splash)
    
    def finish_splash(self):
        # Сигнализируем о завершении загрузки
        self.close()
    
    def drawContents(self, painter):
        # Фон с закругленными углами
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Создаем путь для закругленного прямоугольника
        background_path = QPainterPath()
        background_path.addRoundedRect(QRect(0, 0, self.width(), self.height()), 20, 20)
        
        # Рисуем фон
        painter.fillPath(background_path, QColor(255, 255, 255, 230))
        
        # Рисуем логотип
        painter.save()
        logo_size = 100
        logo_x = (self.width() - logo_size) // 2
        logo_y = 80
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(76, 175, 80, self.logo_opacity))  # Зеленый логотип
        painter.drawEllipse(logo_x, logo_y, logo_size, logo_size)
        
        # Рисуем букву V внутри круга (для VitaVision)
        painter.setPen(QPen(QColor(255, 255, 255), 6))
        painter.drawLine(logo_x + 35, logo_y + 70, logo_x + 50, logo_y + 30)
        painter.drawLine(logo_x + 50, logo_y + 30, logo_x + 65, logo_y + 70)
        painter.restore()
        
        # Рисуем приветствие пользователя
        painter.setPen(QColor(80, 80, 80))
        painter.setFont(QFont("Arial", 14, QFont.Bold))
        welcome_text = f"Добро пожаловать, {self.username}!"
        painter.drawText(0, logo_y + logo_size + 30, self.width(), 30, 
                         Qt.AlignCenter, welcome_text)
        
        # Рисуем текст загрузки
        painter.setPen(QColor(120, 120, 120))
        painter.setFont(QFont("Arial", 10))
        loading_text = self.loading_texts[self.current_text_index] + "." * self.dots_count
        painter.drawText(0, logo_y + logo_size + 70, self.width(), 20, 
                         Qt.AlignCenter, loading_text)
        
        # Рисуем прогресс-бар
        bar_width = 300
        bar_height = 6
        bar_x = (self.width() - bar_width) // 2
        bar_y = logo_y + logo_size + 100
        
        # Фон прогресс-бара
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(230, 230, 230))
        painter.drawRoundedRect(bar_x, bar_y, bar_width, bar_height, 3, 3)
        
        # Заполненная часть прогресс-бара
        filled_width = int(bar_width * self.progress / 100)
        painter.setBrush(QColor(76, 175, 80))  # Зеленый цвет
        painter.drawRoundedRect(bar_x, bar_y, filled_width, bar_height, 3, 3)
        
        # Процент загрузки
        painter.setPen(QColor(76, 175, 80))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        percent_text = f"{self.progress}%"
        painter.drawText(0, bar_y + 20, self.width(), 20, Qt.AlignCenter, percent_text)
