from rest_framework import status
from rest_framework.response import Response

from customers.constants import HOME_SCREEN_ACTIVE_ID
from customers.models.HomeScreen import CustomerHomescreen
from customers.serializers import HomeScreenSerializer


class HomeScreenService:

    def get_home_screen(self, request, ip):
        print("HPOME=------")

        # TODO here static id
        home_screen_obj = CustomerHomescreen.objects.get(id=HOME_SCREEN_ACTIVE_ID, is_active=True)
        serial = HomeScreenSerializer(home_screen_obj)
        return Response({'msg': 'Success', 'data':serial.data, 'status':1}, status=status.HTTP_200_OK)








