class Stack:

    def __init__(self):
        self._list = list()

    def __repr__(self):
        string = ""
        for x in self._list:
            string += "{} ".format(repr(x))
        string += "<- TOP"
        return string

    def __len__(self):
        return len(self._list)

    def push(self, item):
        self._list.append(item)

    def pop(self):
        return self._list.pop()

class Block:

    def __init__(self, commands, definitions=dict()):
        self.commands = commands
        self.definitions = definitions

    def toDict(self):
        return { 'definitions': self.definitions, 'commands': self.commands }

    def __repr__(self):
        return repr(self.toDict())

    def updateDefinitions(self, name, block):
        self.definitions[name] = block


class Machine:

    def __init__(self):
        self.data_stack = Stack()
        self.builtins = {
            'define' : self.createDefinition,
            'round'  : self.createOneValFunction(round),
            'int'    : self.createOneValFunction(int  ),
            'float'  : self.createOneValFunction(float),
            'str'    : self.createOneValFunction(str  ),
            'bool'   : self.createOneValFunction(bool ),
            '+'      : self.createTwoValFunction(lambda a, b: a +  b),
            '-'      : self.createTwoValFunction(lambda a, b: a -  b),
            '*'      : self.createTwoValFunction(lambda a, b: a *  b),
            '/'      : self.createTwoValFunction(lambda a, b: a /  b),
            '%'      : self.createTwoValFunction(lambda a, b: a %  b),
            '**'     : self.createTwoValFunction(lambda a, b: a ** b),
            '&'      : self.createTwoValFunction(lambda a, b: a &  b),
            '|'      : self.createTwoValFunction(lambda a, b: a |  b),
            'drop'   : self.drop,
            'dup'    : self.dup,
            'swap'   : self.swap,
            'clear'  : self.clear,
            '.'      : self.output,
            '.s'     : self.outputDataStack,
            'if'     : self.if_,
            'ifelse' : self.ifelse,
            'while'  : self.while_
        }
        self.block_stack = Stack()

    def decodeTokens(self, tokens, definitions):
        for i, token in enumerate(tokens):
            self.decodeToken(i, token, definitions)

    def decodeToken(self, i, token, definitions):
        if token == "{":
            return lambda x: None
        if token == "}":
            return lambda x: None

        if token in self.builtins:
            return self.builtins[token]

        # handle strings with both single and double quotation marks
        if len(token) >= 2 and token[0] == '"' and token[-1] == '"':
            # token represents a string
            return self.createPushFunction(token[1:-1])
        if len(token) >= 2 and token[0] == "'" and token[-1] == "'":
            # token represents a string
            return self.createPushFunction(token[1:-1])

        is_int = True
        try:
            int_value = int(token)
        except:
            is_int = False
        if is_int:
            return self.createPushFunction(int_value)

        is_float = True
        try:
            float_value = float(token)
        except:
            is_float = False
        if is_float:
            return self.createPushFunction(float_value)

        return createDefinitionExecutionFunction(token)

    def createDefinitionExecutionFunction(self, token):
        def func():
            block = self.block_stack.pop()
            if token not in block.definitions:
                raise Exception("Unknown word: {}".format(token))
            executeBlock(block.definitions[token])

    def createDefinition(self):
        block = self.data_stack.pop()
        name = self.data_stack.pop()
        if not isinstance(name, str):
            raise Exception("Definition name must be string.")
        parent = self.block_stack.pop()
        parent.updateDefinitions(name, block)
        self.block_stack.push(parent)

    def createOneValFunction(self, meta_function):
        def func():
            a = self.data_stack.pop()
            self.data_stack.push(meta_function(a))
        return func

    def createTwoValFunction(self, meta_function):
        def func():
            b = self.data_stack.pop()
            a = self.data_stack.pop()
            self.data_stack.push(meta_function(a, b))
        return func

    def createPushFunction(self, item):
        def push():
            self.data_stack.push(item)
        return push

    def drop(self):
        self.data_stack.pop()

    def dup(self):
        a = self.data_stack.pop()
        self.data_stack.push(a)
        self.data_stack.push(a)

    def swap(self):
        b = self.data_stack.pop()
        a = self.data_stack.pop()
        self.data_stack.push(b)
        self.data_stack.push(a)

    def clear(self):
        while self.data_stack:
            self.data_stack.pop()

    def output(self):
        print(self.data_stack.pop())

    def outputDataStack(self):
        print(repr(self.data_stack))

    def if_(self):
        block = self.data_stack.pop()
        flag = self.data_stack.pop()
        self.data_stack.push(flag)
        if bool(flag) == True:
            self.executeBlock(block)

    def ifelse(self):
        block_else = self.data_stack.pop()
        block_if = self.data_stack.pop()
        flag = self.data_stack.pop()
        self.data_stack.push(flag)
        if bool(flag) == True:
            self.executeBlock(block_if)
        else:
            self.executeBlock(block_else)

    def while_(self):
        block = self.data_stack.pop()
        flag = self.data_stack.pop()
        self.data_stack.push(flag)
        while flag:
            self.executeBlock(block)
            flag = self.data_stack.pop()
            self.data_stack.push(flag)




class Interpreter:

    def __init__(self):
        self.machine = Machine()
        self.tokens = []

    def run(self):
        while True:
            try:
                self.fetchInput()
                self.decodeInput()
                self.executeCommands()
            except Exception as e:
                print(e)

    def fetchInput(self):
        self.tokens = input().split()

    def decodeInput(self):
        try:
            self.commands = self.machine.decodeTokens(self.tokens, dict())
        except Exception as e:
            raise e

    def executeCommands(self):
        try:
            self.machine.executeCommands(self.commands)
        except Exception as e:
            raise e

if __name__ == "__main__":
    app = Interpreter()
    app.run()
