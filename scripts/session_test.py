import pickle

with open('./session/session.pickle', 'rb') as f:
    load = pickle.load(f)
    print(load)
    f.close()
