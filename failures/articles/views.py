from django.shortcuts import render




from .models import Incident



def index(request):
    return render(
        request,
        "articles/index.html",
        {
            "incidents": Incident.objects.all(),
        },
    )
