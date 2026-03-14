from rest_framework import serializers
from ..academics.models import Enrollment
from ..accounts.models import CustomUser, Student, Instructor
from django.shortcuts import get_object_or_404
class CustomUserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    class Meta:
        model = CustomUser
        fields = ['id','email','username','first_name','last_name','password','confirm_password']
        read_only_fields = ['id',]
    def create(self, validated_data):
        password = validated_data.pop('password',None)
        confirm_password = validated_data.pop('confirm_password')
        if password != confirm_password:
            raise serializers.ValidationError("Passwords donot match!")
        
        user = CustomUser(**validated_data)
        
        if password:
            user.set_password(password)
        user.save()
        return user
    def update(self, instance, validated_data):
        password = validated_data.pop('password',None)
        confirm_password = validated_data.pop('confirm_password')
        if password != confirm_password:
            raise serializers.ValidationError("Passwords donot match!")
        
        instance = instance.objects.update(**validated_data)
        instance.set_password(password)
        instance.asve()

class StudentSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    class Meta:
        model = Student
        fields = '__all__'

    def create(self, validated_data):
        user_id = validated_data.get('user_id')
        user = get_object_or_404(Student, id=user_id)
        return Student.objects.create(user=user)
class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = '__all__'
        read_only_fields = ['id',]
