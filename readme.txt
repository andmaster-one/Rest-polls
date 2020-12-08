Do the following steps:
1. Create folder for virtual environment: mkdir virtual
2. Create virtual environment: python -m venv virtual
3. Go to virtual environment folder: cd virtual
4. Activate virtual environment: read from https://docs.python.org/3/tutorial/venv.html
5. Install requirements: pip install -r requirements.txt
6. Update setting.py and local_setting.py
7. Create migrations: python manage.py makemigrations
8. Make migrations: python manage.py migrate
9. Create superuser python manage.py createsuperuser
9. Run develop server: python manage.py runserver
10. Have a fun