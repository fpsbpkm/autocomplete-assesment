class User:
    def __init__(self, name, age):
        self.__name = name
        self.__age = age
    
    @property
    def age(self):
        return self.__age
    
    @age.setter
    def age(self, age):
        if type(age) == int and age >= 0:
            self.__age = age
            return

    

a = User('Taro', 13)
print(a)
print()
