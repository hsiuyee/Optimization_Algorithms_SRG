# refer to: Stochastic Reweighted Gradient Descent - https://proceedings.mlr.press/v162/hanchi22a.html
#           Estimating Convergence of Markov chains with L-Lag Couplings - https://proceedings.neurips.cc/paper_files/paper/2019/file/aec851e565646f6835e915293381e20a-Paper.pdf

import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
    
def f(x):
    # f_i(x) = (x - a_i) ^ 2 / 2
        # a_i = 1 if i = n - 1
        # a_i = 0 else
        # n = 20
    n = tf.shape(x)[0]
    a = tf.zeros_like(x)
    a = tf.tensor_scatter_nd_update(a, [[n-1]], [1]) 
    diff = x - a
    return tf.reduce_sum(tf.square(diff) / 2)


def compute_gradient(f, x_k, i_k):
    n = tf.shape(x_k)[0]
    a = tf.zeros_like(x_k)
    a = tf.tensor_scatter_nd_update(a, [[n-1]], [1]) 
    
    result_vector = tf.tensor_scatter_nd_update(
        tf.zeros_like(x_k),
        [[i_k]],
        [x_k[i_k] - a[i_k]]
    )
    return result_vector


# ------------------------------------------------------------------------------------------------ modify
def maximally_couples(p, q, n):
    # step 1: initial
    X_star = np.random.choice(np.arange(n), p=p)
    W = np.random.uniform(0, 1)

    #step 2
    if p[X_star] * W <= q[X_star]: # case 1
        Y_star = X_star
        return (X_star, Y_star)
    else:                          # case 2        
        Y_hat = np.random.choice(np.arange(n), p=q)
        W_hat = np.random.uniform(0, 1)
        while (q[Y_hat] * W_hat > p[Y_hat]):
            Y_hat = np.random.choice(np.arange(n), p=q)
            W_hat = np.random.uniform(0, 1)
        Y_star = Y_hat
        return X_star, Y_star
# ------------------------------------------------------------------------------------------------ modify


def SRG_plus(num_iterations=10000, d=20, n=20):
    # default
    x_star = tf.Variable([1 / n for i in range(n)])

    # step 1: Parameters
    alpha = np.linspace(1 / 24, 1 / 24, num_iterations)
    theta = np.linspace(0.5, 0.5, num_iterations) 

    # step 2: Initialization
    x_old = tf.Variable(tf.random.normal([d], dtype=tf.float32))
    g_old = [tf.random.normal([n], dtype=tf.float32) for _ in range(n)]
    g_old_norm = tf.Variable([tf.norm(g) for g in g_old], dtype=tf.float32)

    # step 3: iteration
    gradient_list = []
    error_list = []

    for k in range(num_iterations):
        # step 4: update pk
            # L_1 = n - 1
            # L_n = 1 / n
            # L_i = (n - 1) / (n * (n - 2))
            # L_bar = 1
            # L_max = n - 1
        L = [(n - 1) / (n * (n - 2)) for i in range(n)]
        L[0] = n - 1
        L[-1] = 1 / n

        L_bar = 1
        v = tf.Variable([L_i / (n * L_bar) for L_i in L])
        w = tf.Variable([1 / n for i in range(n)])
        q_k = tf.cast(g_old_norm / tf.reduce_sum(g_old_norm), tf.float32).numpy()
        p_k = (1 - theta[k]) * q_k + theta[k] * v

        # step 5: update bk
        b_k = np.random.binomial(n=1, p=theta[k])

        # step 6: update ik
        if b_k == 1:
            i_k, j_k = maximally_couples(v.numpy(), w.numpy(), n)
        else:
            i_k = np.random.choice(np.arange(n), p=q_k)


        # step 7: update x_{k+1}
        gradient = compute_gradient(f, x_old, i_k)
        x_new = x_old - alpha[k] * gradient / (n * p_k[i_k])
        gradient_list.append(gradient)
        error_list.append(tf.reduce_sum(tf.square(f(x_new) - f(x_star))))

        # step 8: update g_k_{j+1}
        g_new_norm = tf.Variable(tf.zeros(n, dtype=tf.float32))
        for j in range(n):
            if b_k == 1 and j == j_k:
                g_new_norm[j].assign(tf.norm(compute_gradient(f, x_old, j)))
            else:
                g_new_norm[j].assign(g_old_norm[j])

        # update
        x_old.assign(x_new)
        g_old_norm.assign(g_new_norm)

    # draw
    plt.plot(range(num_iterations), error_list)
    plt.xlabel('Iteration')
    plt.ylabel('Error')
    plt.title('Error over Iterations')
    plt.show()

if __name__ == '__main__':
    SRG_plus()