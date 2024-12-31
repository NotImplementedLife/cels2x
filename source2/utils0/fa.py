"""

Text Finite Automata self-contained Python implementation.

Written by NotImpLife, version 9 November 2024.

With focus on efficiently handling transitions as character sequences 
instead of individual characters

Usage:

    - Define a charset:
        abc = Charset.range('a', 'c') # {'a', 'b', 'c'}
        digits = Charset.range('0', '9'))
        digits = Charset.digits() # preset
        greek_lower = Charset.range('α', 'ω') # works with UTF-8!
        not_digits = ~Charset.digits()
        digits_or_greek = digits + greek_lower # union!
        letter_without_abc = Charset.lower_alpha() - abc # except!
        ascii_intersect = letter_without_abc * Charset.range(0, 127) # intersection!

    - Create a finite automaton
        fa = TextFiniteAutomaton(CharTransitionsSet({
            ("Q0", Charset.digits()): ["Q1", "Q2"],
            ("Q1", Charset.digits()): ["Q1"],
            ("Q1", Charset.alpha()): ["Q2"],        
        }), "Q0", ["Q2"])
        
    - Make it deterministic:
        fa = fa.as_deterministic()
    
    - Combine Finite Automatas (regular expression like):
        union = fa1 + fa2
        concat = fa1 * fa2
        zero_or_many = fa1 ^ '*'
        one_or_many = fa1 ^ '+'
        repeat_3_times = fa1 ^ 3
    
    - Test sequences:
        # Check if the sequence is accepted by the FA (leads to final state):
        r = fa.is_accepted_sequence("123a") # True
        r = fa.is_accepted_sequence("123abc") # False
        # Get the length of the longest prefix that leads to a final state:
        r = fa.find_longest_accepted_sequence_length("123abc") # 4
        r = fa.find_longest_accepted_sequence_length("a99") # -1
"""

from __future__ import annotations
import sys
from collections import deque


class CharsRange:
    def __init__(self, start : str, end: str):
        if isinstance(start, str):
            assert(len(start)==1)
            self._start = ord(start)
        elif isinstance(start, int): self._start = start
        else: raise AttributeError("Invalid CharsRange start")
        if isinstance(end, str):
            assert(len(end)==1)
            self._end = ord(end)
        elif isinstance(end, int): self._end = end
        else: raise AttributeError("Invalid CharsRange end")
        self._length = max(0, self._end-self._start+1)
        
    def get_start(self)->int: return self._start
    def get_end(self)->int: return self._end
    def get_length(self)->int: return self._length
    
    start = property(get_start)
    end = property(get_end)
    length = property(get_length)

    def __repr__(self):
        if self.length==0: return "[]"
        if self.length==1: return f"[{repr(chr(self.start))}]" 
        return f"[{repr(chr(self.start))}, {repr(chr(self.end))}]"
        
    def contains(self, c:str)->bool:
        if isinstance(c, str):
            return self.start <= ord(c) <= self.end
        return False

    def __contains__(self, c:str)->bool: return self.contains(c)

    @staticmethod
    def _intersect(first:CharsRange, second: CharsRange) -> CharsRange:
        if first.length == 0 or second.length==0: return CharsRange.empty()
        if first.end < second.start or second.end < first.start: return CharsRange.empty()
        s = chr(max(first.start, second.start))
        e = chr(min(first.end, second.end))
        return CharsRange(s, e)
    
    @staticmethod
    def _union(first:CharsRange, second: CharsRange) -> list[CharsRange]:
        if first.length==0: return [second]
        if second.length==0: return [first]
        if CharsRange._intersect(first, second).length==0:
            if first.start > second.start:
                first, second = second, first
            if second.start == first.end+1:
                return [CharsRange(first.start, second.end)]
            return [first, second]            
        s = min(first.start, second.start)
        e = max(first.end, second.end)
        return [CharsRange(s, e)]
        
    @staticmethod
    def _except(first:CharsRange, second:CharsRange) -> list[CharsRange]:
        intersection = CharsRange._intersect(first, second)
        if intersection.length==0: return [first]
        left = CharsRange(first.start, intersection.start-1)
        right = CharsRange(intersection.end+1, first.end)
        return list(filter(lambda t:t.length>0, [left, right]))
    
    @staticmethod
    def _equals(self, other)-> bool:
        if not isinstance(other, CharsRange): return false
        return self.start==other.start and self.end==other.end and self.length==other.length    
    
    def __mul__(self, other:CharsRange): return CharsRange._intersect(self, other)
    def __rmul__(self, other:CharsRange): return CharsRange._intersect(other, self)
    
    def __add__(self, other:CharsRange) -> list[CharsRange]: return CharsRange._union(self, other)
    def __radd__(self, other:CharsRange) -> list[CharsRange]: return CharsRange._union(other, self)
    
    def __sub__(self, other:CharsRange) -> list[CharsRange]: return CharsRange._except(self, other)
    def __rsub__(self, other:CharsRange) -> list[CharsRange]: return CharsRange._except(other, self)
    
    def __eq__(self, other)-> bool: return CharsRange._equals(self, other)
    
    def __hash__(self): return hash((self.start, self.end, self.length))
    
    @staticmethod
    def empty(): return CharsRange('\u0001', '\u0000')    
    
