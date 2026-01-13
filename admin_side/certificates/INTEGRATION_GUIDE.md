# Certificate App Integration Guide

This folder contains a plug-and-play Django app for generating certificates. Follow these steps to integrate it into another Django project.

## 1. Copy the Folder
Copy the entire `certificates` folder into the root directory of your target Django project (where `manage.py` lives).

## 2. Install Dependencies
Run the following command to install the required libraries for PDF generation and image processing:
```bash
pip install reportlab Pillow
```

## 3. Register the App
Add `'certificates'` to your `INSTALLED_APPS` list in `settings.py`:
```python
INSTALLED_APPS = [
    # ... other apps ...
    'certificates',
]
```

## 4. Configure URLs
Include the certificate URLs in your project's main `urls.py`:
```python
from django.urls import path, include

urlpatterns = [
    # ... other patterns ...
    path('', include('certificates.urls')),
]
```

## 5. User Model Requirements
This app assumes your `User` model has a `batch` field. 
- **If you are using the default User model:** You may need to create a profile model or extend AbstractUser.
- **If you have a custom User model:** Add the following field to it:
  ```python
  batch = models.CharField(max_length=10, blank=True, null=True, help_text='Batch year (e.g., 2024)')
  ```

## 6. Run Migrations
Create the necessary database tables:
```bash
python manage.py makemigrations certificates
python manage.py migrate
```

## 7. Media Configuration (Important!)
Ensure your project is configured to serve media files (uploaded templates).
In `settings.py`:
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```
In `urls.py`:
```python
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## 8. Populate Test Data (Optional)
To verify everything is working, run the included management command:
```bash
python manage.py populate_dummy_data
```

## 9. Access the Generator
Go to: `http://localhost:8000/generate/`

---
## Troubleshooting
- **Student Names Missing?** Check the template Y-coordinate. It should be usually around 300 (center of page).
- **Import Errors?** Make sure `certificates` is inside your project root.
