from django.shortcuts import render, redirect
from .models import Program
from .forms import ProgramForm


def manage_programs(request):
    # list and create programs
    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('programs:manage_programs')
    else:
        form = ProgramForm()

    programs = Program.objects.all()
    return render(request, "programs/manage.html", {"programs": programs, "form": form})

