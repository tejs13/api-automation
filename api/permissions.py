from rest_framework import permissions



class ApiPermissionCheck(permissions.BasePermission):
    message = "Access Denied!, Valid Permission is required from Admin."

    READ_METHODS = ["GET", "OPTIONS"]
    WRITE_METHODS = ["OPTIONS", "PUT", "POST", "DELETE", "PATCH"]

    def has_permission(self, request, view):
        user_groups = request.user.groups.all()
        user_groups = [g.name for g in user_groups]
        print(" in API PERMISSIOn CHECk  --------------")
        print(view.__dict__)
        print(request.user, request.method, user_groups, '\n\n\n\n\n', view.__class__.__name__)
        if request.method in self.READ_METHODS and "read_"+ str(view.__class__.__name__).lower() in user_groups:
            return True
        else:
            return False

    def has_object_permission(self, request, view, obj):
        """
        custom logic here, project based
        """
        print("  ---   Object Level permission called")
        print(obj, view, request)
