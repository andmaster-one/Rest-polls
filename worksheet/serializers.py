from rest_framework import serializers
from .models import Poll, Question, Answer, UserAnswers
from rest_framework.serializers import ValidationError
from datetime import datetime

class AnswerListSerializer(serializers.ListSerializer):

    def update(self, instance, validated_data, pk):
        ret = []
        answers_qs_mapping = {answer['answer_name']: answer for answer in validated_data}
        instance_qs_answers_mapping ={item.answer_name: item for item in instance}
        # Perform update or create.      
        for answer_name, answer in answers_qs_mapping.items():
            instance_qs_answer = instance_qs_answers_mapping.get(answer_name, None)
           
            if instance_qs_answer is not None:                
                ret.append(self.child.update(instance_qs_answer, answer))
            else:
                answer.update({'question_id': pk})
                ret.append(self.child.create(answer))
        # Perform deletions.
        for instance_qs_answer_name, instance_answer in instance_qs_answers_mapping.items():
            if instance_qs_answer_name not in answers_qs_mapping:
                instance_answer.delete()            
        return ret  


class AnswerSerializer(serializers.ModelSerializer):
    answer_id = serializers.IntegerField(source='id', required=False)
    class Meta:
        model = Answer
        fields = ['answer_id', 'answer_name']
        list_serializer_class = AnswerListSerializer

    def __init__(self, *args, **kwargs):        
        is_process = kwargs['context'].get('is_process', None)
        super().__init__(*args, **kwargs)     
        if self.context['request'].user.is_staff:
           self.fields['is_true'] = serializers.BooleanField(required=False)
        if is_process:
            self.fields['answer_name'].required = False
            self.fields['answer_id'].required = True

            
    def to_representation(self, value):
        representation = super().to_representation(value)
        if ( not self.context.get('is_process', None) and
            not self.context['request'].user.is_staff and
            value.question.question_type == Question.ONLY_TEXT):
            representation['answer_name'] = ''        
        return representation


class QuestionListSerializer(serializers.ListSerializer):

    def update(self, instance, validated_data, pk):
        ret = []
        questions_mapping = {question['question_name']: question for question in validated_data}
        instance_questions_mapping ={item.question_name: item for item in instance}

        # Perform update or create.
        for question_name, question in questions_mapping.items():
            instance_question = instance_questions_mapping.get(question_name, None)
            if instance_question is not None:                
                ret.append(self.child.update(instance_question, question))
            else:
                ret.append(self.child.create(question, pk))

        # Perform deletions.
        for instance_question_name, instance_question in instance_questions_mapping.items():
            if instance_question_name not in questions_mapping:
                instance_question.delete()
        
        return ret 


class QuestionSerializer(serializers.ModelSerializer):
    question_id = serializers.IntegerField(source='id', required=False)
    class Meta:
        model = Question
        fields = ['question_id', 'question_name', 'question_type',]
        list_serializer_class = QuestionListSerializer
 
    def __init__(self, *args, **kwargs):
        is_detailed = kwargs.pop('is_detailed', None)
        is_process = kwargs['context'].get('is_process', None)
        super().__init__(*args, **kwargs)
        if is_detailed:
            self.fields['answers'] = AnswerSerializer(many=True, context=self.context)
            if is_process:
                self.fields['question_id'].required = True
    
    def update(self, instance, validated_data):
        answers_data = validated_data.pop('answers')
        instance.question_type = validated_data.get('question_type', instance.question_type)
        instance.save()
        self['answers'].update(instance.answers.all(), answers_data, pk = instance.pk)
        return instance

    def create(self, validated_data, pk):
        answers = validated_data.pop('answers')
        question = Question.objects.create(poll_id = pk, **validated_data)
        for answer in answers:
            Answer.objects.create(question = question, **answer)
        return question

    def to_representation(self, value):
        representation = super().to_representation(value)
        question_type = representation['question_type']
        question_type_mapped = Question.QUESTION_TYPE_DICT[question_type]
        representation['question_type'] = f'[{question_type}] - {question_type_mapped}'
        return representation

    def base_validation(self, question_type, question_name, answers_nums):
        """
        Perform base validation fields for admin and user process
        """
        if not answers_nums:
            raise ValidationError({question_name: 'There are no answers'})

        if question_type == Question.ONLY_TEXT and answers_nums > 1:
            raise ValidationError({question_name: 'This type of question requires only one answer'})

    def admin_validation(self, question_type, question_name, answers, answers_nums):
        """
        Perform admin specific validation fields
        """        
        true_answers = []
        if question_type != Question.ONLY_TEXT:
            if answers_nums < 2:
                raise ValidationError({question_name: 'This type of question requires multiple answers'})
           
            for answer in answers:
                if 'is_true' not in answer:
                    raise ValidationError({answer['answer_name']: "This answer requires boolean field 'is_true'"})
                true_answers.append(answer['is_true'])           
            
            if question_type == Question.ONE_ANSWER and true_answers.count(True) > 1:
                raise ValidationError({answer['answer_name']: "[OA] ONE_ANSWER question_type must have only one TRUE answer value in 'is_true' field"})
            
            if all(true_answers):
                raise ValidationError({question_name: 'All answers can not be TRUE'})
            elif not any(true_answers):
                raise ValidationError({question_name: 'All answers can not be FALSE'})
   
    def process_validation(self, question_type, question_name, answers, answers_nums):
        """
        Perform process specific validation fields:
        1. [OA] ONE_ANSWER question_type may have only one answer
        """ 
        if question_type == Question.ONE_ANSWER and answers_nums > 1:
            raise ValidationError({question_name: "[OA] ONE_ANSWER question_type must have only one TRUE answer"})

    def validate(self, value):
        """
        Perform validate both for admin and for user process:
        Base validation (admin and user process):
            1. If there are no answers - raise ValidationError 
            2. If Question_type '[OT] ONLY_TEXT':
                2.1 must have only one answer
        Admin specific validation:  
            1. If Question_type '[OT] ONLY_TEXT':
                1.1 must not have an answer boolean field 'is_true' 
            2. If Question_type '[OA] ONE_ANSWER' and '[MA] MANY_ANSWERS':
                2.1  must have more than one answers
                2.2 All answers field 'is_true' can not be TRUE or FALSE
                2.3 '[OA] ONE_ANSWER' must have only one TRUE value 'is_true' field
        """
        question_type = value['question_type']
        question_name = value['question_name']
        answers = value['answers']
        answers_nums = len(answers) 

        self.base_validation(question_type, question_name, answers_nums)
        if not self.context.get('is_process', None):
            self.admin_validation(question_type, question_name, answers, answers_nums)
        else:
            self.process_validation(question_type, question_name, answers, answers_nums)
        return value
    

class PollSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='poll-detail')
    class Meta:
        model = Poll
        fields = ['url', 'poll_name', 'date_start', 'date_finish', 'description']
        
    def __init__(self, *args, **kwargs):
        is_detailed = kwargs.pop('is_detailed', None)
        super().__init__(*args, **kwargs)
        is_update = self.context.get('is_update', None)
        if is_detailed:
            self.fields['questions'] = QuestionSerializer(is_detailed = True, many=True, context=self.context)
            if is_update:
                 self.fields['description'].required = False
                 self.fields['date_finish'].required = False
                 self.fields['poll_name'].required = False
                 self.fields['date_start'].read_only = True



    def create(self, validated_data):
        questions_data = validated_data.pop('questions')
        poll = Poll.objects.create(**validated_data)
        for question_data in questions_data:
            answers_data = question_data.pop('answers')
            question = Question.objects.create(poll = poll, **question_data)
            for answer_data in answers_data:
                answer = Answer.objects.create(question = question, **answer_data)
        return poll
    
    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions')
        instance.date_finish = validated_data.get('date_finish', instance.date_finish)
        instance.poll_name = validated_data.get('poll_name', instance.poll_name)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        self['questions'].update(instance.questions.all(), questions_data, pk=instance.pk)
        return instance


class ProcessPollSerializer(PollSerializer):
    poll_id = serializers.IntegerField(source='id', required=True)
    class Meta:
        model = Poll
        fields = ['poll_id',]

    def __init__(self, *args, **kwargs):
        kwargs.update({'is_detailed': True})
        kwargs.get('context', {}).update({'is_process': True})
        super().__init__(*args, **kwargs)  

    def is_correct_answer(self, question):
        answers = question['answers']
        correct_answers = Answer.objects.filter(question_id = question['id'])
        if question['question_type'] == Question.ONLY_TEXT:
            res = answers[0]['answer_name'] == correct_answers.get().answer_name
        else:
            given_answers = [answer['id'] for answer in answers]
            correct_answers = [answer.pk for answer in correct_answers.filter(is_true=True)]
            res = given_answers == correct_answers
        return res

    def save(self, user=None):        
        value = self.validated_data
        poll_id = value['id']
        results = self.get_results(value)
        if not user:      
            user = UserAnswers.objects.create()
        user.user_data.update({str(poll_id) : results})
        user.save() 
        return user

    def get_results(self, value):
        results = [] 
        questions = value['questions']
        for question in questions:
            result = self.is_correct_answer(question) 
            results.append({question['id']:  result})
        return results

    def to_internal_value(self, value):
        """ 
        Prepare incoming user data for validation:
        1. Check if poll_id is present
        2. Check if poll with poll_id exist in database
        3. Check if questions are preasent
        4. Check if questions match to poll
        5. Append additional data to every question 
           (question_type, question_name, answer_id for question_type [OT] only text)
        """   

        poll_id = value.get('poll_id', None)
        if poll_id is None:
            raise ValidationError({'poll_id':'Poll_id is not present'}) 
        else:
            try:
                poll = Poll.objects.get(pk = poll_id)
            except Poll.DoesNotExist:
                raise ValidationError({'poll_id': f'Poll with id = {poll_id} does not exist'})
       
        now = datetime.now().date()
        poll_finish_date = poll.date_finish
        if now > poll_finish_date:
            raise ValidationError({'date': f'Poll finish_date {poll_finish_date} is expired'})

        valid_questions_list = poll.questions.all().values_list('pk', flat=True)
        questions = value.get('questions', None)
       
        if questions is None:
            raise ValidationError({'questions':'Questions are not presents'}) 
       
        for question in questions:
            question_id = question.get('question_id', None)
          
            if question_id not in valid_questions_list:
                raise ValidationError({poll.poll_name: f'This poll does not have a question with id = {question_id}'})
            
            question_object = Question.objects.get(pk=question_id)
            question['question_type'] = question_object.question_type
            question['question_name'] = question_object.question_name
          
            if question['question_type'] == Question.ONLY_TEXT:
                if question['answers']:
                    question['answers'][0].update({'answer_id': 0})
        
        value = super().to_internal_value(value)
        return value
        