class Charset:
    def __init__(self, ranges:list[CharsRange]):
        self._ranges = Charset._normalize_ranges(ranges)
        self._count = sum(map(lambda t:t.length, self._ranges))
        
    ranges = property(lambda s: s._ranges)
    count = property(lambda s: s._count)
        
    def __repr__(self): return f'{{{", ".join(map(str, self.ranges))}}} ({self.count} chars)'

    @staticmethod
    def _normalize_ranges(ranges:list[CharsRange])->list[CharsRange]:
        result = []
        for rng in sorted(ranges, key=lambda t:t.start):
            if rng.length==0: continue
            if len(result)==0:
                result.append(rng)
                continue  
            u = rng + result[-1]
            result.pop()
            result+=u            
        return result
    
    def contains(self, c:str)->bool:
        if isinstance(c, str):
            return any(map(lambda r:r.contains(c), self.ranges))
        return False
    
    def _except(self, other:Charset)->Charset:
        if len(self.ranges)==0: return Charset([])
        if len(other.ranges)==0: return self
        
        tmpRanges:list[CharsRange] = []
        difIndex:int = 0
        
        for rng in self.ranges:
            while difIndex<len(other.ranges) and other.ranges[difIndex].end<rng.start:
                difIndex+=1
            rgs = [rng]
            for i in range(difIndex, len(other.ranges)):
                if other.ranges[i].start > rng.end: break                
                rgs = list(map(lambda r:r - other.ranges[i], rgs))                                
                rgs = [item for lst in rgs for item in lst]                
            tmpRanges += rgs        
        return Charset(tmpRanges)
     
    def _intersect(self, other:Charset):
        tmpRanges: list[CharsRange] = []
        for r0 in self.ranges:
            for r1 in other.ranges:
                i = r0 * r1
                if i.length>0: tmpRanges.append(i)
        return Charset(tmpRanges)
        
    def equals(self, other)->bool:
        if not isinstance(other, Charset): return False
        if len(self.ranges)!=len(other.ranges): return False
        for i in range(len(self.ranges)):
            if self.ranges[i]!=other.ranges[i]: return False
        return True
        
    def complementary(self)->Charset: return Charset.all() - self
    
    def is_empty(self)->bool: return self.count==0
    
    def _union(self, other:Charset):
        return Charset(self.ranges + other.ranges)
        
    def __sub__(self, other:Charset)->Charset: 
        return self._except(other)
    
    def __mul__(self, other:Charset)->Charset:
        return self._intersect(other)
        
    def __add__(self, other:Charset)->Charset:
        return self._union(other)
        
    def __invert__(self)->Charset: return self.complementary()
    
    def __eq__(self, other:Charset)->bool:
        return self.equals(other)
        
    def __contains__(self, c): return self.contains(c)
    def __hash__(self): return sum(map(hash, self.ranges))
        
    @staticmethod
    def all(): return Charset([CharsRange(0, sys.maxunicode)])
        
        
    @staticmethod
    def lower_alpha(): return Charset([CharsRange('a', 'z')])
    
    @staticmethod
    def upper_alpha(): return Charset([CharsRange('A', 'Z')])
    
    @staticmethod
    def digits(): return Charset([CharsRange('0', '9')])    
    
    @staticmethod
    def alpha(): return Charset.lower_alpha() + Charset.upper_alpha()
    
    @staticmethod
    def alpha_num(): return Charset.alpha() + Charset.digits()
    
    @staticmethod
    def empty(): return Charset([])
        
    @staticmethod
    def single_char(c:str): return Charset([CharsRange(c,c)])
    
    @staticmethod
    def chars(chars:str): return Charset(list(map(lambda c:CharsRange(c,c), chars)))
   
    @staticmethod
    def range(c0:str, c1:str): return Charset([CharsRange(c0,c1)])
    
