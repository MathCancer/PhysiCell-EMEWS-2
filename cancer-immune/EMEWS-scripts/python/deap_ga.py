import threading
import random
import time
import math
import csv
import json
import sys
import time
import pickle

import stats as sts

from deap import base
from deap import creator
from deap import tools
from deap import algorithms

import eqpy, ga_utils

# list of ga_utils parameter objects
transformer = None


class Transformer:

    def __init__(self, ga_params, clf = None, scaler = None):
        self.ga_params = ga_params

    def check_constraint(self, pt):
        return True

    def mutate(self, population, indpb):
        """
        Mutates the values in list individual with probability indpb
        """

        # Note, if we had some aggregate constraint on the individual
        # (e.g. individual[1] * individual[2] < 10), we could copy
        # individual into a temporary list and mutate though until the
        # constraint was satisfied
        for i, param in enumerate(self.ga_params):
            individual = param.mutate(population[i], mu=0, indpb=indpb)
            for _ in range(100):
                if self.check_constraint(individual):
                    break
                individual = param.mutate(population[i], mu=0, indpb=indpb)
            
            population[i] = individual

        return population,

    def cxUniform(self, ind1, ind2, indpb):
        for _ in range(100):
            c1, c2 = tools.cxUniform(ind1, ind2, indpb)
            if self.check_constraint(c1) and self.check_constraint(c2):
                break

        return (c1, c2)

    def random_params(self):
        draws = []
        for p in self.ga_params:
            draws.append(p.randomDraw())

        return draws

    def parse_init_params(self, params_file):
        init_params = []
        with open(params_file) as f_in:
            reader = csv.reader(f_in)
            header = next(reader)
            for row in reader:
                init_params.append(dict(zip(header,row)))
        return init_params

    def update_init_pop(self, pop, params_file):
    
        printf("Reading initial population from {}".format(params_file))
        init_params = self.parse_init_params(params_file)
        if len(pop) > len(init_params):
            raise ValueError("Not enough initial params to set the population: size of init params < population size")

        # first 12 are best ones
        sampled_params = init_params[0:12]
        sample_size = len(pop) - 12
        if sample_size > 0:
            sampled_params = sampled_params + random.sample(init_params[12:], sample_size)
        for i, indiv in enumerate(pop):
            for j, param in enumerate(self.ga_params):
                indiv[j] = param.parse(sampled_params[i][param.name])

class ConstrainingTransformer(Transformer):

    def __init__(self, ga_params, clf, scaler):
        Transformer.__init__(self, ga_params)
        self.clf = clf
        self.scaler = scaler

    def check_constraint(self, pt):
        spt = self.scaler.transform([pt])
        res = self.clf.predict(spt)
        return res == 0
        
def printf(val):
    print(val)
    sys.stdout.flush()

def obj_func(x):
    return 0

# {"batch_size":512,"epochs":51,"activation":"softsign",
#"dense":"2000 1000 1000 500 100 50","optimizer":"adagrad","drop":0.1378,
#"learning_rate":0.0301,"conv":"25 25 25 25 25 1"}
def create_list_of_json_strings(list_of_lists, super_delim=";"):
    # create string of ; separated jsonified maps
    res = []
    global transformer
    for l in list_of_lists:
        jmap = {}
        for i,p in enumerate(transformer.ga_params):
            jmap[p.name] = l[i]

        jstring = json.dumps(jmap)
        res.append(jstring)

    return (super_delim.join(res))

def create_fitnesses(params_string):
    """return equivalent length tuple list
    :type params_string: str
    """
    params = params_string.split(";")
    # get length
    res = [(i,) for i in range(len(params))]
    return (res)

def queue_map(obj_func, pops):
    # Note that the obj_func is not used
    # sending data that looks like:
    # [[a,b,c,d],[e,f,g,h],...]
    if not pops:
        return []

    eqpy.OUT_put(create_list_of_json_strings(pops))
    result = eqpy.IN_get()
    split_result = result.split(';')
    # TODO determine if max'ing or min'ing and use -9999999 or 99999999
    return [(float(x),) if not math.isnan(float(x)) else (float(99999999),) for x in split_result]
    
    #return [(float(x),) for x in split_result]

def make_random_params():
    """
    Performs initial random draw on each parameter
    """
    return transformer.random_params()
    # global ga_params

    # draws = []
    # for p in ga_params:
    #     draws.append(p.randomDraw())

    # return draws

