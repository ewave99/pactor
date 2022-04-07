import sys


class App:
    
    def __init__(self):
        self.interpreter = Interpreter()
        self.user_input = None
    
    def run(self):
        if len(sys.argv) == 1:
            self.runRepl()
        elif len(sys.argv) > 1:
            self.runWithFile(sys.argv[1])

    def runRepl(self):
        while True:
            self.handleUserInput()
            self.processInput(self.user_input)

    def runWithFile(self, filename):
        with open(filename, 'r') as file:
            for line in file:
                self.processInput(line)

    def processInput(self, input_text):
        self.interpreter.processInput(input_text)

    def handleUserInput(self):
        try:
            self.user_input = input()
        except EOFError:
            sys.exit(0)


class Interpreter:

    def __init__(self):
        self.machine = Machine()

    def processInput(self, user_input):
        tokens = user_input.split(' ')
        try:
            for token in tokens:
                self.machine.processToken(token.strip())
        except Exception as e:
            print(e)


class Machine:

    def __init__(self):
        self.stack = Stack()
        self.scope_stack = Stack()
        self.scope_stack.push(dict())

        self.word_builder = WordBuilder()
        self.literal_builder = LiteralBuilder()

        self.parsing_block_level = 0

    def processToken(self, token):
        if not token:
            return
        if token != "{" and token != "}":
            if self.parsing_block_level == 0:
                item = self.getItem(token)
                item.execute(self)
            else:
                block = self.stack.pop()
                block.addChild(token)
                self.stack.push(block)
        elif token == "{":
            if self.parsing_block_level == 0:
                item = self.getItem(token)
                item.execute(self)
                self.parsing_block_level += 1
            else:
                block = self.stack.pop()
                block.addChild(token)
                self.stack.push(block)
                self.parsing_block_level += 1
        elif token == "}":
            if self.parsing_block_level > 1:
                block = self.stack.pop()
                block.addChild(token)
                self.stack.push(block)
            self.parsing_block_level -= 1
        #print(self.stack)
        #print(self.parsing_block_level)

    def getItem(self, token):
        is_string = token[0] == "'"
        if is_string:
            item = self.literal_builder.fromIdentifier(str, token[1:])
            return item

        is_int = True
        try:
            item = self.literal_builder.fromIdentifier(int, token)
        except ValueError:
            is_int = False
        if is_int:
            return item

        is_float = True
        try:
            item = self.literal_builder.fromIdentifier(float, token)
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
        self.builtins["rot"] = self.rot

        self.builtins["{"] = self.blockStart
        self.builtins["}"] = self.blockEnd

        self.builtins["define"] = self.define
        self.builtins["do"] = self.do
        self.builtins["while"] = self.while_
        self.builtins["dowhile"] = self.dowhile
        self.builtins["if"] = self.if_
        self.builtins["ifelse"] = self.ifelse

    def createWord(self, machine, token):
        func = self.getWordFunction(machine, token)
        word = Word(func)
        return word

    def getWordFunction(self, machine, token):
        if token in self.builtins:
            return self.builtins[token]
        return self.getDefinition(machine, token)

    def getDefinition(self, machine, token):
        scope = self.getScope(machine)
        if token in scope:
            return scope[token]
        raise Exception("Unknown token: {}".format(token))

    def getScope(self, machine):
        if not machine.scope_stack:
            return dict()
        return machine.scope_stack.peek()

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

    def rot(self, machine):
        c = machine.stack.pop()
        b = machine.stack.pop()
        a = machine.stack.pop()
        machine.stack.push(b)
        machine.stack.push(c)
        machine.stack.push(a)

    def blockStart(self, machine):
        block = Block()
        machine.stack.push(block)

    def blockEnd(self, machine):
        pass

    def define(self, machine):
        name = machine.stack.pop()
        if not isinstance(name, str):
            raise Exception("Invalid definition name, must be string.")
        item = machine.stack.pop()
        scope = machine.scope_stack.pop()
        if isinstance(item, Block):
            scope[name] = item.execute
        else:
            literal = machine.literal_builder.fromValue(item)
            scope[name] = literal.execute
        machine.scope_stack.push(scope)

    def do(self, machine):
        block = machine.stack.pop()
        if not isinstance(block, Block):
            raise Exception("Invalid do body, must be a code block.")
        block.execute(machine)

    def while_(self, machine):
        block = machine.stack.pop()
        if not isinstance(block, Block):
            raise Exception("Invalid while body, must be a code block.")
        flag = machine.stack.peek()
        while flag:
            block.execute(machine)
            flag = machine.stack.peek()

    def dowhile(self, machine):
        block = machine.stack.pop()
        if not isinstance(block, Block):
            raise Exception("Invalid dowhile body, must be a code block.")
        block.execute(machine)
        flag = machine.stack.peek()
        while flag:
            block.execute(machine)
            flag = machine.stack.peek()

    def if_(self, machine):
        block = machine.stack.pop()
        if not isinstance(block, Block):
            raise Exception("Invalid if body, must be a code block.")
        flag = machine.stack.peek()
        if flag:
            block.execute(machine)

    def ifelse(self, machine):
        block_else = machine.stack.pop()
        if not isinstance(block_else, Block):
            raise Exception("Invalid ifelse body, must be a code block.")
        block_if = machine.stack.pop()
        if not isinstance(block_if, Block):
            raise Exception("Invalid ifelse body, must be a code block.")
        flag = machine.stack.peek()
        if flag:
            block_if.execute(machine)
        else:
            block_else.execute(machine)


class Word:

    def __init__(self, func):
        self.func = func

    def __repr__(self):
        return str(self.func)

    def execute(self, machine):
        self.func(machine)


class Block:

    def __init__(self):
        self.children = list()

    def __repr__(self):
        string = "{ "
        for child in self.children:
            string += "{} ".format(child)
        string += "}"
        return string

    def addChild(self, child):
        self.children.append(child)

    def execute(self, machine):
        parent_scope = machine.scope_stack.peek()
        scope = parent_scope.copy()

        machine.scope_stack.push(scope)

        for child in self.children:
            machine.processToken(child)

        machine.scope_stack.pop()


class LiteralBuilder:

    def fromValue(self, value):
        return Literal(value)

    def fromIdentifier(self, baseclass, identifier):
        if baseclass is str:
            value = self.handleString(identifier)
        else:
            value = baseclass(identifier)
        return Literal(value)

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


class Literal:

    def __init__(self, value):
        self.value = value

    def execute(self, machine):
        machine.stack.push(self.value)


if __name__ == "__main__":
    app = App()
    app.run()
