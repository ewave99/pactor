

class App:

    def __init__(self):
        self.interpreter = Interpreter()

    def run(self):
        while True:
            user_input = input()
            self.interpreter.run(user_input)


class Interpreter:

    def __init__(self):
        self.machine = Machine()

    def run(self, user_input):
        words = user_input.split(' ')
        for word in words:
            self.machine.execute(word)


class Machine:

    def __init__(self):
        self.block_level = 0
        self.stack = Block(self.block_level)
        self.hierarchy_stack = Block(0)
        self.current_defs = self.hierarchy_stack.defs

    def execute(self, word):
        if word == "{":
            self.block_level += 1
            block = Block(self.block_level)
            block.defs.update(self.current_defs)
            self.stack.push(block)
            self.hierarchy_stack.push(block)

        elif word == "}":
            b = self.stack.pop()
            # if block b is not closed
            if self.block_level >= b.level:
                # close it
                self.block_level -= 1


            # if we have already closed the last block
            # then we are closing the parent
            else:
                # Revert the defs to the parent.
                # If the block does not have a parent:
                if b.level <= 1:
                    self.stack.push(b)
                    self.current_defs = self.stack.defs
                else:
                    # we are using a block as a temporary stack here
                    children_stack = Block(0)
                    children_stack.push(b)
                    child = self.stack.pop()
                    while not (isinstance(child, Block) and child.level < self.block_level):
                        children_stack.push(child)
                        child = self.stack.pop()
                    parent = child
                    while children_stack:
                        child = children_stack.pop()
                        parent.push(child)
                    self.stack.push(parent)
                    self.current_defs = parent.defs

        elif word == ".s":
            print(self.stack)

        else:
            if self.block_level <= 0:
                if word == "define":
                    name_block = self.stack.pop()
                    if not isinstance(name_block, block):
                        raise exception("definition name should be block with length 1.")
                    if len(block) != 1:
                        raise exception("invalid name for definition.")
                    code_block = self.stack.pop()
                    if not isinstance(code_block, block):
                        raise exception("definition body must be block.")
                    name = name_block.items[0]
                    self.stack.defs[name] = code_block

                elif word in self.stack.defs:
                    self.executeBlock(self.stack.defs[word])
            else:
                top = self.stack.pop()
                top.push(word)
                self.stack.push(top)

    def executeBlock(self, block):
        pass


class Block:

    def __init__(self, level):
        self.level = level
        self.items = list()
        self.defs = dict()
        self.closed = False

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        yield from self.items

    def __repr__(self):
        string = "{ "
        for item in self.items:
            string += "{} ".format(repr(item))
        string += "}"
        string += ":{}".format(self.level)
        return string

    def push(self, item):
        self.items.append(item)

    def pop(self):
        return self.items.pop()

if __name__ == "__main__":
    app = App()
    app.run()
