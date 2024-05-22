class Converter:
    def __init__(self, StateSet, TerminalSet, DeltaFunc, StartState, FinalStateSet):
        self.StateSet = StateSet
        self.TerminalSet = TerminalSet
        self.DeltaFunc = DeltaFunc
        self.StartState = StartState
        self.FinalStateSet = FinalStateSet

    # epsilon을 보고 갈 수 있는 모든 상태를 리턴
    def epsilon_closure(self, StateSet): 
        closure = set(StateSet)
        stack = list(StateSet)
        while stack:
            state = stack.pop()
            for next_state in self.DeltaFunc.get((state, "ε"), []):
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)
        return closure

    # symbol을 보고 갈 수 있는 모든 상태를 리턴
    def move(self, StateSet, symbol): 
        next_states = set()
        for state in StateSet:
            next_states.update(self.DeltaFunc.get((state, symbol), []))
        return next_states       
    
    # IAS가 제거된 DFA로 변환
    def convert_to_dfa(self): 
        dfa_StateSet = [self.epsilon_closure({self.StartState})]
        dfa_DeltaFunc = {}
        dfa_StartState = dfa_StateSet[0]
        dfa_FinalStateSet = []
        state_index_map = {}
        stack = [dfa_StartState]
        state_index = 0
        # stack에서 pop하여 다음 상태 집합 구하기, 그 상태도 stack에 push하여 반복
        while stack:
            current_dfa_state = stack.pop()
            # 치환을 위해 state_index_map 생성하여 상태 집합, 상태 이름 매핑
            if frozenset(current_dfa_state) not in state_index_map:
                state_index_map[frozenset(current_dfa_state)] = "q" + str(state_index).zfill(3)
                print("   - q" + str(state_index).zfill(3),'=',current_dfa_state)
                state_index += 1
            # 각 symbol에 대해 다음 상태 집합 구하기
            for symbol in self.TerminalSet:
                next_nfa_state = self.move(current_dfa_state, symbol)
                epsilon_closure = self.epsilon_closure(next_nfa_state)
                if epsilon_closure:
                    if epsilon_closure not in dfa_StateSet:
                        # 치환을 위해 state_index_map 생성하여 상태 집합, 상태 이름 매핑
                        if frozenset(epsilon_closure) not in state_index_map:
                            state_index_map[frozenset(epsilon_closure)] = "q" + str(state_index).zfill(3)
                            print("   - q" + str(state_index).zfill(3),'=',epsilon_closure)
                            state_index += 1
                        # 새로운 상태 집합이면 stack에 push
                        dfa_StateSet.append(epsilon_closure)
                        stack.append(epsilon_closure)
                    dfa_DeltaFunc[(state_index_map[frozenset(current_dfa_state)], symbol)] = state_index_map[frozenset(epsilon_closure)]
        # nfa의 FinalStateSet을 포함하는 dfa_state에 대해 FinalStateSet 생성
        for dfa_state in dfa_StateSet:
            if dfa_state.intersection(self.FinalStateSet):
                dfa_FinalStateSet.append(state_index_map[frozenset(dfa_state)])
        return DFA(set(state_index_map.values()), self.TerminalSet, dfa_DeltaFunc, state_index_map[frozenset(dfa_StartState)], set(dfa_FinalStateSet))

class DFA:
    def __init__(self, StateSet, TerminalSet, DeltaFunc, StartState, FinalStateSet):
        self.StateSet = StateSet
        self.TerminalSet = TerminalSet
        self.DeltaFunc = DeltaFunc
        self.StartState = StartState
        self.FinalStateSet = FinalStateSet

    def minimize(self): # minimized DFA로 변환
        # final, non-final 상태로 나누기
        P = [set(self.FinalStateSet), set(self.StateSet) - set(self.FinalStateSet)]
        W = [set(self.FinalStateSet), set(self.StateSet) - set(self.FinalStateSet)]
        # 각 symbol에 대해서 같은 그룹인지 확인
        while W:
            A = W.pop(0)
            if len(A) == 1:
                continue
            for c in self.TerminalSet:
                new_state_map = {}
                for s in A:
                    # c로 이동한 상태가 없는 경우에는 reduce할 수 없음
                    if self.DeltaFunc.get((s,c)) == None: 
                        return self
                    new_state_map[s] = self.DeltaFunc.get((s,c)) in A
                X = set()
                Y = set()    
                for s, x in new_state_map.items():
                    if x:
                        X.add(s)
                    else:
                        Y.add(s)
                if X == A or Y == A:
                    continue    
                else:   
                    P.remove(A)
                    if X:
                        P.append(X)
                        W.append(X)
                    if Y:
                        P.append(Y)
                        W.append(Y)    
                    break

        # minimized DFA가 아닌 경우
        if len(P) == len(self.StateSet): 
            return self
        
        minimized_DeltaFunc = {}
        minimized_StateSet = set()
        minimized_StartState = None
        minimized_FinalStateSet = set()
        state_map = {}
        
        # minimized_StateSet, StartSet, FinalStateSet 생성
        # minimized_DeltaFunc 생성을 위해 state_map 생성
        for group in P:
            minimized_StateSet.add(frozenset(group))
            state_map.update({s: group for s in group})
            if self.StartState in group:
                minimized_StartState = group
            if group.intersection(self.FinalStateSet):
                minimized_FinalStateSet.add(frozenset(group))
        
        # minimized_DeltaFunc 생성
        for s in minimized_StateSet:
            for c in self.TerminalSet:
                for s2 in s:
                    original_states = state_map[s2]
                next_states = set()
                for original_state in original_states:
                    if self.DeltaFunc.get((original_state, c)): 
                        next_states.add(self.DeltaFunc.get((original_state, c)))
                next_state = state_map[next_states.pop()] if next_states else None
                if next_state:
                    minimized_DeltaFunc[(s, c)] = next_state
        
        # minimized DFA 객체 생성
        minimized_dfa = DFA([set(x) for x in minimized_StateSet], self.TerminalSet, minimized_DeltaFunc, minimized_StartState, [set(x) for x in minimized_FinalStateSet])
        return minimized_dfa

