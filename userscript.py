class X(object):
    def __init__(self, foo):
        self.foo = foo

class Y(object):
    def __init__(self, x):
        self.xoo = x

    def boom(self):
        self.xoo.foo = "xoo foo!"

x = X(50)
x.zoo = 500
x.foo = 200
x.goo = 300
a = {0: 1}
a[1] = 42
y = Y(x)
y.boom()
