import sys
import os
from PySide6.QtWidgets import QApplication
from login import LoginWindow, NotificationDialog
from database import UserDatabase
from main_app import YOLOv5DetectionApp
from animation import AnimatedSplashScreen

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    token_file = 'remember_token.dat'
    
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r') as f:
                token = f.read().strip()
            
            db = UserDatabase()
            result = db.verify_remember_token(token)
            
            if result['success']:
                splash = AnimatedSplashScreen(result['username'])
                splash.show()
                
                main_app = YOLOv5DetectionApp(user_id=result['user_id'], username=result['username'])
                
                def on_splash_finished():
                    main_app.show()
                splash.close = lambda: [super(AnimatedSplashScreen, splash).close(), on_splash_finished()]
            else:
                login_window = LoginWindow()
                login_window.show()
        except Exception as e:
            print(f"Ошибка при проверке токена: {e}")
            login_window = LoginWindow()
            login_window.show()
    else:
        login_window = LoginWindow()
        login_window.show()
    
    sys.exit(app.exec())