class CharTransitionsSet:
    def __init__(self, transitions: dict[tuple[any, Charset], list[any]]):
        self._transitions = {}
        for k,v in transitions.items(): self._transitions[k] = set(v)
        self._transitions = CharTransitionsSet.fix_disjoint_symbols_sets(self._transitions)
        
        states = []
        states += list(map(lambda t:t[0], transitions.keys()))
        for v in transitions.values():
            states += list(v)
        states = set(states)
        self._states = states
        self._is_deterministic = all(map(lambda t:len(t)<=1, self._transitions.values()))
    
    transitions = property(lambda s:s._transitions)
    states = property(lambda s:s._states)
    is_deterministic = property(lambda s:s._is_deterministic)
    
    def get_transitions(self, state:any, symbols:Charset)->list[any]:
        if (state, symbols) in self.transitions:
            return list(set(self.transitions[(state, symbols)]))
        return []
        
    def get_all_transitions(self, state:any)->list[tuple[Charset, list[any]]]|dict[tuple[any, Charset], list[any]]:
        if state is None: return self.transitions
        result=[]
        for q0, s in self.transitions.keys():
            if q0!=state: continue
            for v in self.transitions[q0, s]:
                result.append((s, v))
        return result
    
    def __repr__(self):
        return repr(self.transitions)
    
    @staticmethod
    def gather_sets(charsets:list[Charset])->tuple[list[Charset], dict[Charset, int]]:
        sets = list(set(charsets))
        index_map = dict(map(lambda u:u[::-1], enumerate(sets)))
        return sets, index_map
        
    @staticmethod
    def _enumerate_transitions(transitions:dict[tuple[any, Charset], list[any]]):
        for q0, s in transitions.keys():            
            yield q0, s, transitions[(q0, s)]
            
    @staticmethod
    def _enumerate_each_transition(transitions:dict[tuple[any, Charset], any]):
        for q0, s in transitions.keys():
            for q1 in transitions[(q0, s)]:
                yield q0, s, q1
        
    @staticmethod
    def fix_disjoint_symbols_sets(transitions):        
        def get_or_create_list(dct, key):
            if not key in dct: dct[key]=[]
            return dct[key]
            
        def get_many(dct, keys):            
            result = []
            for k in keys: result.append(dct[k])
            return result
        
        def enum_flatten(l): return [it for lst in l for it in lst]
            
        symbols = map(lambda t:t[1], transitions.keys())
        sets, index_set = CharTransitionsSet.gather_sets(symbols)        
        if len(index_set)==0: return transitions
        
        partitions_list = [sets[0]]
        partition_indices:list[list[int]] = [None] * len(sets)
        partition_indices[0] = [0]        
        reunion = sets[0]
        
        for i in range(1, len(sets)):
            part_ix:dict[int, list[int]] = {}
            new_partitions_list:list[Charset] = []
            partition_indices[i] = []
            
            for j, p in enumerate(partitions_list):
                s = p * sets[i]
                if not s.is_empty():
                    new_partitions_list.append(s)
                    get_or_create_list(part_ix, j).append(len(new_partitions_list)-1)
                    partition_indices[i].append(len(new_partitions_list)-1)
                s = p - sets[i]
                if not s.is_empty():
                    new_partitions_list.append(s)
                    get_or_create_list(part_ix, j).append(len(new_partitions_list)-1)
            s = sets[i] - reunion
            if not s.is_empty():
                new_partitions_list.append(s)
                partition_indices[i].append(len(new_partitions_list)-1)
            reunion = reunion + sets[i]
            for k in range(0,i):
                l = l0 = get_many(part_ix, partition_indices[k])
                l = list(enum_flatten(l))                
                partition_indices[k] = l
            partitions_list = new_partitions_list
        new_transitions = {}
        for q0, s, q1 in CharTransitionsSet._enumerate_transitions(transitions):            
            for part in get_many(partitions_list, partition_indices[index_set[s]]):
                get_or_create_list(new_transitions, (q0, part)).extend(q1)
        return new_transitions

