import sys


class App:
    
    def __init__(self):
        self.interpreter = Interpreter()

    def run(self):
        while True:
            try:
                user_input = input()
            except EOFError:
                sys.exit(0)

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
        self.scope_stack.push(dict())

        self.word_builder = WordBuilder()

        self.do_execute = True

    def processToken(self, token):
        item = self.getItem(token)
        if self.do_execute or token == "}":
            item.execute(self)
        else:
            block = self.stack.pop()
            block.addChild(item)
            self.stack.push(block)

    def getItem(self, token):
        is_string = token[0] == "'"
        if is_string:
            item = Literal(str, token[1:])
            return item

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

    def __repr__(self):
        string = ""
        for item in self:
            string += "{} ".format(repr(item))
        string += "<- TOP"
        return string

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

        self.builtins["int"] = self.createOneValFunction(lambda a: int(a))
        self.builtins["float"] = self.createOneValFunction(lambda a: float(a))
        self.builtins["str"] = self.createOneValFunction(lambda a: str(a))
        self.builtins["bool"] = self.createOneValFunction(lambda a: bool(a))

        self.builtins["~"] = self.createOneValFunction(lambda a: ~a)

        self.builtins["not"] = self.createOneValFunction(lambda a: not a)

        self.builtins["+"] = self.createTwoValFunction(lambda a, b: a + b)
        self.builtins["-"] = self.createTwoValFunction(lambda a, b: a - b)
        self.builtins["*"] = self.createTwoValFunction(lambda a, b: a * b)
        self.builtins["/"] = self.createTwoValFunction(lambda a, b: a / b)
        self.builtins["%"] = self.createTwoValFunction(lambda a, b: a % b)
        self.builtins["//"] = self.createTwoValFunction(lambda a, b: a // b)
        self.builtins["**"] = self.createTwoValFunction(lambda a, b: a ** b)

        self.builtins["&"] = self.createTwoValFunction(lambda a, b: a & b)
        self.builtins["|"] = self.createTwoValFunction(lambda a, b: a | b)
        self.builtins["^"] = self.createTwoValFunction(lambda a, b: a ^ b)
        self.builtins["<<"] = self.createTwoValFunction(lambda a, b: a << b)
        self.builtins[">>"] = self.createTwoValFunction(lambda a, b: a >> b)

        self.builtins["and"] = self.createTwoValFunction(lambda a, b: a and b)
        self.builtins["or"] = self.createTwoValFunction(lambda a, b: a or b)

        self.builtins["="] = self.createTwoValFunction(lambda a, b: a == b)
        self.builtins["!="] = self.createTwoValFunction(lambda a, b: a != b)
        self.builtins["<"] = self.createTwoValFunction(lambda a, b: a < b)
        self.builtins["<="] = self.createTwoValFunction(lambda a, b: a <= b)
        self.builtins[">"] = self.createTwoValFunction(lambda a, b: a > b)
        self.builtins[">="] = self.createTwoValFunction(lambda a, b: a >= b)

        self.builtins[".s"] = self.printStack
        self.builtins["."] = self.printTop

        self.builtins["defs"] = self.printDefs

        self.builtins["drop"] = self.drop
        self.builtins["dup"] = self.dup
        self.builtins["swap"] = self.swap

        self.builtins["{"] = self.blockStart
        self.builtins["}"] = self.blockEnd

        self.builtins["define"] = self.define
        self.builtins["while"] = self.while_
        self.builtins["if"] = self.if_
        self.builtins["ifelse"] = self.ifelse

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
        print(machine.stack)

    def printTop(self, machine):
        item = machine.stack.pop()
        print(item)

    def printDefs(self, machine):
        scope = machine.scope_stack.peek()
        print(scope)

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

    def blockStart(self, machine):
        block = Block()
        machine.stack.push(block)
        machine.do_execute = False

    def blockEnd(self, machine):
        machine.do_execute = True

    def define(self, machine):
        name = machine.stack.pop()
        if not isinstance(name, str):
            raise Exception("Invalid definition name, must be string.")
        block = machine.stack.pop()
        if not isinstance(block, Block):
            raise Exception("Invalid definition body, must be a code block.")
        scope = machine.scope_stack.pop()
        scope[name] = block.execute
        machine.scope_stack.push(scope)

    def while_(self, machine):
        pass

    def if_(self, machine):
        pass

    def ifelse(self, machine):
        pass


class Word:

    def __init__(self, func):
        self.func = func

    def execute(self, machine):
        self.func(machine)


class Block:

    def __init__(self):
        self.children = list()

    def addChild(self, child):
        self.children.append(child)

    def execute(self, machine):
        parent_scope = machine.scope_stack.peek()
        scope = parent_scope.copy()
        machine.scope_stack.push(scope)
        for child in self.children:
            child.execute(machine)
        machine.scope_stack.pop()


class Literal:

    def __init__(self, baseclass, identifier):
        if baseclass is str:
            self.value = self.handleString(identifier)
        else:
            self.value = baseclass(identifier)

    def handleString(self, identifier):
        # replace _ with space unless there is a \ before the _
        new_string = ""
        i = 0
        while i < len(identifier):
            if identifier[i] == "\\":
                if i < len(identifier) - 1:
                    new_string += identifier[i + 1]
                    i += 2
            elif identifier[i] == "_":
                new_string += " "
                i += 1
            else:
                new_string += identifier[i]
                i += 1
        return new_string

    def execute(self, machine):
        machine.stack.push(self.value)


if __name__ == "__main__":
    app = App()
    app.run()
