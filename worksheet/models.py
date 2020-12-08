from django.db import models
from django.core.exceptions import ValidationError

# Poll questions
class Poll(models.Model):
    poll_name = models.CharField(max_length=255)
    date_start = models.DateField(auto_now_add=True)
    date_finish = models.DateField()
    description = models.TextField()

# Questions
class Question(models.Model):    

    ONLY_TEXT = 'OT'
    ONE_ANSWER = 'OA'
    MANY_ANSWERS = 'MA'

    QUESTION_TYPE_DICT = {
        ONLY_TEXT: 'only_text',
        ONE_ANSWER: 'one_answer',
        MANY_ANSWERS: 'many_answers'
        }

    QUESTION_TYPE_CHOICES = [
        (ONLY_TEXT, QUESTION_TYPE_DICT[ONLY_TEXT]),
        (ONE_ANSWER, QUESTION_TYPE_DICT[ONE_ANSWER]),
        (MANY_ANSWERS, QUESTION_TYPE_DICT[MANY_ANSWERS]),
    ]

    question_name = models.CharField(max_length=255)
    question_type = models.CharField(max_length=2, choices=QUESTION_TYPE_CHOICES)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='questions')


# Answers
class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_name = models.CharField(max_length=255)
    is_true = models.BooleanField()

    def save(self, *args, **kwargs):
        if self.question.question_type == Question.ONLY_TEXT:
            self.is_true = True
        super().save(*args, **kwargs)
             
            
# UserAnswers
class UserAnswers(models.Model):    
    user_data = models.JSONField(null=False, default = dict)

