__all__ = [
    'LoginDialog',
]

from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLineEdit, QLabel, QPushButton, QMessageBox
import requests
from dotenv import load_dotenv
import os
import beeref.user_instance as user_instance

load_dotenv()

class User:
    def __init__(self, user_id):
        self.id = user_id

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user = None

        self.setWindowTitle('Login')

        self.layout = QVBoxLayout()

        self.email_label = QLabel('Email:')
        self.layout.addWidget(self.email_label)

        self.email_field = QLineEdit()
        self.layout.addWidget(self.email_field)

        self.password_label = QLabel('Password:')
        self.layout.addWidget(self.password_label)

        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.layout.addWidget(self.password_field)

        self.login_button = QPushButton('Login')
        self.login_button.clicked.connect(self.handle_login)
        self.layout.addWidget(self.login_button)

        self.setLayout(self.layout)

    def handle_login(self):
        email = self.email_field.text()
        password = self.password_field.text()
        api_key = os.getenv('FIREBASE_API_KEY')

        # Pass the email and password to Firebase
        response = requests.post(
            f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}',
            data={
                'email': email,
                'password': password,
                'returnSecureToken': True
            }
        )

        if response.status_code == 200:
            data = response.json()

            # id_token = data['idToken']  # The ID token of the logged in user
            user_uid = data['localId']  # The Firebase user ID of the logged in user
            # refresh_token = data['refreshToken']  # The refresh token of the logged in user

            # TODO: Store the ID token and refresh token somewhere safe
            # print(f'ID Token: {id_token}')
            # print(f'Refresh Token: {user_uid}')
            user_instance.user = User(user_uid)

            self.accept()
        else:
            # TODO: Handle login failure, show error message to user
            print('Login failed:', response.content)
            QMessageBox.warning(self, "Login failed", "Incorrect email or password.")
            self.reject()

        