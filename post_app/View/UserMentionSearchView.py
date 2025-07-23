from rest_framework import generics, permissions
from user_app.models import UserModel
from user_app.Serializer.UserSerializer import UserMentionSerializer
from django.db.models import Q

class UserMentionSearchView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]  # or AllowAny if you want
    serializer_class = UserMentionSerializer

    def get_queryset(self):
        query = self.request.query_params.get("query", "").lstrip("@")
        return UserModel.objects.filter(
                            Q(username__istartswith=query) |
                            Q(first_name__istartswith=query) |
                            Q(last_name__istartswith=query)
                        )[:10]
