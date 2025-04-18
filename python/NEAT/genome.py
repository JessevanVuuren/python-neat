from .genome_history import *
from .gene import *
from .node import *
import random

import numpy as np


class Genome:
    def __init__(self, gh: GenomeHistory) -> None:
        self.genome_history = gh

        self.inputs = gh.inputs
        self.outputs = gh.outputs

        self.input_layer = 0
        self.output_layer = 10

        self.total_nodes = 0
        self.create_rate = .6

        self.nodes: list[Node] = []
        self.genes: list[Gene] = []

        self.fitness = random.uniform(0, 200)
        self.adjusted_fitness = 0.0

        for _ in range(self.inputs):
            self.nodes.append(Node(self.total_nodes, 0))
            self.total_nodes += 1

        for _ in range(self.outputs):
            self.nodes.append(Node(self.total_nodes, 1))
            self.total_nodes += 1

    def clone(self):
        clone = Genome(self.genome_history)
        clone.total_nodes = self.total_nodes
        clone.nodes.clear()
        clone.genes.clear()

        for i in range(len(self.nodes)):
            clone.nodes.append(self.nodes[i].clone())

        for i in range(len(self.genes)):
            clone.genes.append(self.genes[i].clone())

        clone.connect_genes()
        return clone

    def connect_nodes(self, n1: Node, n2: Node):
        n1_layer = n1.layer if n1.layer != 1 else 1000000
        n2_layer = n2.layer if n2.layer != 1 else 1000000

        if n1_layer > n2_layer:
            n1, n2 = n2, n1

        c = self.genome_history.exists(n1, n2)
        x = Gene(n1, n2)

        if c:
            x.innovation = c.innovation
            if not self.exists(x.innovation):
                self.genes.append(x)
        else:
            x.innovation = self.genome_history.global_innovation
            self.genome_history.global_innovation += 1
            self.genome_history.all_genes.append(x)
            self.genes.append(x)

    def add_gene(self):
        n1 = random.choice(self.nodes)
        n2 = random.choice(self.nodes)

        while n1.layer == n2.layer or (n2.layer == 0):
            n1 = random.choice(self.nodes)
            n2 = random.choice(self.nodes)

        self.connect_nodes(n1, n2)

    def mutate(self):
        if len(self.genes) == 0:
            self.add_gene()

        if random.random() < 0.8:
            for i in range(len(self.genes)):
                self.genes[i].mutate()
        if random.random() < 0.08:
            self.add_gene()
        if random.random() < 0.02:
            self.add_node()

    def get_node(self, n):
        for i in range(len(self.nodes)):
            if self.nodes[i].number == n:
                return self.nodes[i]
        print("Node not found : Something's Wrong ", n)
        return None

    def get_gene(self, innovation):
        for g in self.genes:
            if g.innovation == innovation:
                return g.clone()
        print("Gene not found")
        return None

    def connect_genes(self):

        for i in range(len(self.genes)):
            self.genes[i].in_node = self.get_node(self.genes[i].in_node.number)  # type: ignore
            self.genes[i].out_node = self.get_node(self.genes[i].out_node.number)  # type: ignore

        for i in range(len(self.nodes)):
            self.nodes[i].genes.clear()

        for i in range(len(self.genes)):
            self.genes[i].out_node.genes.append(self.genes[i])

    def get_outputs(self, inputs):
        if len(inputs) != self.inputs:
            print("Wrong number of inputs")
            return [-1]

        for i in range(self.inputs):
            self.nodes[i].output = inputs[i]

        self.connect_genes()

        for layer in range(2, self.genome_history.highest_hidden + 1):
            nodes_in_layer = []
            for n in range(len(self.nodes)):
                if self.nodes[n].layer == layer:
                    nodes_in_layer.append(self.nodes[n])

            for n in range(len(nodes_in_layer)):
                nodes_in_layer[n].calculate()

        final_outputs = []
        for n in range(self.inputs, self.inputs + self.outputs):
            self.nodes[n].calculate()
            final_outputs.append(self.nodes[n].output)

        return final_outputs

    def exists(self, nn):
        for c in self.genes:
            if c.innovation == nn:
                return True
        return False

    def get_weight(self, innovation):
        for g in self.genes:
            if g.innovation == innovation:
                return g.weight
        return -1

    def crossover(self, partner):
        child = Genome(self.genome_history)
        child.nodes.clear()

        try:
            p1_highest_innovation = max([(x.innovation) for x in self.genes])
        except Exception:
            p1_highest_innovation = 0

        try:
            p2_highest_innovation = max([(x.innovation) for x in partner.genes])
        except Exception:
            p2_highest_innovation = 0

        if self.total_nodes > partner.total_nodes:
            child.total_nodes = self.total_nodes
            for i in range(self.total_nodes):
                child.nodes.append(self.nodes[i].clone())
        else:
            child.total_nodes = partner.total_nodes
            for i in range(partner.total_nodes):
                child.nodes.append(partner.nodes[i].clone())

        highest_innovation = (
            p1_highest_innovation if self.fitness > partner.fitness else p2_highest_innovation
        )

        for i in range(highest_innovation + 1):
            e1 = self.exists(i)
            e2 = partner.exists(i)
            if e1 or e2:
                if e1 and e2:
                    gene = (
                        self.get_gene(i)
                        if (random.random()) < 0.5
                        else partner.get_gene(i)
                    )
                    child.genes.append(gene)  # type: ignore
                    continue
                if e1:
                    child.genes.append(self.get_gene(i))  # type: ignore
                if e2:
                    child.genes.append(partner.get_gene(i))

        child.connect_genes()
        return child

    def calculate_compatibility(self, partner):
        try:
            p1_highest_innovation = max([(x.innovation) for x in self.genes])
        except Exception:
            p1_highest_innovation = 0

        try:
            p2_highest_innovation = max([(x.innovation) for x in partner.genes])
        except Exception:
            p2_highest_innovation = 0

        if self.fitness > partner.fitness:
            highest_innovation = p1_highest_innovation
        else:
            highest_innovation = p2_highest_innovation

        matching = 0
        disjoint = 0
        excess = 0

        total_weights = 0
        average_weights = 0

        for i in range(highest_innovation + 1):
            e1 = self.exists(i)
            e2 = partner.exists(i)
            if e1 or e2:
                if e1 and e2:
                    matching += 1
                    total_weights += abs(self.get_weight(i)) + abs(partner.get_weight(i))
                    continue
                disjoint += 1

        average_weights = total_weights / (1 if matching == 0 else matching)

        for i in range(highest_innovation + 1, max(p1_highest_innovation, p2_highest_innovation) + 1):
            e1 = self.exists(i)
            e2 = partner.exists(i)
            if e1 or e2:
                excess += 1

        N = 1 if highest_innovation < 20 else highest_innovation

        c1 = 1.0
        c2 = 1.0
        c3 = 0.4

        E = c1 * excess / N
        D = c2 * disjoint / N
        W = c3 * average_weights

        delta = E + D + W

        return delta

    def add_node(self):
        if len(self.genes) == 0:
            self.add_gene()

        if random.random() < 0.2:
            self.genome_history.highest_hidden += 1

        n = Node(self.total_nodes, random.randint(2, self.genome_history.highest_hidden))
        self.total_nodes += 1

        g = random.choice(self.genes)
        l1 = g.in_node.layer
        l2 = g.out_node.layer
        if l2 == 1:
            l2 = 1000000

        while l1 > n.layer or l2 < n.layer:
            g = random.choice(self.genes)
            l1 = g.in_node.layer
            l2 = g.out_node.layer
            if l2 == 1:
                l2 = 1000000

        self.connect_nodes(g.in_node, n)
        self.connect_nodes(n, g.out_node)

        self.genes[-1].weight = 1.0
        self.genes[-2].weight = g.weight
        g.enabled = False
        self.nodes.append(n)
