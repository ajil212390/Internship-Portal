"""
Management command to populate database with dummy data for testing certificate generation
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from institutions.models import Institution
from certificates.models import CertificateTemplate
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with dummy institutions, students, and certificate templates'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting to populate dummy data...'))

        # Create Institutions
        institutions_data = [
            {
                'name': 'MIT College of Engineering',
                'location': 'Pune, Maharashtra',
                'address': 'Paud Road, Kothrud, Pune - 411038',
                'phone': '020-25431879',
                'email': 'info@mitcoe.edu.in',
                'principal_name': 'Dr. Rajesh Kumar',
                'principal_email': 'principal@mitcoe.edu.in'
            },
            {
                'name': 'COEP Technological University',
                'location': 'Pune, Maharashtra',
                'address': 'Wellesley Road, Shivajinagar, Pune - 411005',
                'phone': '020-25507000',
                'email': 'info@coep.ac.in',
                'principal_name': 'Dr. Anil Sahasrabudhe',
                'principal_email': 'principal@coep.ac.in'
            },
            {
                'name': 'VIT Pune',
                'location': 'Pune, Maharashtra',
                'address': 'Survey No. 3/4, Kondhwa, Pune - 411048',
                'phone': '020-24265714',
                'email': 'info@vit.edu',
                'principal_name': 'Dr. Madhuri Patil',
                'principal_email': 'principal@vit.edu'
            },
        ]

        institutions = []
        for inst_data in institutions_data:
            institution, created = Institution.objects.get_or_create(
                name=inst_data['name'],
                defaults=inst_data
            )
            institutions.append(institution)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created institution: {institution.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'○ Institution already exists: {institution.name}'))

        # Create Students
        students_data = [
            # MIT College
            {'username': 'amit_sharma', 'first_name': 'Amit', 'last_name': 'Sharma', 'email': 'amit.sharma@student.edu', 'institution': institutions[0]},
            {'username': 'priya_patel', 'first_name': 'Priya', 'last_name': 'Patel', 'email': 'priya.patel@student.edu', 'institution': institutions[0]},
            {'username': 'rahul_verma', 'first_name': 'Rahul', 'last_name': 'Verma', 'email': 'rahul.verma@student.edu', 'institution': institutions[0]},
            {'username': 'sneha_desai', 'first_name': 'Sneha', 'last_name': 'Desai', 'email': 'sneha.desai@student.edu', 'institution': institutions[0]},
            
            {'username': 'vikram_singh', 'first_name': 'Vikram', 'last_name': 'Singh', 'email': 'vikram.singh@student.edu', 'institution': institutions[0]},
            {'username': 'anjali_mehta', 'first_name': 'Anjali', 'last_name': 'Mehta', 'email': 'anjali.mehta@student.edu', 'institution': institutions[0]},
            {'username': 'karan_joshi', 'first_name': 'Karan', 'last_name': 'Joshi', 'email': 'karan.joshi@student.edu', 'institution': institutions[0]},
            
            # COEP
            {'username': 'neha_kulkarni', 'first_name': 'Neha', 'last_name': 'Kulkarni', 'email': 'neha.kulkarni@coep.edu', 'institution': institutions[1]},
            {'username': 'rohan_jadhav', 'first_name': 'Rohan', 'last_name': 'Jadhav', 'email': 'rohan.jadhav@coep.edu', 'institution': institutions[1]},
            {'username': 'pooja_rane', 'first_name': 'Pooja', 'last_name': 'Rane', 'email': 'pooja.rane@coep.edu', 'institution': institutions[1]},
            
            {'username': 'aditya_bhosale', 'first_name': 'Aditya', 'last_name': 'Bhosale', 'email': 'aditya.bhosale@coep.edu', 'institution': institutions[1]},
            {'username': 'kavya_shinde', 'first_name': 'Kavya', 'last_name': 'Shinde', 'email': 'kavya.shinde@coep.edu', 'institution': institutions[1]},
            
            # VIT
            {'username': 'siddharth_naik', 'first_name': 'Siddharth', 'last_name': 'Naik', 'email': 'siddharth.naik@vit.edu', 'institution': institutions[2]},
            {'username': 'ishita_sawant', 'first_name': 'Ishita', 'last_name': 'Sawant', 'email': 'ishita.sawant@vit.edu', 'institution': institutions[2]},
            {'username': 'arjun_pawar', 'first_name': 'Arjun', 'last_name': 'Pawar', 'email': 'arjun.pawar@vit.edu', 'institution': institutions[2]},
            
            {'username': 'divya_kamble', 'first_name': 'Divya', 'last_name': 'Kamble', 'email': 'divya.kamble@vit.edu', 'institution': institutions[2]},
            {'username': 'harsh_gaikwad', 'first_name': 'Harsh', 'last_name': 'Gaikwad', 'email': 'harsh.gaikwad@vit.edu', 'institution': institutions[2]},
        ]

        for student_data in students_data:
            student, created = User.objects.get_or_create(
                username=student_data['username'],
                defaults={
                    'first_name': student_data['first_name'],
                    'last_name': student_data['last_name'],
                    'email': student_data['email'],
                    'institution': student_data['institution'],
                    'role': 'STUDENT',
                    'is_active': True
                }
            )
            if created:
                student.set_password('password123')  # Default password
                student.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Created student: {student.get_full_name()}'))
            else:
                self.stdout.write(self.style.WARNING(f'○ Student already exists: {student.username}'))

        # Create a blank certificate template
        self.stdout.write(self.style.SUCCESS('\nCreating blank certificate template...'))
        
        # Create media directories if they don't exist
        cert_template_dir = os.path.join(settings.MEDIA_ROOT, 'cert_templates')
        os.makedirs(cert_template_dir, exist_ok=True)
        
        # Create a blank certificate image (A4 landscape size)
        width, height = 2480, 1754  # A4 landscape at 300 DPI
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add a simple border and text
        border_color = (41, 128, 185)  # Blue
        draw.rectangle([50, 50, width-50, height-50], outline=border_color, width=10)
        draw.rectangle([70, 70, width-70, height-70], outline=border_color, width=3)
        
        # Add "CERTIFICATE OF COMPLETION" text at top
        try:
            # Try to use a nice font if available
            title_font = ImageFont.truetype("arial.ttf", 80)
            subtitle_font = ImageFont.truetype("arial.ttf", 40)
        except:
            # Fallback to default font
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        title_text = "CERTIFICATE OF COMPLETION"
        # Get text bounding box for centering
        bbox = draw.textbbox((0, 0), title_text, font=title_font)
        text_width = bbox[2] - bbox[0]
        title_x = (width - text_width) // 2
        draw.text((title_x, 200), title_text, fill=border_color, font=title_font)
        
        # Add placeholder text
        subtitle_text = "This is to certify that"
        bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
        text_width = bbox[2] - bbox[0]
        subtitle_x = (width - text_width) // 2
        draw.text((subtitle_x, 400), subtitle_text, fill=(100, 100, 100), font=subtitle_font)
        
        # Note: Student name will be added at coordinates (1240, 600) - center of the page
        name_note = "[Student Name will appear here]"
        bbox = draw.textbbox((0, 0), name_note, font=subtitle_font)
        text_width = bbox[2] - bbox[0]
        note_x = (width - text_width) // 2
        draw.text((note_x, 650), name_note, fill=(150, 150, 150), font=subtitle_font)
        
        completion_text = "has successfully completed the internship program"
        bbox = draw.textbbox((0, 0), completion_text, font=subtitle_font)
        text_width = bbox[2] - bbox[0]
        completion_x = (width - text_width) // 2
        draw.text((completion_x, 900), completion_text, fill=(100, 100, 100), font=subtitle_font)
        
        # Save the image
        template_path = os.path.join(cert_template_dir, 'blank_certificate.png')
        img.save(template_path)
        
        # Create the template record
        template, created = CertificateTemplate.objects.get_or_create(
            name='Default Blank Certificate',
            defaults={
                'background_image': 'cert_templates/blank_certificate.png',
                'name_x_axis': 421,  # Center of A4 landscape (842 / 2)
                'name_y_axis': 300,  # Center of A4 landscape (595 / 2)
                'font_size': 60
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created certificate template: {template.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'○ Certificate template already exists: {template.name}'))
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Dummy data population completed!'))
        self.stdout.write(self.style.SUCCESS(f'Total Institutions: {Institution.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'Total Students: {User.objects.filter(role="STUDENT").count()}'))
        self.stdout.write(self.style.SUCCESS(f'Total Certificate Templates: {CertificateTemplate.objects.count()}'))
        self.stdout.write(self.style.SUCCESS('='*50))