class TextFiniteAutomaton:
    def __init__(self, transitions:CharTransitionsSet|dict, initial_state:any, final_states:list):
        self._transitions = transitions if isinstance(transitions, CharTransitionsSet) else CharTransitionsSet(transitions)
        self._initial_state = initial_state
        self._final_states = list(set(final_states))
        self._is_deterministic = self.transitions.is_deterministic
    
    transitions = property(lambda s:s._transitions) 
    initial_state = property(lambda s:s._initial_state)
    final_states = property(lambda s:s._final_states)
    is_deterministic = property(lambda s:s._is_deterministic)
    
    def __repr__(self):
        return f"InitialState: {self.initial_state}\n" \
            + f"FinalStates: {self.final_states}\n" \
            + f"Transitions: {self.transitions}"

    def _get_next_states(self, q0:any, c:str)->any:
        if len(c)!=1:
            raise ValueError("Token must be a single character")
        r = self.transitions.get_all_transitions(q0)
        r = filter(lambda t: c in t[0], r)
        r = map(lambda t:t[1], r)
        return list(set(r))
    
    def _get_next_state(self, q0:any, c:str)->any:
        states = self._get_next_states(q0, c)
        return states[0] if len(states)>0 else None
        
    def _validate_sequence_processing(self):
        if not self.is_deterministic:
            raise RuntimeError("Could not check a sequence against an NFA. Make the automaton deterministic first. Use the TextFiniteAutomaton.as_deterministic() method")

    def is_accepted_sequence(self, sequence:str)->bool:
        self._validate_sequence_processing()
        q = self.initial_state
        for c in sequence:
            q = self._get_next_state(q, c)
            if q is None: return False
        return q in self.final_states
    
    def find_longest_accepted_sequence_length(self, sequence:str, start_index:int=0)->int:
        self._validate_sequence_processing()
        if start_index<0:
            raise ValueError(f"Invalid access index {start_index}")
        q = self.initial_state
        max_len = 0 if q in self.final_states else -1
        steps = 0
        
        # print(f"Start {q}")
        i = start_index
        while i<len(sequence):
            q = self._get_next_state(q, sequence[i])
            # print(f"With {sequence[i]} --> {q}")
            if q is None: break
            if q in self.final_states: max_len = i + 1 - start_index
            steps+=1
            i+=1
        return max_len
        
    class AutomatonProps:
        def __init__(self, transitions = None, initial_state=None, final_states=None):
            if transitions is None: transitions = {}            
            if final_states is None: final_states = []
            self.transitions = transitions
            self.initial_state = initial_state
            self.final_states = final_states
            
        def add_transition(self, q0, s, q1):
            tr = self.transitions
            if not (q0,s) in tr: tr[(q0,s)]=[]
            if not q1 in tr[(q0,s)]:
                tr[(q0,s)].append(q1)

        def as_tuple(self): return self.transitions, self.initial_state, self.final_states
        
        def get_all_states(self)->list:
            states = [self.initial_state]
            states += self.final_states
            for q0, s in self.transitions.keys(): states.append(q0)
            for qs in self.transitions.values(): states += qs
            return list(set(states))        
        
        def drop_unreachable_states(self):
            transitions, initial_state, final_states = self.as_tuple()
            queue = deque([initial_state])
            visited = set([initial_state])
            result = {}
                        
            while len(queue) > 0:                
                q = queue.popleft()
                for (state, symbols), neighbors in transitions.items():                                        
                    if state!=q: continue                    
                    if not (state, symbols) in result:
                        result[(state, symbols)] = []
                    s = result[(state, symbols)]
                    for n in neighbors:
                        s.append(n)
                        if not n in visited:
                            visited.add(n)
                            queue.append(n)                
            result_final_states = set(final_states).intersection(visited)
            return TextFiniteAutomaton.AutomatonProps(result, initial_state, result_final_states)
        
        # var deadEndStates = states
        #   .Where(s => !d.Any(_ => object.Equals(_.Key.State, s)))
        #   .Except(finalStates).ToArray();
        
        @staticmethod
        def _get_dead_end_states(d, states, final_states):
            result = []
            for s in states:
                if not any(map(lambda t:t[0]==s, d.keys())):
                    if not s in final_states:
                        result.append(s)
            return result
        
        def drop_unproductive_states(self):
            states = self.get_all_states()
            d, initial_state, final_states = self.as_tuple()
            
            while True:
                dead_end_states= TextFiniteAutomaton.AutomatonProps._get_dead_end_states(d, states, self.final_states)
                if(len(dead_end_states)==0): break
                
                d1 = {}
                for k,v in d.items():
                    val = [x for x in v if not x in dead_end_states]
                    if len(val)>0: d1[k] = val
                d = d1
                states = [x for x in states if not x in dead_end_states]
            return TextFiniteAutomaton.AutomatonProps(d, initial_state, final_states)
            
        
    def as_deterministic(self):
        class StatesSet:
            def __init__(self, states): self.states = set(states)
            def __eq__(self, other):
                return isinstance(other, StatesSet) and len(self.states.symmetric_difference(other.states))==0
            def __hash__(self): return sum(map(hash, self.states))
            def __repr__(self): return f"StatesSet({', '.join(map(str, self.states))})"
            def intersection(self, other): return self.states.intersection(other.states)
        
    
        transitions = self.transitions
        initial_state = self.initial_state
        final_states = self.final_states
        
        charsets = list(set(map(lambda t:t[1], transitions.transitions)))
        
        new_states:set[StatesSet] = set()
        new_states_count = 0
        
        # deterministic automaton properties
        dap = TextFiniteAutomaton.AutomatonProps()
        dap.initial_state = StatesSet([initial_state])
        dap.final_states = list(map(lambda t:StatesSet([t]), final_states))        

        for q, s, qs in CharTransitionsSet._enumerate_transitions(transitions.transitions):
            q0 = StatesSet([q])            
            q1 = StatesSet(qs)            
            dap.add_transition(q0, s, q1)
            if len(qs)>1:
                if not q1 in new_states:
                    new_states.add(q1)
                    new_states_count+=1
        
        while new_states_count>0:
            tmp_states:set[StatesSet] = set()
            new_states_count = 0
            
            for q0 in new_states:
                if len(q0.states.intersection(final_states))>0:                    
                    dap.final_states.append(q0)
                for s in charsets:
                    q1 = []
                    for q in q0.states:                        
                        if (q, s) in transitions.transitions:                                 
                            q1.extend(transitions.transitions[(q, s)])
                    q1 = StatesSet(q1)                    
                    if len(q1.states)>1 and not q1 in new_states and not q1 in tmp_states:
                        tmp_states.add(q1)
                        new_states_count += 1
                    dap.add_transition(q0, s, q1)
            new_states = new_states.union(tmp_states)
            tmp_states.clear()                
        
        dap = dap.drop_unreachable_states()
        dap = dap.drop_unproductive_states()
        
        """
        print("_____________________")
        print("Transitions = ",dap.transitions)
        print("InitialState = ",dap.initial_state)
        print("FinalStates = ", dap.final_states)        
        dap = dap.drop_unreachable_states()
        print("_____________________")
        print("Transitions = ",dap.transitions)
        print("InitialState = ",dap.initial_state)
        print("FinalStates = ", dap.final_states)        
        dap = dap.drop_unproductive_states()
        print("_____________________")
        print("Transitions = ",dap.transitions)
        print("InitialState = ",dap.initial_state)
        print("FinalStates = ", dap.final_states)
        """
                
        return TextFiniteAutomaton(CharTransitionsSet(dap.transitions), dap.initial_state, dap.final_states)
     
    def _as_props(self):
        return TextFiniteAutomaton.AutomatonProps(self.transitions.transitions, self.initial_state, self.final_states)
     
    def _combine(self, combiner, other:TextFiniteAutomaton)->TextFiniteAutomaton:
        def props2fa(props):
            d, i, f = props.as_tuple()
            return TextFiniteAutomaton(CharTransitionsSet(d), i, f)
        d, i, f = props2fa(combiner(self._as_props(), other._as_props())).as_deterministic()._as_props().as_tuple()
        return TextFiniteAutomaton(CharTransitionsSet(d), i, f)
    
    def _transform(self, transformer) -> TextFiniteAutomaton:
        def props2fa(props):
            d, i, f = props.as_tuple()
            return TextFiniteAutomaton(CharTransitionsSet(d), i, f)
        d, i, f = props2fa(transformer(self._as_props())).as_deterministic()._as_props().as_tuple()
        return TextFiniteAutomaton(CharTransitionsSet(d), i, f)
        
    def pretty_print(self):
        print(f"InitialState: {self.initial_state}")
        print(f"FinalStates: {self.final_states}")
        print("Transitions:")
        for q0, s, q1 in CharTransitionsSet._enumerate_each_transition(self.transitions.transitions):
            print(f"  {q0}, {s} --> {q1}")
    
    class CummulativeStatePool:
        def __init__(self):
            self.states = {}
            self.next_id = 0
        
        def __getitem__(self, key): return self.states[key]
        
        def add_identical(self, keys):
            for key in keys:
                self.states[key] = self.next_id
            self.next_id+=1
        
        def add(self, key): self.states[key] = self.next_id; self.next_id+=1
    
    @staticmethod
    def transitions_union(ap1:TextFiniteAutomaton.AutomatonProps, ap2:TextFiniteAutomaton.AutomatonProps)->TextFiniteAutomaton.AutomatonProps:
        def get_many(dct, keys):            
            result = []
            for k in keys: result.append(dct[k])
            return result
    
        d1, q01, f1 = ap1.as_tuple()
        d2, q02, f2 = ap2.as_tuple()        
        
        ap = TextFiniteAutomaton.AutomatonProps()        
        
        d = {}
        Q1 = ap1.get_all_states(); Q1.remove(q01)
        Q2 = ap2.get_all_states(); Q2.remove(q02)
        
        state_pool = TextFiniteAutomaton.CummulativeStatePool()
        state_pool.add_identical([(1, q01), (2, q02)])
        
        for q in Q1: state_pool.add((1, q))
        for q in Q2: state_pool.add((2, q))
        
        for q0, s, q1 in CharTransitionsSet._enumerate_each_transition(d1):
            ap.add_transition(state_pool[1, q0], s, state_pool[1, q1])
        for q0, s, q1 in CharTransitionsSet._enumerate_each_transition(d2):
            ap.add_transition(state_pool[2, q0], s, state_pool[2, q1])
        ap.initial_state = state_pool[1, q01]        
        ap.final_states = get_many(state_pool, [(1, _) for _ in f1] + [(2, _) for _ in f2])
        return ap
        
    @staticmethod
    def transitions_concat(ap1:TextFiniteAutomaton.AutomatonProps, ap2:TextFiniteAutomaton.AutomatonProps)->TextFiniteAutomaton.AutomatonProps:
        d1, q01, f1 = ap1.as_tuple()
        d2, q02, f2 = ap2.as_tuple()
        
        ap = TextFiniteAutomaton.AutomatonProps()
        Q1 = ap1.get_all_states()
        Q2 = ap2.get_all_states()
        state_pool = TextFiniteAutomaton.CummulativeStatePool()
        
        for q in Q1: state_pool.add((1, q))
        for q in Q2: state_pool.add((2, q))
        
        used_states = set()
        def use(x): used_states.add(x); return x
        
        for q0, s, q1 in CharTransitionsSet._enumerate_each_transition(d1):
            ap.add_transition(use(state_pool[1, q0]), s, use(state_pool[1, q1]))
        
        for q0, s, q1 in CharTransitionsSet._enumerate_each_transition(d2):
            if q0 == q02:
                if q1 == q02:
                    for qf in f1:
                        ap.add_transition(use(state_pool[1, qf]), s, use(state_pool[1, qf]))
                else:
                    for qf in f1:
                        ap.add_transition(use(state_pool[1, qf]), s, use(state_pool[2, q1]))
            else:
                ap.add_transition(use(state_pool[2, q0]), s, use(state_pool[2, q1]))
        
        ap.final_states = list(set(map(lambda _:state_pool[2, _], f2)).intersection(used_states))
        if q02 in f2:
            ap.final_states += list(map(lambda _:state_pool[1, _], f1))
        ap.final_states = list(set(ap.final_states))
        ap.initial_state = state_pool[1, q01]
        return ap

    @staticmethod
    def zero_or_many_of(ap0:TextFiniteAutomaton.AutomatonProps)->TextFiniteAutomaton.AutomatonProps:
        d0, q0, f0 = ap0.as_tuple()
        ap = TextFiniteAutomaton.AutomatonProps()
        state_pool = TextFiniteAutomaton.CummulativeStatePool()
        
        Qs = ap0.get_all_states()
        for q in Qs: state_pool.add((0, q))
        
        newQ0 = (1, q0)
        state_pool.add(newQ0)
        
        for qi, s, qj in CharTransitionsSet._enumerate_each_transition(d0):
            if q0==qi:
                ap.add_transition(state_pool[newQ0], s, state_pool[0, qj])
                for qf in f0:
                    ap.add_transition(state_pool[0, qf], s, state_pool[0, qj])
            else:
                ap.add_transition(state_pool[0, qi], s, state_pool[0, qj])
        ap.final_states = list(map(lambda q:state_pool[0, q], f0)) + [state_pool[newQ0]]
        #print(ap.final_states)
        ap.initial_state = state_pool[newQ0]
        return ap
    
    @staticmethod
    def empty()->TextFiniteAutomaton:
        return TextFiniteAutomaton(CharTransitionsSet({}), "Q0", ["Q0"])
        
        
    def __mul__(self, other:TextFiniteAutomaton)->TextFiniteAutomaton:
        return self._combine(TextFiniteAutomaton.transitions_concat, other)
    
    def __add__(self, other:TextFiniteAutomaton)->TextFiniteAutomaton:
        return self._combine(TextFiniteAutomaton.transitions_union, other)
        
    def __xor__(self, modifier:int|str):
        if isinstance(modifier, str):
            if modifier=='*':
                return self._transform(TextFiniteAutomaton.zero_or_many_of)
            if modifier=='+':
                return self * self._transform(TextFiniteAutomaton.zero_or_many_of)
            raise ValueError("Invalid modifier. Must be '*' or '+'.")
        elif isinstance(modifier, int):
            if modifier>0:
                res = TextFiniteAutomaton.empty()
                for i in range(modifier):
                    res = res * self
                return res
            raise ValueError("Invalid modifier. Concatenate count must be non-negative")