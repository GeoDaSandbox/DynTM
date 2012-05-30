from django.db import models

# Create your models here.
class Calc(models.Model):
    @staticmethod
    def add(left,right):
        return left+right
    @staticmethod
    def sub(left,right):
        return left-right
    @staticmethod
    def multiply(left,right):
        return left*right
    @staticmethod
    def divide(left,right):
        return left/float(right)
