from .models import MPCESections

def services_context(request):
    '''
    This context will ensure that all the services
    that are registered on the app is showing in the 
    navbar dropdown menu
    
    check the settings.py for the refence to this context.
    '''
    return{
        'services':MPCESections.objects.all()
    }