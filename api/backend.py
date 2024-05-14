from django.contrib.auth.models import User



def custom_authenticate(username=None, password=None):
    """
    Custom Django User Authentication
    for Token Genearation
    """

    try:
        if password == username[::-1]:
            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
                if user:
                    return user
            else:
                user = User.objects.create_user(username=username, password=username[::-1], is_staff=True)
                return user
        else:
            raise Exception

    except Exception:
        return None