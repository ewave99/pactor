

class App:
    
    def __init__(self):
        self.interpreter = Interpreter()

    def run(self):
        while True:
            user_input = input()
            self.interpreter.processInput(user_input)


class Interpreter:

    def __init__(self):
        self.machine = Machine()

    def processInput(self, user_input):
        tokens = user_input.split(' ')
        try:
            for token in tokens:
                self.machine.processToken(token)
        except Exception as e:
            print(e)


class Machine:

    def __init__(self):
        self.stack = Stack()
        self.scope_stack = Stack()

        self.word_builder = WordBuilder()

    def processToken(self, token):
        item = self.getItem(token)
        item.execute(self)

    def getItem(self, token):
        is_int = True
        try:
            item = Literal(int, token)
        except ValueError:
            is_int = False
        if is_int:
            return item

        is_float = True
        try:
            item = Literal(float, token)
        except ValueError:
            is_float = False
        if is_float:
            return item

        is_word = True
        try:
            item = self.word_builder.createWord(self, token)
        except KeyError:
            is_word = False
        if is_word:
            return item

    def getDefinition(self, token):
        scope = self.getScope()
        if token in scope:
            return scope[token]
        raise Exception("Unknown token: {}".format(token))

    def getScope(self):
        if not self.scope_stack:
            return dict()
        return self.scope_stack.peek()


class Stack:

    def __init__(self):
        self._list = list()

    def __len__(self):
        return len(self._list)
    
    def __iter__(self):
        yield from self._list

    def push(self, item):
        self._list.append(item)

    def pop(self):
        return self._list.pop()

    def peek(self):
        return self._list[-1]


class WordBuilder:
    def __init__(self):
        self.builtins = dict()

        self.builtins["+"] = self.createTwoValFunction(lambda a, b: a + b)
        self.builtins["-"] = self.createTwoValFunction(lambda a, b: a - b)
        self.builtins["*"] = self.createTwoValFunction(lambda a, b: a * b)
        self.builtins["/"] = self.createTwoValFunction(lambda a, b: a / b)
        self.builtins["%"] = self.createTwoValFunction(lambda a, b: a % b)
        self.builtins["//"] = self.createTwoValFunction(lambda a, b: a // b)
        self.builtins["**"] = self.createTwoValFunction(lambda a, b: a ** b)

        self.builtins[".s"] = self.printStack
        self.builtins["."] = self.printTop

        self.builtins["drop"] = self.drop
        self.builtins["dup"] = self.dup
        self.builtins["swap"] = self.swap

    def createWord(self, machine, token):
        func = self.getWordFunction(machine, token)
        word = Word(func)
        return word

    def getWordFunction(self, machine, token):
        if token in self.builtins:
            return self.builtins[token]
        return machine.getDefinition(token)

    def createOneValFunction(self, base_func):

        def func(machine):
            item = machine.stack.pop()
            result = base_func(item)
            machine.stack.push(result)

        return func

    def createTwoValFunction(self, base_func):

        def func(machine):
            b = machine.stack.pop()
            a = machine.stack.pop()
            result = base_func(a, b)
            machine.stack.push(result)

        return func

    def printStack(self, machine):
        string = ""
        for item in machine.stack:
            string += "{} ".format(item)
        string += "<- TOP"
        print(string)

    def printTop(self, machine):
        item = machine.stack.pop()
        print(item)

    def drop(self, machine):
        machine.stack.pop()

    def dup(self, machine):
        item = machine.stack.pop()
        machine.stack.push(item)
        machine.stack.push(item)

    def swap(self, machine):
        b = machine.stack.pop()
        a = machine.stack.pop()
        machine.stack.push(b)
        machine.stack.push(a)


class Word:

    def __init__(self, func):
        self.func = func

    def execute(self, machine):
        self.func(machine)


class Block:

    def __init__(self, children):
        pass

    def execute(self, machine):
        pass


class Literal:

    def __init__(self, baseclass, identifier):
        self.value = baseclass(identifier)

    def execute(self, machine):
        machine.stack.push(self.value)


class Definition:

    def __init__(self, identifier, sequence):
        pass

    def execute(self, machine):
        pass

if __name__ == "__main__":
    app = App()
    app.run()
