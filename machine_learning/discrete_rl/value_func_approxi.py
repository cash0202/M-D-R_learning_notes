import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn import linear_model as lin
from sklearn.preprocessing import PolynomialFeatures as Poly

'''
usage:
    get policy by sarsa method

arguments:
    env: return from package gym.make()
    track_branches: number of track samples
    epsilon: epsilon-greed method argument
    update_step: Temporal Difference(TD) update step width argument
    discount: gamma-discount cumulative reward argument
    poly: polinimial paraments

returns:
    policy: policy of env besed on track samples
    Q_table: state-action cumulative reward besed on track samples
    track_branches: number of track samples
    plt: matplotlib.pyplot object
'''
def linear_approxi_sarsa_1(env, track_branches=2000, epsilon=0.2, update_step=0.9, discount=0.9, poly=7):

    step = 0
    samples = pd.DataFrame(columns=['state', 'action', 'Q_value'])
    Q_xita = []

    def update_Qxita():
        x = Poly(degree=poly).fit_transform(np.array(samples)[:, [0, 1]])
        y = np.array(samples)[:, 2]
        # Q_table's approximation function is polyfit(x, y)
        Q_xita = lin.LinearRegression().fit(x, y)
        # Q_xita = lin.Ridge(alpha=0.5).fit(x, y)
        return Q_xita

    def Q_approxi(state, action):
        if Q_xita == []:
            return 0
        x1, x2 = np.asarray(state), np.asarray(action)
        sample_x = np.vstack((x1.reshape(1, -1), x2.reshape(1, -1))).T
        x = Poly(degree=poly).fit_transform(sample_x)
        return Q_xita.predict(x)

    # choose next action by argmax(a)[predict(x, a)]
    def predict_action(state):
        if Q_xita == []:
            return env.action_space.sample()
        x1, x2 = np.meshgrid(state, np.arange(env.action_space.n))
        Q_value = Q_approxi(x1, x2)
        max_q = np.max(Q_value)
        max_indexes = np.where(Q_value==max_q)[0]
        return np.random.choice(max_indexes)

    for track in range(track_branches):
        # first state
        state = env.reset()
        action = np.random.choice(env.action_space.n)

        # begin a track
        while True:
            # proceed epsilon-greed policy's action
            next_state, reward, done, _ = env.step(action)

            # next action generated by epsilon-greed policy
            if np.random.random() < epsilon:
                next_action = env.action_space.sample()
            else:
                next_action = predict_action(next_state)

            # get new Q_value
            Qvalue = Q_approxi(state, action) + update_step * (reward + discount*Q_approxi(next_state, next_action) - Q_approxi(state, action))
            # update samples
            samples.loc[step] = state, action, float(Qvalue)
            Q_xita = update_Qxita()

            step += 1
            if done:
                break
            # update state and action
            state = next_state
            action = next_action

    policy = np.zeros([16, 4])
    Q_table = np.zeros([16, 4])
    for state in range(env.observation_space.n):
        policy[state, predict_action(state)] = 1
        for action in range(env.action_space.n):
            Q_table[state, action] = Q_approxi(state, action)

    actions = ['left', 'down', 'right', 'up']
    fig = plt.figure(1)
    ax = fig.gca(projection='3d')
    ax.scatter(np.array(samples)[:, 0], np.array(samples)[:, 1], np.array(samples)[:, 2])
    for i in range(env.action_space.n):
        ax.plot(np.arange(16), np.ones(16)*i, Q_table[:, i], label=actions[i])
    ax.set_xlabel("state")
    ax.set_ylabel("action")
    ax.set_zlabel("Qvalue")
    fig.legend()

    return policy, Q_table, track_branches, plt