def update_init_pop(pop, params_file):
    transformer.update_init_pop(pop, params_file)
    # global ga_params
    # printf("Reading initial population from {}".format(params_file))
    # init_params = parse_init_params(params_file)
    # if len(pop) > len(init_params):
    #     raise ValueError("Not enough initial params to set the population: size of init params < population size")

    # # first 12 are best ones
    # sampled_params = init_params[0:12]
    # sample_size = len(pop) - 12
    # if sample_size > 0:
    #     sampled_params = sampled_params + random.sample(init_params[12:], sample_size)
    # for i, indiv in enumerate(pop):
    #     for j, param in enumerate(ga_params):
    #         indiv[j] = param.parse(sampled_params[i][param.name])

# keep as reference for log type
# def mutGaussian_log(x, mu, sigma, mi, mx, indpb):
#     if random.random() < indpb:
#         logx = math.log10(x)
#         logx += random.gauss(mu, sigma)
#         logx = max(mi, min(mx, logx))
#         x = math.pow(10, logx)
#     return x

# Returns a tuple of one individual
def custom_mutate(individual, indpb):
    """
    Mutates the values in list individual with probability indpb
    """
    return transformer.mutate(individual, indpb)

    # # Note, if we had some aggregate constraint on the individual
    # # (e.g. individual[1] * individual[2] < 10), we could copy
    # # individual into a temporary list and mutate though until the
    # # constraint was satisfied

    # global ga_params
    # for i, param in enumerate(ga_params):
    #     individual[i] = param.mutate(individual[i], mu=0, indpb=indpb)

    # return individual,

def cxUniform(ind1, ind2, indpb):
    return transformer.cxUniform(ind1, ind2, indpb)
    # c1, c2 = tools.cxUniform(ind1, ind2, indpb)
    # return (c1, c2)

def timestamp(scores):
    return str(time.time())

def create_transformer(ga_params, classifier_path, scaler_path):
    global transformer
    if classifier_path == "":
        transformer = Transformer(ga_params)
    else:
        with open(classifier_path, 'rb') as f_in:
            clf = pickle.load(f_in)

        with open (scaler_path, 'rb') as f_in:
            scaler = pickle.load(f_in)
        
        transformer = ConstrainingTransformer(ga_params, clf, scaler)

def run():
    """
    :param num_iter: number of generations
    :param num_pop: size of population
    :param seed: random seed
    :param strategy: one of 'simple', 'mu_plus_lambda'
    :param ga parameters file name: ga parameters file name (e.g., "ga_params.json")
    :param param_file: name of file containing initial parameters
    """
    eqpy.OUT_put("Params")
    params = eqpy.IN_get()

    # parse params
    (num_iter, num_pop, seed, strategy, mut_prob, ga_params_file, param_file, classifer_path, scaler_path) = eval('{}'.format(params))
    random.seed(seed)
    ga_params = ga_utils.create_parameters(ga_params_file)
    create_transformer(ga_params, classifer_path, scaler_path)

    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMin)
    toolbox = base.Toolbox()
    toolbox.register("individual", tools.initIterate, creator.Individual,
                     make_random_params)

    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", obj_func)
    toolbox.register("mate", cxUniform, indpb=0.5)
    mutate_indpb = mut_prob
    toolbox.register("mutate", custom_mutate, indpb=mutate_indpb)
    toolbox.register("select", tools.selTournament, tournsize=3)
    toolbox.register("map", queue_map)

    pop = toolbox.population(n=num_pop)
    if param_file != "":
        update_init_pop(pop, param_file)

    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", sts.mean)
    stats.register("std", sts.std)
    stats.register("min", sts.min)
    stats.register("max", sts.max)
    stats.register("ts", timestamp)

    # num_iter-1 generations since the initial population is evaluated once first
    mutpb = mut_prob
    start_time = time.time()
    if strategy == 'simple':
        pop, log = algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=mutpb, ngen=num_iter - 1,
                                   stats=stats, halloffame=hof, verbose=True)
    elif strategy == 'mu_plus_lambda':
        mu = int(math.floor(float(num_pop) * 0.5))
        lam = int(math.floor(float(num_pop) * 0.5))
        if mu + lam < num_pop:
            mu += num_pop - (mu + lam)

        pop, log = algorithms.eaMuPlusLambda(pop, toolbox, mu=mu, lambda_=lam,
                                             cxpb=0.5, mutpb=mutpb, ngen=num_iter - 1,
                                             stats=stats, halloffame=hof, verbose=True)
    else:
        raise NameError('invalid strategy: {}'.format(strategy))

    end_time = time.time()

    fitnesses = [str(p.fitness.values[0]) for p in pop]

    eqpy.OUT_put("DONE")
    # return the final population
    eqpy.OUT_put("{}\n{}\n{}\n{}\n{}".format(create_list_of_json_strings(pop), ';'.join(fitnesses),
        start_time, log, end_time))
