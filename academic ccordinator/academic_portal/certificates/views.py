from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Certificate
from applications.models import Application


def approve_certificates(request):
    """Show approved applications and allow approving or rejecting certificates.

    POST params:
      - application_id
      - action: 'approve' or 'reject'
    """
    applications = Application.objects.filter(status="approved")

    # allow selecting a particular application via GET ?app=<id>
    selected_app = None
    selected_id = request.GET.get('app')
    if selected_id:
        try:
            selected_app = applications.get(id=selected_id)
        except Application.DoesNotExist:
            selected_app = None

    if request.method == "POST":
        app_id = request.POST.get("application_id")
        action = request.POST.get("action")

        try:
            app = Application.objects.get(id=app_id)
        except Application.DoesNotExist:
            messages.error(request, "Application not found.")
            return redirect("approve_certificates")

        if action == 'approve':
            Certificate.objects.update_or_create(
                application=app,
                defaults={"approved": True}
            )
            messages.success(request, f"Certificate approved for {app.student_name}.")

        elif action == 'reject':
            # set application status to rejected and remove certificate if exists
            app.status = 'rejected'
            app.save()
            Certificate.objects.filter(application=app).delete()
            messages.success(request, f"Application for {app.student_name} rejected and certificate removed.")

        else:
            messages.error(request, "Invalid action.")

        # redirect back to the approval page and keep the same application selected
        return redirect(f"{request.path}?app={app_id}")

    # fetch certificate for selected app (if any)
    certificate = None
    if selected_app:
        certificate = Certificate.objects.filter(application=selected_app).first()

    return render(request, "certificates/approve.html", {
        "applications": applications,
        "selected_app": selected_app,
        "certificate": certificate,
    })