'''
usage:
    get policy by sarsa method

arguments:
    env: return from package gym.make()
    track_branches: number of track samples
    epsilon: epsilon-greed method argument
    discount: gamma-discount cumulative reward argument
    memory_size: the max saved samples
    minibatch: the minimal batch of samples used to training
    begin_step: the algorithm begin to study samples after begin_step
    update_step: update Q_xita every update_step
    update_target_step: update Q_xita_target every update_target_step
    poly: polinimial paraments

returns:
    policy: policy of env besed on track samples
    Q_table: state-action cumulative reward besed on track samples
    track_branches: number of track samples
    plt: matplotlib.pyplot object
'''
def linear_approxi_sarsa(env, track_branches=5000, epsilon=0.2, discount=0.9, memory_size=10000, 
        minibatch=2000, begin_step=2000, update_step=200, update_target_step=1000, poly=7):

    step = 0
    samples = np.zeros([memory_size, 4])
    Q_xita = []
    Q_xita_target = []

    def update_Qxita(sample_batch, Q_xita, Q_xita_target):
        states, actions, rewards, next_states = sample_batch[0:, :].T
        sample_x = np.vstack((states, actions)).T

        Q_now =  Q_approxi(states, actions, Q_xita).reshape(-1, 1)
        next_actions = np.zeros(next_states.shape)
        for i in range(next_states.size):
            next_actions[i] = predict_action(next_states[i], Q_xita_target)
        Q_next = Q_approxi(next_states, next_actions, Q_xita_target).reshape(-1, 1)
        terminal_befor_state_indexes = np.where(states.reshape(-1, 1) == 14)[0]
        terminal_indexes = terminal_befor_state_indexes[np.where(actions[terminal_befor_state_indexes] == 2)[0]]

        x = Poly(degree=poly).fit_transform(sample_x)
        y = rewards.reshape(-1, 1) + discount*Q_next - Q_now
        if terminal_indexes.size != 0:
            y[terminal_indexes, :] = rewards.reshape(-1, 1)[terminal_indexes, :]
        # Q_table's approximation function is polyfit(x, y)
        Q_xita = lin.LinearRegression().fit(x, y)
        #Q_xita = lin.Ridge(alpha=0.5).fit(x, y)
        return Q_xita

    def Q_approxi(state, action, Q_xita):
        if Q_xita == []:
            return np.zeros(np.size(state))
        x1, x2 = np.asarray(state), np.asarray(action)
        sample_x = np.vstack((x1.reshape(1, -1), x2.reshape(1, -1))).T
        x = Poly(degree=poly).fit_transform(sample_x)
        return Q_xita.predict(x)

    # choose next action by argmax(a)[Q_xita_target.predict(x, a)]
    def predict_action(state, Q_xita):
        if Q_xita == []:
            return env.action_space.sample()
        state, actions = np.meshgrid(state, np.arange(env.action_space.n))
        Q_value = Q_approxi(state, actions, Q_xita)
        max_q = np.max(Q_value)
        max_indexes = np.where(Q_value==max_q)[0]
        return np.random.choice(max_indexes)

    for track in range(track_branches):
        # first state
        state = env.reset()
        action = np.random.choice(env.action_space.n)

        # begin a track
        while True:
            # proceed epsilon-greed policy's action
            next_state, reward, done, _ = env.step(action)

            # next action generated by epsilon-greed policy
            if np.random.random() < epsilon:
                next_action = env.action_space.sample()
            else:
                next_action = predict_action(next_state, Q_xita)

            # save sample if over memory_size, recover it from index 0
            samples[step%memory_size, :] = state, action, reward, next_state
                
            # begin to learn
            if step >= begin_step and step % update_step == 0:
                random_indexes = np.random.randint(min(step, memory_size), size=[minibatch, 1])
                sample_batch = samples[random_indexes, :].reshape(-1, 4)
                Q_xita = update_Qxita(sample_batch, Q_xita, Q_xita_target)

                if step % update_target_step == 0:
                    Q_xita_target = Q_xita

            step += 1
            if done:
                break
            # update state and action
            state = next_state
            action = next_action

    policy = np.zeros([16, 4])
    Q_table = np.zeros([16, 4])
    for state in range(env.observation_space.n):
        for action in range(env.action_space.n):
            policy[state, predict_action(state, Q_xita)] = 1
            Q_table[state, action] = Q_approxi(state, action, Q_xita)

    actions = ['left', 'down', 'right', 'up']
    marker = ['^-', '.-', '+-', '*-']
    fig = plt.figure(1)
    ax = fig.gca(projection='3d')
    ax.scatter(samples[:, 0], samples[:, 1], samples[:, 2], color="black")
    for i in range(env.action_space.n):
        ax.plot(np.arange(16), np.ones(16)*i, Q_table[:, i], marker[i], label=actions[i])
    ax.set_xlabel("state")
    ax.set_ylabel("action")
    ax.set_zlabel("Qvalue")
    fig.legend()

    return policy, Q_table, step, plt
