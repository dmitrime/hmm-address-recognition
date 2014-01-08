from hmm import HMM
from hmm import viterbi
from collections import defaultdict
import numpy as np
from emissions import text_emissions

# 14 states, 12 emissions
address_states = {'background': 0,  'prefix1': 1, 'prefix2': 2, 'prefix3': 3, 'prefix4': 4, 
                  'target1': 5, 'target2': 6, 'target3': 7, 'target4': 8, 'target5': 9, 'suffix1': 10, 
                  'suffix2': 11, 'suffix3': 12, 'suffix4': 13}
address_states_debug = {'background': 'background',  'prefix1': 'prefix1', 'prefix2': 'prefix2', 'prefix3': 'prefix3', 
                        'prefix4': 'prefix4', 'target1': 'target1', 'target2': 'target2', 'target3': 'target3', 'target4': 
                        'target4', 'target5': 'target5', 'suffix1': 'suffix1', 'suffix2': 'suffix2', 'suffix3': 'suffix3', 
                        'suffix4': 'suffix4'}
address_emissions = {'default': 0, 'comma': 1, 'colon': 2, 'ziplike': 3, 
                     'phonelike': 4, 'purenumber': 5, 'containsnumber': 6, 'mailterm': 7, 
                     'roadname': 8, 'statename': 9, 'cityname': 10, 'startcap': 11}
address_emissions_debug = {'default': 'default', 'comma': 'comma', 'colon': 'colon', 'ziplike': 'ziplike', 'phonelike': 'phonelike', 
                           'purenumber': 'purenumber', 'containsnumber': 'containsnumber', 'mailterm': 'mailterm', 'roadname': 'roadname', 
                           'statename': 'statename', 'cityname': 'cityname', 'startcap': 'startcap'}

def label_states(emissions, apos, alen, emitstate):
    states = list()
    target = 1
    def target_state(emission, target):
        if address_emissions['purenumber'] == emission or address_emissions['containsnumber'] == emission:
            return 2
        elif address_emissions['comma'] == emission:
            return 3
        elif address_emissions['ziplike'] == emission:
            return 4
        elif target >= 4: # after the zip
            return 5
        return target

    for i in range(len(emissions)):
        if i < apos - 4 or i > apos+alen+4:
            state = 'background'
        elif i >= apos - 4 and i < apos:
            state = 'prefix%d' % (5 - (apos-i))
        elif i >= apos and i <= apos + alen:
            target = target_state(emissions[i], target)
            state = 'target%d' % target
            #print state, emissions[i]
        elif i > apos+alen and i <= apos+alen+4:
            state = 'suffix%d' % (i-apos-alen)
        states.append(emitstate[state])
    return states

def train_hmm(filename):
    Nstates, Nemissions = len(address_states), len(address_emissions)
    address_transition_probs = np.array([ [0.0]*Nstates for _ in range(Nstates) ]) 
    address_emission_probs = np.array([ [0.0]*Nemissions for _ in range(Nstates) ])

    count = 0
    state_count = defaultdict(int)
    for emissions, _, apos, adr in text_emissions(filename, address_emissions):
        states = label_states(emissions, apos, len(adr), address_states)

        for i in range(len(states) - 1):
            state_count[states[i]] += 1.
            address_transition_probs[ states[i] ][ states[i+1] ] += 1.
        for i in range(len(emissions)):
            address_emission_probs[ states[i] ][ emissions[i] ] += 1.
        count += 1
        if count >= 250:
            break

    for s in range(Nstates):
        if state_count[s] > 0:
            address_transition_probs[s] /= state_count[s]
            address_emission_probs[s] /= state_count[s]

    # do smoothing with absolute discounting
    for s in range(Nstates):
        v = len(address_emission_probs[s].nonzero()[0])
        p = 1. / (state_count[s] + v)
        for e in range(Nemissions):
            if address_emission_probs[s][e] > 0:
                address_emission_probs[s][e] -= p
            else:
                address_emission_probs[s][e] = v * p / (Nemissions - v)

    #print state_count
    #print address_transition_probs
    #print address_emission_probs
    return HMM(address_transition_probs, address_emission_probs)

def validation(hmm, filename):
    p = 1. / 6. # backround, prefix states and first target
    address_initial_dist = np.array([[p, p, p, p, p, p, 0, 0, 0, 0, 0, 0, 0, 0]])

    target_states = [v for k, v in address_states.items() if k.startswith('target')]
    for emissions, orig, pos, adr in text_emissions(filename, address_emissions):
        states = viterbi(hmm, address_initial_dist, emissions)
        #print states

        address, addresses = list(), list()
        for i in range(len(states)):
            if states[i] in target_states:
                address.append(orig[i])
            else:
                if len(address) > 1: 
                    addresses.append(' '.join([a for a in address if a]))
                    address = list()

        yield ' '.join(adr), addresses


if __name__ == '__main__':
    address_hmm = train_hmm('data/input.txt')

    count = 0
    for orig, found in validation(address_hmm, 'data/validation.txt'):
        print 'Given:', orig
        if len(found) > 0:
            for f in found:
                print 'Found:', f
        else:
            print '(None)'
        print 

        count += 1
        if count >= 30:
            break

