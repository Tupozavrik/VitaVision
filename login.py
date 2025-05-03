from PySide6.QtWidgets import (QMainWindow, QWidget, QLabel, QPushButton, 
                              QVBoxLayout, QHBoxLayout, QLineEdit, QFormLayout,
                              QMessageBox, QDialog, QCheckBox)
from PySide6.QtGui import QFont, QPixmap, QIcon
from PySide6.QtCore import Qt, QSize

from database import UserDatabase
from animation import NotificationDialog, AnimatedSplashScreen
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect

class RegistrationDialog(QDialog):
    """для нью юзеров"""
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Регистрация нового пользователя")
        self.setMinimumWidth(400)
        self.setup_ui()
        
    def setup_ui(self):
        """настройка интерфейса"""
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Введите имя пользователя")
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Введите email (необязательно)")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Подтвердите пароль")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        
        form_layout.addRow("Имя пользователя:", self.username_input)
        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("Пароль:", self.password_input)
        form_layout.addRow("Подтверждение пароля:", self.confirm_password_input)
        
        layout.addLayout(form_layout)
        
        self.show_password_cb = QCheckBox("Показать пароль")
        self.show_password_cb.toggled.connect(self.toggle_password_visibility)
        layout.addWidget(self.show_password_cb)
        
        button_layout = QHBoxLayout()
        self.register_btn = QPushButton("Зарегистрироваться")
        self.register_btn.clicked.connect(self.register_user)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.register_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def toggle_password_visibility(self, show):
        """Переключает видимость пароля"""
        if show:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.confirm_password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.confirm_password_input.setEchoMode(QLineEdit.Password)
        
    def register_user(self):
        """Обрабатывает регистрацию пользователя"""
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        if not username:
            QMessageBox.warning(self, "Ошибка", "Имя пользователя не может быть пустым")
            return
            
        if not password:
            QMessageBox.warning(self, "Ошибка", "Пароль не может быть пустым")
            return
            
        if password != confirm_password:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
            return
        
        if email and not email.strip():
            email = None  
            
        result = self.db.add_user(username, password, email)
        
        if result['success']:
            QMessageBox.information(self, "Успех", "Пользователь успешно зарегистрирован!")
            self.accept()  
        else:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при регистрации: {result['error']}")


class LoginWindow(QMainWindow):
    """Главное окно"""
    def __init__(self):
        super().__init__()
        self.db = UserDatabase()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("VitaVision - Авторизация")
        self.setMinimumSize(500, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        header_label = QLabel("VitaVision")
        header_label.setFont(QFont("Arial", 24, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("color: #4CAF50;")
        main_layout.addWidget(header_label)
        
        subheader_label = QLabel("Система распознавания продуктов")
        subheader_label.setFont(QFont("Arial", 14))
        subheader_label.setAlignment(Qt.AlignCenter)
        subheader_label.setStyleSheet("color: #555555;")
        main_layout.addWidget(subheader_label)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(50, 20, 50, 20)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Введите имя пользователя")
        self.username_input.setMinimumHeight(40)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        
        form_layout.addRow("Имя пользователя:", self.username_input)
        form_layout.addRow("Пароль:", self.password_input)
        
        main_layout.addLayout(form_layout)
        
        self.show_password_cb = QCheckBox("Показать пароль")
        self.show_password_cb.toggled.connect(self.toggle_password_visibility)
        main_layout.addWidget(self.show_password_cb)
        
        self.remember_me_cb = QCheckBox("Запомнить меня")
        self.remember_me_cb.setStyleSheet("color: #555555;")
        main_layout.addWidget(self.remember_me_cb)
        
        button_layout = QHBoxLayout()
        
        self.login_btn = QPushButton("Войти")
        self.login_btn.setMinimumSize(120, 45)
        self.login_btn.clicked.connect(self.login)
        
        self.register_btn = QPushButton("Регистрация")
        self.register_btn.setMinimumSize(120, 45)
        self.register_btn.clicked.connect(self.open_registration)
        
        button_layout.addWidget(self.login_btn)
        button_layout.addWidget(self.register_btn)
        
        main_layout.addLayout(button_layout)
        
        self.apply_styles()
        
    def apply_styles(self):
        """Применяет стили к окну авторизации"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            QLabel {
                color: #333333;
            }
            
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
            
            QLineEdit:focus {
                border: 1px solid #4CAF50;
            }
            
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
            }
            
            QPushButton:hover {
                background-color: #45a049;
            }
            
            QPushButton#register_btn {
                background-color: #2196F3;
            }
            
            QPushButton#register_btn:hover {
                background-color: #1e88e5;
            }
            
            QCheckBox {
                color: #555555;
            }
        """)
        
    def toggle_password_visibility(self, show):
        """визибилити пароля (я спрятался хаха))))"""
        if show:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
    
    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            # Неуспешная авторизация 
            notification = NotificationDialog(
                self, 
                "Ошибка авторизации", 
                "Пожалуйста, введите имя пользователя и пароль",
                success=False
            )
            notification.exec()
            return
        
        result = self.db.authenticate_user(username, password)
        
        if result['success']:
            """ # раскомментить если буду рисовать нормальную галочку
            notification = NotificationDialog( 
                self, 
                "Успешная авторизация", 
                f"Добро пожаловать, {username}!",
                success=True
            )
            notification.exec()
            """
            self.sound = QSoundEffect()
            sound_path = "D:/hakaton/succes1.wav" 
            self.sound.setSource(QUrl.fromLocalFile(sound_path))
            self.sound.setVolume(1.0)
            self.sound.play() 
            self.hide()
            
            # Если выбрана опция "Запомнить меня", сохраняем токен
            if self.remember_me_cb.isChecked():
                try:
                    # Генерим токен
                    token = self.db.generate_remember_token(result['user_id'])
                    
                    # Сохраняем токен в файл
                    with open('remember_token.dat', 'w') as f:
                        f.write(token)
                except Exception as e:
                    print(f"Ошибка при сохранении токена: {e}")
            
            splash = AnimatedSplashScreen(username)
            splash.show()
            
            from main_app import YOLOv5DetectionApp
            self.main_app = YOLOv5DetectionApp(user_id=result['user_id'], username=username)
            
            def on_splash_finished():
                self.main_app.show()
                self.hide()
            
            splash.close = lambda: [super(AnimatedSplashScreen, splash).close(), on_splash_finished()]
        else:
            notification = NotificationDialog(
                self, 
                "Ошибка авторизации", 
                result['error'],
                success=False
            )
            notification.exec()

    
    def open_registration(self):
        """Открывает диалог регистрации"""
        dialog = RegistrationDialog(self, self.db)
        dialog.exec()
    
    def open_main_app(self, user_id, username):
        """Открывает основное приложение"""
        from main_app import YOLOv5DetectionApp
        
        self.main_app = YOLOv5DetectionApp(user_id=user_id, username=username)
        self.main_app.show()
        self.hide()  
