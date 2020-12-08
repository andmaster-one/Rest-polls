from rest_framework import status
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Poll, Question, Answer, UserAnswers
from .permissions import IsAdminOrReadOnly
from .serializers import PollSerializer, QuestionSerializer, ProcessPollSerializer
from rest_framework.serializers import ValidationError


class PollList(APIView):
    permission_classes = (IsAdminOrReadOnly,)
        
    def get(self, request, format=None):
        polls = Poll.objects.all()
        serializer = PollSerializer(polls, many=True, context={'request': request})
        data = serializer.data
        return Response(data)
    
    def post(self, request, format=None):
        serializer = PollSerializer(data=request.data, is_detailed=True, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            poll = serializer.save()
            serializer.instance = poll
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class PollDetail(APIView):
    permission_classes = (IsAdminOrReadOnly,)

    def get_object(self, pk):
        try:
            return Poll.objects.get(pk=pk)
        except Poll.DoesNotExist:
            raise ValidationError({'poll':'Poll questions does not exist'})
         
    def get(self, request, pk, format=None):
        poll = self.get_object(pk)
        serializer = PollSerializer(poll, is_detailed=True, context={'request': request})
        return Response(serializer.data)

    def delete(self, request, pk, format=None):
        poll = self.get_object(pk)
        poll.delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 

    def put(self, request, pk, format=None):  
        poll = self.get_object(pk)  
        serializer = PollSerializer(poll, is_detailed=True, data=request.data, context={'request': request, 'is_update':True})
        if serializer.is_valid(raise_exception=True):
            updated_instance = serializer.save()
            return Response(serializer.initial_data)
  

class Process(APIView):

    def get_user(self, user_pk=None):
        try:
            return UserAnswers.objects.get(pk=user_pk)
        except UserAnswers.DoesNotExist:
            raise ValidationError({'user': 'User does not exist'}) 

    def post(self, request, user_pk=None, format=None):
        user = None
        if user_pk is not None:
            user = self.get_user(user_pk=user_pk) 
        serializer = ProcessPollSerializer(data=request.data, context={'request': request, 'view': self})
        if serializer.is_valid(raise_exception=True):         
            user = serializer.save(user=user)           
            data = {'user_id' : user.pk, 'data' : serializer.data}
            return Response(data, status=status.HTTP_201_CREATED)
  
    def get(self, request, user_pk= None, format=None):
        if user_pk is not None:
            user = self.get_user(user_pk=user_pk)
        else:
            raise ValidationError({'url': '/process/ url does not support get method'}) 
        data = user.user_data
        return Response(data)
