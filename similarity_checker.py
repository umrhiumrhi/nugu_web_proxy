from num_for_check import *

class similarity_checker:
 
    def get_levenshtein_distance(self, s1, s2):
        m = len(s1)
        n = len(s2)
    
        dp = [[0 for _ in range(n+1)] for _ in range(m+1)]
        
        for i in range(1, m+1):
            dp[i][0] = i
        
        for i in range(1, n+1):
            dp[0][i] = i
            
        for i in range(1, m+1):
            for j in range(1, n+1):
                cost = 0 if s1[i-1] == s2[j-1] else 1
                dp[i][j] = min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + cost)
        
        return dp[m][n]
    
    def get_korean_levenshtein_distance(self, s1, s2):
        m = len(s1)
        n = len(s2)

        dp = [[0 for _ in range(n+1)] for _ in range(m+1)]
        
        for i in range(1, m+1):
            dp[i][0] = i
        
        for i in range(1, n+1):
            dp[0][i] = i
        
        for i in range(1, m+1):
            for j in range(1, n+1):
                cost = self.sub_cost(s1[i-1], s2[j-1])
                dp[i][j] = min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + cost)
        
        return dp[m][n]
        
    
    def check_korean(self, c):
        i = ord(c)
        return (i in range(KOR_BEGIN, KOR_END+1)) or (i in range(JAUM_BEGIN, JAUM_END+1)) or (i in range(MOUM_BEGIN, MOUM_END+1))
    
    def decompose(self, c):
        if self.check_korean(c) is False:
            return []
        
        i = ord(c)
        
        if i in range(JAUM_BEGIN, JAUM_END+1):
            return [c, ' ', ' ']
        
        if i in range(MOUM_BEGIN, MOUM_BEGIN+1):
            return [' ', c, ' ']
        
        i -= KOR_BEGIN
        
        cho = i // CHOSUNG_BASE
        joong = (i - cho * CHOSUNG_BASE) // JOONGSUNG_BASE
        jong = (i - cho * CHOSUNG_BASE - joong * JOONGSUNG_BASE)
        
        return [CHOSUNG_LIST[cho], JOONGSUNG_LIST[joong], JONGSUNG_LIST[jong]]
    
    def compose(self, cho, joong, jong):
        tmp = KOR_BEGIN + CHOSUNG_LIST.index(cho)*CHOSUNG_BASE + JOONGSUNG_LIST.index(joong)*JOONGSUNG_BASE + JONGSUNG_LIST.index(jong)
        
        return chr(tmp)

    def sub_cost(self, c1, c2):
        if c1 == c2: return 0.0
        if self.alphabet_check(c1) is True and self.alphabet_check(c2) is True :
            return self.get_levenshtein_distance(c1.lower(), c2.lower())
        elif self.alphabet_check(c1) is True or self.alphabet_check(c2) is True or c2.isdigit() or c1.isdigit() :
            return 1
        else: return self.get_levenshtein_distance(self.decompose(c1), self.decompose(c2)) / 3.0
        
    def find_similarity(self, s1, s2):
        if s1 == "" or s2 == "" : return -1
        
        result = -1
        max_length = max(len(s1), len(s2))
        
        if max_length > 0:
            result = (max_length - self.get_korean_levenshtein_distance(s1, s2)) / max_length
        else:
            result = 1
        
        return result
    
    def alphabet_check(self, c) :
        if 'a' <= c.lower() <= 'z':
            return True
        else : return False