# states = ['a','b','c','d','e','f','g','h','i','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','-']
import math
def initialPi(N):
    # pi is the initial state distribution, initial state distribution initialization
    pi = list()
    for i in range(N):
            pi.append(1/float(N))
    # print(pi)
    return pi

def initialTran(N):
    # A is the transition matrix, transition matrix initialization
    A = list()
    for i in range(N):
        a_sub = list()
        for j in range(N):
            a_sub.append(1/float(N))
        A.append(a_sub)
    # print(A)
    return A

def initialOb(N,M):
    # B is the observation matrix, observation matrix initialization
    B = list()
    for i in range(N):
        b_sub = list()
        for j in range(M):
            b_sub.append(1/float(M))
        B.append(b_sub)
    # print(B)
    return B

# def denomZero(denom, numer,M):
#     if denom == 0:
#         return numer+1/denom+M
#     else:
#         return numer/denom


class HMMImpl:
    # N = int(input())
    # M = int(input())
    # pi =initialPi(N)
    # A = initialTran(N)
    # B = initialOb(N,M)
    # # ob_seq = input().split()

    def __init__(self, A = [[0.7,0.3],[0.4,0.6]], B = [[0.1,0.4,0.5],[0.7,0.2,0.1]], pi = [0.3, 0.7]):

        self._initialA = A
        self._initialB = B
        self._initialPi = pi

    def _forward(self, A, B, pi, ob_seq):
        N = len(A)
        T = len(ob_seq)
        alp = list()

        # computing alp[0][i]
        c = []
        c.append(0)
        alp_row = list()
        for i in range(N):
            alp_row.append(pi[i] * (B[i][(ob_seq[0])]))
            c[0] += alp_row[i]
        alp.append(alp_row)

        # scaling alp[0][i]
        c[0] = 1 / c[0]
        for i in range(N):
            alp[0][i] = c[0] * alp[0][i]

        # computing Alp[t][i]
        for t in range(1, T):
            c.append(0)
            alp_row = list()
            for i in range(N):
                alp_row.append(0)
                for j in range(N):
                    alp_row[i] += (alp[t - 1][j]) * (A[j][i])
                alp_row[i] = (alp_row[i]) * (B[i][ob_seq[t]])
                c[t] += alp_row[i]
            alp.append(alp_row)

            # scale alp[t][i]
            # print('{}{}{}{}'.format("c[", t, "] ", c[t]))
            c[t] = 1 / c[t]
            # print('{}{}{}{}'.format("c[",t,"] ", c[t]))
            for i in range(N):
                alp[t][i] = c[t] * alp[t][i]

        return alp, c

    def _backward(self, A, B, ob_seq, c):

        N = len(A)
        T = len(ob_seq)
        beta = list()

        for i in range(T):
            beta_row = list()
            beta.append(beta_row)

        # scaling B by ct-1
        for i in range(N):
            beta[T - 1].append(c[T - 1])

        for t in list(reversed(range(T - 1))):
            # print(t)
            for i in range(N):
                beta[t].append(0)
                for j in range(N):
                    beta[t][i] += (A[i][j]) * (B[j][(ob_seq[t + 1])]) * (beta[t + 1][j])
                beta[t][i] = c[t] * beta[t][i]  # scaling beta[t][i] with the same scale factor as alp[t][i]

        return beta

    def _gamma(self, A, B, alp, ob_seq, beta):
        N = len(A)
        T = len(ob_seq)
        r = list()
        r_t = list()

        for t in range(T - 1):
            r_ij = list()
            denom = 0
            for i in range(N):
                for j in range(N):
                    denom += alp[t][i] * A[i][j] * B[j][ob_seq[t + 1]] * beta[t + 1][j]

            r_row = []

            for i in range(N):
                r_row.append(0)
                r_ij_row = []
                for j in range(N):
                    r_ij_row.append((alp[t][i] * A[i][j] * B[j][ob_seq[t + 1]] * beta[t + 1][j]) / denom)
                    # print(r_ij_row)
                    r_row[i] += r_ij_row[j]
                r_ij.append(r_ij_row)
            r.append(r_row)
            r_t.append(r_ij)
        # print(r_t)

        # special case
        denom = 0
        for i in range(N):
            denom += alp[T - 1][i]

        r_row = []
        for i in range(N):
            r_row.append(alp[T - 1][i] / denom)
        r.append(r_row)

        return r, r_t

    # re-estimation
    def _restimation(self, A, B, r, ob_seq, r_t):

        N = len(A)
        M = len(B)
        T = len(ob_seq)

        # re-estimating pi
        pi = [r[0][i] for i in range(N)]

        # re-estimating A
        for i in range(N):
            for j in range(N):
                numer = 0
                denom = 0
                for t in range(T - 1):
                    numer += r_t[t][i][j]
                    denom += r[t][i]
                A[i][j] = numer / denom

        # re-estimating B
        for i in range(N):
            for j in range(M):
                numer = 0
                denom = 0
                for t in range(T):
                    if ob_seq[t] == j:
                        numer += r[t][i]
                    denom += r[t][i]
                B[i][j] = numer / denom

        return A, B, pi

    def train(self, ob_seq, minIters, e):

        oldLogProb = 0
        iters = 0
        delta = float('inf')
        A = self._initialA
        B = self._initialB
        pi = self._initialPi
        T = len(ob_seq)

        while iters < minIters and delta > e:
            alp, c = self._forward(A, B, pi, ob_seq)
            beta = self._backward(A, B, ob_seq, c)
            r, r_t = self._gamma(A, B, alp, ob_seq, beta)
            (A, B, pi) = self._restimation(A, B, r, ob_seq, r_t)

            # Compute delta
            clogArr = [math.log(c[i]) for i in range(T)]
            logProb = sum(clogArr)
            logProb = -logProb
            delta = abs(logProb - oldLogProb)
            oldLogProb = logProb
            iters += 1
        print(iters)

        return A, B, pi


def main():
    A = [[0.7, 0.3], [0.4, 0.6]]
    B = [[0.1, 0.4, 0.5], [0.7, 0.2, 0.1]]
    pi = [0.3, 0.7]
    ob_seq = [1,0,2]
    print('{}{}'.format("Transition matrix A: ", A))
    print(('{}{}'.format("Observation matrix B: ",B)))
    print(('{}{}'.format("Initial Distribution matrix pi: ",pi)))

    ob = HMMImpl(A, B, pi)
    A, B, pi = ob.train(ob_seq, minIters = 100, e = 0.001)

    print('{}{}'.format("Transition matrix A: ", A))
    print(('{}{}'.format("Re Observation matrix B: ", B)))
    print(('{}{}'.format("Re Distribution matrix pi: ", pi)))

    for i in A:
        print(sum(i))
    for i in B:
        print(sum(i))


main()