# FA 정보를 파일로 저장
def write_dfa_info(filename, dfa, r_dfa): 
    with open(filename, 'w') as f:
        f.write("* DFA 정보\n")
        f.write("StateSet = {{{}}}\n".format(','.join(map(str, dfa.StateSet))))
        f.write("TerminalSet = {{{}}}\n".format(','.join(map(str, dfa.TerminalSet))))
        f.write("DeltaFunctions = {\n")
        for transition, next_state in dfa.DeltaFunc.items():
            f.write("   ({},{}) = {}\n".format(transition[0], transition[1], next_state if next_state else 'Φ'))
        f.write("}\n")
        f.write("StartState = {}\n".format(dfa.StartState))
        f.write("FinalStateSet = {{{}}}\n".format(','.join(map(str, dfa.FinalStateSet)))) 

        f.write("\n\n* reduced_DFA 정보\n")
        if dfa != reduced_dfa: # dfa, r_dfa가 다른 경우에만 reduced_DFA 정보를 저장
            f.write("StateSet = {{{}}}\n".format(','.join(map(str, r_dfa.StateSet))))
            f.write("TerminalSet = {{{}}}\n".format(','.join(map(str, r_dfa.TerminalSet))))
            f.write("DeltaFunctions = {\n")
            for transition, next_state in r_dfa.DeltaFunc.items():
                f.write("   ({},{}) = {}\n".format(set(transition[0]), transition[1], next_state if next_state else 'Φ'))
            f.write("}\n")
            f.write("StartState = {}\n".format(r_dfa.StartState))
            f.write("FinalStateSet = {{{}}}\n".format(','.join(map(str, r_dfa.FinalStateSet)))) 
        else:
            f.write("DFA의 상태들이 모두 indistinguishable함.")     

########################################
### (ε-)NFA -> reduced_DFA CONVERTER ###
########################################

## 입력 파일 이름
input_file_name = '여기에 파일 이름 입력'
StateSet = set()
TerminalSet = set()
DeltaFunc = {}
FinalStateSet = set()

## 입력 파일 parsing
with open(input_file_name + '.txt', 'r') as file:
    lines = file.readlines()

for idx, line in enumerate(lines):
    parts = line.strip().split()
    if parts[0] == 'StateSet':
        StateSet = set(parts[2][1:-1].split(','))  
    elif parts[0] == 'TerminalSet':
        TerminalSet = set(parts[2][1:-1].split(','))  
    elif parts[0] == 'DeltaFunctions':
        while True:
            idx += 1
            next_line = lines[idx]
            parts = next_line.strip().split()
            if parts[0] == '}':
                break
            parts_list = parts[0][1:-1].split(',')
            state, symbol = parts_list
            next_states = set(parts[2][1:-1].split(','))
            DeltaFunc[(state, symbol)] = next_states
    elif parts[0] == 'StartState':
        StartState = parts[2]
    elif parts[0] == 'FinalStateSet':
        FinalStateSet = set(parts[2][1:-1].split(','))
    else:
        continue

# 입력받은 NFA 정보로 변환기 객체 생성, dfa, reduced_dfa 생성 후 파일로 저장
nfa = Converter(StateSet, TerminalSet, DeltaFunc, StartState, FinalStateSet)

# NFA를 DFA로 변환
dfa = nfa.convert_to_dfa() 
# DFA를 reduced_DFA로 변환
reduced_dfa = dfa.minimize()
# 파일로 저장
write_dfa_info("FA_INFO({}).txt".format(input_file_name), dfa, reduced_dfa)