@echo OFF
echo --- STEP 1: DELETING OLD ENVIRONMENT ---
deactivate
rmdir /s /q venv
rmdir /s /q staticfiles
rmdir /s /q media
FOR /D /R . %%G in (__pycache__) DO (rmdir /s /q "%%G")

echo.
echo --- STEP 2: CREATING NEW ENVIRONMENT ---
python -m venv venv
call .\venv\Scripts\activate.bat

echo.
echo --- STEP 3: INSTALLING PACKAGES ---
pip install -r requirements.txt

echo.
echo --- STEP 4: RESETTING DATABASE AND MIGRATIONS ---
REM You will need to enter your PostgreSQL password for this step
psql -U postgres -c "DROP DATABASE IF EXISTS geosmartdb;"
psql -U postgres -c "CREATE DATABASE geosmartdb;"
psql -U postgres -d geosmartdb -c "CREATE EXTENSION postgis;"
del /s /q "core\migrations\*.py"
echo. > "core\migrations\__init__.py"
python manage.py makemigrations
python manage.py migrate

echo.
echo --- STEP 5: CREATING SUPERUSER ---
echo Please create your superuser now.
python manage.py createsuperuser

echo.
echo --- STEP 6: COLLECTING STATIC FILES ---
python manage.py collectstatic --noinput

echo.
echo --- SETUP COMPLETE! ---
echo You can now run the server with: python manage.py runserver