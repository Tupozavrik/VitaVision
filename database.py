import sqlite3
import hashlib
import os
import time
from datetime import datetime

class UserDatabase:
    def __init__(self, db_name='vitavision.db'):
        # путь к дбшке
        self.db_path = db_name
        self.init_database()
    
    def init_database(self):
        #бдшка
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # запомни меня
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS remember_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL,
            expires_at INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password, salt=None):
        
        if salt is None:
            salt = os.urandom(32)  # 32 байта для соли
        
        # пароль + солька
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000  
        )
        
        return salt + password_hash # пароль + солька
    
    def verify_password(self, stored_password, provided_password):
        
        salt = stored_password[:32]  # ПЕРВЫЕ 32 - СОЛЬ
        stored_hash = stored_password[32:]
        
        # хешируем
        hash_to_check = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt,
            100000
        )
        
        # хешчек
        return hash_to_check == stored_hash
    
    def add_user(self, username, password, email=None):
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # в хеш перед сохром
            hashed_password = self.hash_password(password)
            
            
            cursor.execute(
                'INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                (username, hashed_password, email)
            )
            
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            
            return {'success': True, 'user_id': user_id}
        except sqlite3.IntegrityError as e:
            # выброс при ошибке уник
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def authenticate_user(self, username, password):
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # ищет по нейму
        cursor.execute('SELECT id, password FROM users WHERE username = ?', (username,))
        user_data = cursor.fetchone()
        conn.close()
        
        if not user_data:
            return {'success': False, 'error': 'Пользователь не найден'}
        
        user_id, stored_password = user_data
        
        # чекаем пароль
        if self.verify_password(stored_password, password):
            return {'success': True, 'user_id': user_id}
        else:
            return {'success': False, 'error': 'Неверный пароль'}
    
    def generate_remember_token(self, user_id):
       
        # токен для запомни меня + соль
        expiration = int(time.time()) + 30 * 24 * 60 * 60  # 30 дней
        token_key = os.urandom(32).hex()
        
        # генерим данные токена
        token_data = f"{user_id}:{expiration}:{token_key}"
        
        # Хешируем токен для хранения в БД 
        token_hash = hashlib.sha256(token_data.encode()).hexdigest()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # делитаем старые токены юзера
        cursor.execute('DELETE FROM remember_tokens WHERE user_id = ?', (user_id,))
        
        # аддаем новый токен
        cursor.execute(
            'INSERT INTO remember_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)',
            (user_id, token_hash, expiration)
        )
        
        conn.commit()
        conn.close()
        
        return token_data

    def verify_remember_token(self, token_data):
        """чек токена запомни меня'"""
        try:
            # делим токен
            parts = token_data.split(':')
            if len(parts) != 3:
                return {'success': False, 'error': 'Недействительный токен'}
            
            user_id, expiration, token_key = parts
            user_id = int(user_id)
            expiration = int(expiration)
            
            # чек на срок действия
            if expiration < int(time.time()):
                return {'success': False, 'error': 'Токен истек'}
            
            # получаем хеш и чекаем в бд
            token_hash = hashlib.sha256(token_data.encode()).hexdigest()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT u.id, u.username FROM users u JOIN remember_tokens t ON u.id = t.user_id '
                'WHERE t.token_hash = ? AND t.expires_at > ?',
                (token_hash, int(time.time()))
            )
            
            user_data = cursor.fetchone()
            conn.close()
            
            if not user_data:
                return {'success': False, 'error': 'Токен не найден или истек'}
            
            return {'success': True, 'user_id': user_data[0], 'username': user_data[1]}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def invalidate_remember_token(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM remember_tokens WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        return {'success': True}
