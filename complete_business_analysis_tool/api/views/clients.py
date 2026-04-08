"""API views for the clients application."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from complete_business_analysis_tool.clients.forms import ClientForm


class ClientCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        form = ClientForm(request.data)
        if form.is_valid():
            client = form.save()
            return Response(
                {"id": str(client.pk), "text": str(client)},
                status=status.HTTP_201_CREATED,
            )
        return Response({"errors": form.errors}, status=status.HTTP_400_BAD_REQUEST)
