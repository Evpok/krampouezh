'''
@author: Loïc Grobol <loic.grobol@gmail.com>
Copyright © 2014, Loïc Grobol <loic.grobol@gmail.com>
Permission is granted to Do What The Fuck You Want To
with this document.

See the WTF Public License, Version 2 as published by Sam Hocevar
at http://www.wtfpl.net if you need more details.

A naïve syntax tree to help format function definitions for several engines.

Plans are for support of
  - Python
  - LaTeX maths
  - Geogebra
  - Pgf/TikZ
'''

import itertools as it
class Term:
    pass

class Sum(Term):
    def __init__(self, summands):
        self.summands = summands

    def __str__(self):
        return '({})'.format('+'.join(('{}'.format(s) for s in self.summands)))

    def latex(self):
        return '({})'.format('+'.join(('{}'.format(s.latex()) for s in self.summands)))

    def geogebra(self):
        return '({})'.format('+'.join(('{}'.format(s.geogebra()) for s in self.summands)))
        
    def pgf(self):
        return '({})'.format('+'.join(('{}'.format(s.pgf()) for s in self.summands)))
        
    def value(self, *args, **kwargs):
        return sum(s.value(*args, **kwargs) for s in self.summands)
    
    
class Scale(Term):
    def __init__(self, scale, vector):
        self.scale = scale
        self.vector = vector

    def __str__(self):
        return '({scale}*{vector})'.format(**self.__dict__)
        
    def geogebra(self):
        return '({scale}*{vector})'.format(**{a: self.__dict__[a].geogebra() for a in self.__dict__})

    def latex(self):
        return '({scale}*{vector})'.format(**{a: self.__dict__[a].latex() for a in self.__dict__})
        
    def pgf(self):
        return '({scale}*{vector})'.format(**{a: self.__dict__[a].pgf() for a in self.__dict__})
        
    def value(self, *args, **kwargs):
        return self.scale.value(*args, **kwargs)*self.vector.value(*args, **kwargs)
        
        
class Scalar(Term):
    def __init__(self, scalar):
        self.scalar = scalar

    def __str__(self):
        return str(self.scalar)
        
    def value(self, *args, **kwargs):
        return self.scalar

    geogebra = __str__
    pgf = __str__
    latex = __str__
    

class Integer(Scalar):
    pass

    
class Minus(Term):
    def __init__(self, val):
        self.val = val
        
    def __str__(self):
        return '(-{})'.format(self.val)
        
    def geogebra(self):
        return '(-{})'.format(self.val.geogebra())

    def latex(self):
        return '(-{})'.format(self.val.latex())
        
    def pgf(self):
        return '(-{})'.format(self.val.pgf())
        
    def value(self, *args, **kwargs):
        return -self.val.value(*args, **kwargs)
        
        
class Variable(Term):
    def __init__(self, varname='x'):
        self.varname = varname
        
    
    def __str__(self):
        return self.varname        

    geogebra = __str__
    
    def pgf(self):
        return r'\{}'.format(self.varname)
        
    latex = __str__
    
    def value(self, *args, **kwargs):
        return kwargs[self.varname]
        

class Power(Term):
    def __init__(self, var, power):
        self.var = var
        self.power = power

    def __str__(self):
        return '({var}**{power})'.format(**self.__dict__)
        
    def geogebra(self):
        return '({var}^{power})'.format(**{a: self.__dict__[a].geogebra() for a in self.__dict__})

    def latex(self):
        return '({var}^{{{power}}})'.format(**{a: self.__dict__[a].latex() for a in self.__dict__})
        
    def pgf(self):
        return '({var}^{power})'.format(**{a: self.__dict__[a].pgf() for a in self.__dict__})
        
    def value(self, *args, **kwargs):
        return self.var.value(*args, **kwargs)**self.power.value(*args, **kwargs)
        

class RealFun(Term):
    def __init__(self, a, b, image, variable):
        self.a = a
        self.b = b
        self.image = image
        self.variable = variable
    
    def __str__(self):
        return r'''def f({variable}):
    if {a}<={variable}<={b}:
        return {image}
    else:
        raise DomainError()'''.format(**self.__dict__)
        
    def geogebra(self):
        return 'Function[{a}, {b}, {image}]'.format(**{a: self.__dict__[a].geogebra() for a in self.__dict__})
    
    def pgf(self):
        return r'\draw[smooth,samples=100,domain={a}:{b}] plot({variable},{{{image}}});'.format(**{a: self.__dict__[a].pgf() for a in self.__dict__})
    
    def latex(self):
        return '{variable}⟼{image}'.format(**{a: self.__dict__[a].latex() for a in self.__dict__})
        
    def value(self, *args, **kwargs):
        if not (a.value(*args, **kwargs) <= self.variable.value(*args, **kwargs) <=  a.value(*args, **kwargs)):
            raise DomainError()
        return self.image.value(*args, **kwargs)
        

class Indicator(Term):
    '''Indicator of [a,b[ (𝟙_{[a,b[}).'''
    def __init__(self, a, b, variable):
        self.a = a
        self.b = b
        self.variable = variable
        
    def __str__(self):
        return '(1 if {a} <= {variable} < {b} else 0)'.format(**self.__dict__)
        
    def geogebra(self):
        return '(If[x>={a} && x<{b},{variable},0])'.format(**{a: self.__dict__[a].geogebra() for a in self.__dict__})
        
    def latex(self):
        return r'𝟙_{{\left[{a}, {b}\right[}}({variable})'.format(**{a: self.__dict__[a].latex() for a in self.__dict__})
        
    def pgf(self):
        return 'and({variable}>={a},{variable}<{b})'.format(**{a: self.__dict__[a].pgf() for a in self.__dict__})
        
    def value(self, *args, **kwargs):
        return 1 if a.value(*args, **kwargs) <= variable.value(*args, **kwargs) < b.value(*args, **kwargs) else 0


class DomainError(Exception):
    pass
    
    
def piecewise_polynomial(variable, coefs, bounds):
    bounds = sorted(list(bounds))
    img = Sum(
	  (Scale(
		Sum(
		    (Scale(Scalar(c),Power(Sum((variable,Minus(Scalar(a)))),Integer(i)))
		    for c,i in zip(piece_coefs,it.count()))),
		Indicator(Scalar(a),Scalar(b),variable))
	  for a,b,piece_coefs in zip(bounds[:-1],bounds[1:],coefs)))
    #print(str(img))
    return RealFun(Scalar(bounds[0]), Scalar(bounds[-1]), img, variable)
        
        
def tree_fun(tree, *vars):
    '''Return a callable that returns the evaluation of `tree` afer the substitution of
       `vars`. That is `tree_fun(tree, ('x', 'y'))(2,5)` is `tree.value({'x': 2, 'y':5})`.'''
    def f(*vals):
        return tree.value({x: y for x,y in zip(vars, vals)})
    return f

if __name__=='__main__':
    x = Variable()
    import libinterpol
    c = list(libinterpol.cubic_coefs(((0,-2),(3,1),(2,7),(1,3),(5,-6))))
    f = piecewise_polynomial(x, c, (0,2,3,1,5))
    print(f.pgf())

