from rest_framework import serializers
from user_app.models import ProfileModel

class CustomerSendOtpSerializer(serializers.ModelSerializer):
    phone_no = serializers.SerializerMethodField()

    class Meta:
        model = ProfileModel
        fields = ('id', 'phone_no','otp', 'otp_requested_at')
        read_only_fields = fields

    def get_phone_no(self, obj):
        if obj.mobile_no:
            return str(obj.mobile_no)
        return None