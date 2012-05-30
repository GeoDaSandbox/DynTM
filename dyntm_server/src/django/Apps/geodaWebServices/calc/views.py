from django.http import HttpResponse
from django.template import Template
from geodaWebServices import WebService

class Calc(WebService):
    def __init__(self,format='HTML'):
        t = Template("{{left}} {{operation}} {{right}} = {{result}}")
        WebService.__init__(self,format,t)
    def get(self,left=0,operation=None,right=0):
        if not operation:
            return self.index()
        left = float(left) if left else 0.0
        right = float(right) if right else 0.0
        result = {'+':self.add, '-':self.sub, '*':self.multi, '/':self.div}[operation](left,right)
        return self.write({'left':left,'right':right,'result':result,'operation':operation})
    def index(self):
        # This should be a template for the web service's home page. (if there is one)
        return HttpResponse('Welcome to my Calculator Web Service!')
    def add(self,left,right):
        return left+right
    def sub(self,left,right):
        return left-right
    def multi(self,left,right):
        return left*right
    def div(self,left,right):
        return left/right
