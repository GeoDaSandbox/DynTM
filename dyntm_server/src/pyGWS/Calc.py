import pyGWS
DEBUG = False

class GeoDaWS_Calc(pyGWS.GeoDaWebServiceClient):
    _url="http://127.0.0.1:8000/calc.json/"
    _url="http://apps.geodacenter.org/calc.json/"
    def __init__(self):
        pyGWS.GeoDaWebServiceClient.__init__(self,None,None)
    def operate(self,a,b,opp):
        if type(a) == float or type(b) == float:
            result = self._open("%f%s%f"%(a,opp,b)).read()
        else:
            result = self._open("%d%s%d"%(a,opp,b)).read()
        result = eval(result,{},{})
        return result['result']
    def add(self,a,b):
        return self.operate(a,b,'+')
    def subtract(self,a,b):
        return self.operate(a,b,'-')
    def multiple(self,a,b):
        return self.operate(a,b,'*')
    def divide(self,a,b):
        return self.operate(a,b,'/')
    def __call__(self,s):
        seps = {'*':self.multiple, '+':self.add, '-':self.subtract, '/': self.divide}
        for sep in seps:
            if sep in s:
                a,b = map(float,s.split(sep))
                return seps[sep](a,b)

if __name__ == '__main__':
    calc = GeoDaWS_Calc()

    c=0
    for i in range(1,25):
        c = calc.add(c,calc.multiple(i,i))
        print i,c
        assert calc.add(i,i) == i+i
        assert calc.divide(i,i) == i/i
        assert calc.subtract(i,i) == i-i
        assert calc.multiple(i,i) == i*i

