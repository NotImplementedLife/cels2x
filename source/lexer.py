from __future__ import annotations
from fa import Charset, TextFiniteAutomaton

class RegularExpression:
    def __init__(self, regex):
        self.fa = RegularExpression.parse_regex(regex)

    @staticmethod
    def parse_regex(regex) -> RegularExpression:
        class LeftBracket:
            def __repr__(self): return "<LeftBracket>"
        class Escape:
            def __repr__(self): return "<Escape>"
        class RangeOp:
            def __repr__(self): return "<RangeOp>"
        class Literal:
            def __init__(self, c): self.char = c
            def __eq__(self, other): return isinstance(other, Literal) and self.char==other.char
            def __repr__(self): return f"<Literal[{repr(self.char)}]>"
        class FAOr:
            def __repr__(self): return "<FAOr>"
        class LeftParen:
            def __repr__(self): return "<LeftParen>"
        class Compl:
            def __repr__(self): return "<Compl>"
        leftBracket = LeftBracket()
        escape = Escape()
        range_op = RangeOp()
        faor = FAOr()
        leftParen = LeftParen()
        compl = Compl()

        stack = []

        def is_last_on_stack(cond): return len(stack)>0 and cond(stack[-1])
        def pop_last_two():
            if len(stack)<2: raise RuntimeError("Invalid stack when attempting pop")
            last = stack.pop()
            second2last = stack.pop()
            return second2last, last

        def pop_until(cond):
            done=False
            res = []
            while len(stack)>0  and not done:
                it = stack.pop()
                if cond(it): done=True; continue
                res.append(it)
            if not done:
                raise RuntimeError("ParseError: token mismatch")
            return res[::-1]

        def push_char_in_range(c):
            if isinstance(c, str):
                if is_last_on_stack(lambda _:_ == escape):
                    stack.pop()
                    push_char_in_range(Literal(c))
                    return True
                if c=='\\': stack.append(escape); return True
                if c=='-':
                    if is_last_on_stack(lambda _:_==range_op):
                        raise ValueError("Duplicate range operator --")
                    stack.append(range_op)
                    return True
                if c==']':
                    ranges = pop_until(lambda _:_==leftBracket)
                    charset = Charset.empty()
                    negate = False
                    for r in ranges:
                        if isinstance(r, Charset):
                            charset = charset+r
                        elif isinstance(r, Literal):
                            charset = charset+Charset.single_char(r.char)
                        elif r==compl: negate = True
                    if negate: charset = ~charset
                    stack.append(TextFiniteAutomaton({('Q0', charset):["Q1"]}, "Q0", ["Q1"]))
                    return False
                if c=='^' and is_last_on_stack(lambda _:_==leftBracket):
                    stack.append(compl)
                push_char_in_range(Literal(c))
                return True
            if isinstance(c, Literal):
                if is_last_on_stack(lambda _:_==range_op):
                    d, _ = pop_last_two()
                    if not isinstance(d, Literal):
                        raise RuntimeError(f"Parse error: expected literal, got {type(d)}")
                    stack.append(Charset.range(d.char, c.char))
                    return True
                stack.append(c)
                return True

        def push_in_fa_ctx(c):
            if isinstance(c, str):
                if is_last_on_stack(lambda _:_ == escape):
                    stack.pop()
                    push_in_fa_ctx(TextFiniteAutomaton({('Q0', Charset.single_char(c)):['Q1']}, 'Q0', ['Q1']))
                    return
                if c=='\\': stack.append(escape); return
                if c=='*' or c=='+':
                    if not is_last_on_stack(lambda _:isinstance(_, TextFiniteAutomaton)):
                        raise ValueError(f"SyntaxError before '{c}': invalid expression")
                    fa = stack.pop()
                    push_in_fa_ctx(fa^c)
                    return
                if c=='|': stack.append(faor); return
                if c=='(': stack.append(leftParen); return
                if c==')':
                    fas = pop_until(lambda _:_==leftParen)
                    fa = TextFiniteAutomaton.empty()
                    for a in fas: fa = fa * a
                    push_in_fa_ctx(fa)
                    return
                push_in_fa_ctx(TextFiniteAutomaton({('Q0', Charset.single_char(c)):['Q1']}, 'Q0', ['Q1']))
                return
            if isinstance(c, TextFiniteAutomaton):
                if is_last_on_stack(lambda _:_==faor):
                    d, _ = pop_last_two()
                    if not isinstance(d, TextFiniteAutomaton):
                        raise RuntimeError(f"SyntaxError error: expected expression, got {type(d)}")
                    push_in_fa_ctx(c + d)
                    return
                stack.append(c)

        charset_mode = False
        for c in regex:
            if not charset_mode:
                if c=='[':
                    if is_last_on_stack(lambda _:_==escape):
                        stack.pop()
                        push_in_fa_ctx(TextFiniteAutomaton({('Q0', Charset.single_char(c)):['Q1']}, 'Q0', ['Q1']))
                    else:
                        stack.append(leftBracket)
                        charset_mode = True
                        continue
                else: push_in_fa_ctx(c)
            else:
                if not push_char_in_range(c): charset_mode = False
                continue

        fa = TextFiniteAutomaton.empty()
        for a in stack: fa = fa * a

        return fa

class LexicalToken:
    def __init__(self, value, token_type, pos, row, col, props = None):
        self._value = value
        self._token_type = token_type
        self._pos = pos
        self._row = row
        self._col = col
        self.props = props if props is not None else {}

    value = property(lambda s:s._value)
    token_type = property(lambda s:s._token_type)
    pos = property(lambda s:s._pos)
    row = property(lambda s:s._row)
    col = property(lambda s:s._col)

    def __repr__(self):
        return f"<{self.token_type}@{self.row}:{self.col} = {repr(self.value)}>"

class Lexer:
    def __init__(self):
        self.rules = []

    def add_rule(self, token_name, regex, props=None):
        if isinstance(regex, str):
            regex = RegularExpression(regex)
        self.rules.append((token_name, regex, props))

    @staticmethod
    def index_to_coordinates(s, index):
        """Returns (line_number, col) of `index` in `s`."""
        if not len(s):
            return 1, 1
        sp = s[:index+1].splitlines(keepends=True)
        return len(sp), len(sp[-1])

    def parse(self, text):
        index = 0
        tokens = []
        error = None
        while index<len(text):
            l = -1
            token_type = None
            token_props = None
            for rule in self.rules:
                l0 = rule[1].fa.find_longest_accepted_sequence_length(text, index)
                if l0>l:
                    l = l0
                    token_type = rule[0]
                    token_props = rule[2]
            coords = self.index_to_coordinates(text, index)
            if l<=0:
                error = f"Lexical error at {coords}: Invalid token"
                break
            tokens.append(LexicalToken(text[index:index+l], token_type, index, *coords, token_props))
            index+=l
        if error is None:
            return {"tokens":tokens, "success":True}
        return {"tokens":tokens, "success":False, "error":error}

