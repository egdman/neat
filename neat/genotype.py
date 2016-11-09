import yaml
from copy import copy, deepcopy




def unicode_representer(dumper, data):
    return dumper.represent_scalar(u'tag:yaml.org,2002:str', data)



class Gene(object):

    def __init__(self, gene_type, historical_mark=0, enabled=True, **params):
        self.gene_type = gene_type
        self.params = params
        self.historical_mark = historical_mark
        self.enabled = enabled


    def copy_params(self):
        return deepcopy(self.params)


    def get_param(self, param_name):
        return self.params[param_name]


    def set_param(self, param_name, param_value):
        self.params[param_name] = param_value


    def __getitem__(self, key):
        return self.get_param(key)


    def __setitem__(self, key, value):
        self.set_param(key, value)


    def get_type(self):
        return self.gene_type


    def copy(self):
        return deepcopy(self)




class NeuronGene(Gene):

    def __init__(self, neuron_type, historical_mark=0, enabled=True, **params):
        super(NeuronGene, self).__init__(neuron_type, historical_mark, enabled, **params)


    neuron_type = property(Gene.get_type)


    def __str__(self):
        return "NEAT Neuron gene, mark: {}, type: {}".format(self.historical_mark, self.neuron_type)





class ConnectionGene(Gene):

    def __init__(self, connection_type, mark_from, mark_to, historical_mark=0, enabled=True, **params):
        super(ConnectionGene, self).__init__(connection_type, historical_mark, enabled, **params)
        self.mark_from  = mark_from
        self.mark_to    = mark_to

    connection_type = property(Gene.get_type)

    def __str__(self):
        return "NEAT Connection gene, mark: {}, type: {}, from: {}, to: {}".format(
            self.historical_mark,
            self.connection_type,
            self.mark_from,
            self.mark_to
        )





class GeneticEncoding:
    
    def __init__(self, neuron_genes=[], connection_genes=[]):
        self.neuron_genes = neuron_genes
        self.connection_genes = connection_genes
    

    
    def num_genes(self):
        return len(self.neuron_genes) + len(self.connection_genes)



    def num_neuron_genes(self):
        return len(self.neuron_genes)



    def num_connection_genes(self):
        return len(self.connection_genes)



    def get_connection_genes(self, mark_from, mark_to):
        return [c_g for c_g in self.connection_genes if c_g.mark_from == mark_from and c_g.mark_to == mark_to]
    
    

    @staticmethod
    def get_dissimilarity(genotype1, genotype2, excess_coef=1., disjoint_coef=1., weight_diff_coef=0.):
        excess_num, disjoint_num = GeneticEncoding.get_excess_disjoint(genotype1, genotype2)
        num_genes = max(genotype1.num_genes(), genotype2.num_genes())
        dissimilarity = float(disjoint_coef * disjoint_num + excess_coef * excess_num) / float(num_genes)

        return dissimilarity
        

        
    @staticmethod
    def get_excess_disjoint(genotype1, genotype2):
        genes_sorted1 = sorted(genotype1.neuron_genes + genotype1.connection_genes,
                               key = lambda gene: gene.historical_mark)

        genes_sorted2 = sorted(genotype2.neuron_genes + genotype2.connection_genes,
                               key = lambda gene: gene.historical_mark)

        min_mark1 = genes_sorted1[0].historical_mark
        max_mark1 = genes_sorted1[-1].historical_mark

        min_mark2 = genes_sorted2[0].historical_mark
        max_mark2 = genes_sorted2[-1].historical_mark
        
        pairs = GeneticEncoding.get_pairs(genes_sorted1, genes_sorted2)

        excess_num = 0
        disjoint_num = 0
        
        for pair in pairs:

            if pair[0] and not pair[1]:
                mark = pair[0].historical_mark
                if mark > (min_mark2 - 1) and mark < (max_mark2 + 1):
                    disjoint_num += 1
                else:
                    excess_num += 1
                    
            elif pair[1] and not pair[0]:
                mark = pair[1].historical_mark
                if mark > (min_mark1 - 1) and mark < (max_mark1 + 1):
                    disjoint_num += 1
                else:
                    excess_num += 1
        
        return excess_num, disjoint_num


    @staticmethod
    def get_pairs(genes_sorted1, genes_sorted2):
        num_genes1 = len(genes_sorted1)
        num_genes2 = len(genes_sorted2)

        min_mark1 = genes_sorted1[0].historical_mark
        max_mark1 = genes_sorted1[-1].historical_mark

        min_mark2 = genes_sorted2[0].historical_mark
        max_mark2 = genes_sorted2[-1].historical_mark

        min_mark = min(min_mark1, min_mark2)
        max_mark = max(max_mark1, max_mark2)
        
        
        gene_pairs = []

        # search for pairs of genes with equal marks:
        start_from1 = 0
        start_from2 = 0

        mark = min_mark
        while mark < max_mark + 1:

            # jump1 and jump2 are here to skip long sequences of empty historical marks

            gene1 = None
            jump1 = mark + 1
            for i in range(start_from1, num_genes1):
                if genes_sorted1[i].historical_mark == mark:
                    gene1 = genes_sorted1[i]
                    start_from1 = i
                    break

                # if there is a gap, jump over it:
                elif genes_sorted1[i].historical_mark > mark:
                    jump1 = genes_sorted1[i].historical_mark
                    start_from1 = i
                    break

                # if the end of the gene sequence is reached:
                elif i == num_genes1 - 1:
                    jump1 = max_mark + 1
                    start_from1 = i

            gene2 = None
            jump2 = mark + 1
            for i in range(start_from2, num_genes2):
                if genes_sorted2[i].historical_mark == mark:
                    gene2 = genes_sorted2[i]
                    start_from2 = i
                    break

                # if there is a gap, jump over it:
                elif genes_sorted2[i].historical_mark > mark:
                    jump2 = genes_sorted2[i].historical_mark
                    start_from2 = i
                    break

                # if the end of the gene sequence is reached:
                elif i == num_genes2 - 1:
                    jump2 = max_mark + 1
                    start_from2 = i


            # do not add a pair if both genes are None:
            if gene1 or gene2:
                gene_pairs.append((gene1, gene2))

            mark = min(jump1, jump2)
            
        return gene_pairs



    def get_sorted_genes(self):
        return sorted(self.neuron_genes + self.connection_genes,
            key = lambda gene: gene.historical_mark)



    def min_max_hist_mark(self):
        genes_sorted = self.get_sorted_genes()
        return genes_sorted[0].historical_mark, genes_sorted[-1].historical_mark



    def find_gene_by_mark(self, mark):
        for gene in self.neuron_genes + self.connection_genes:
            if gene.historical_mark == mark:
                return gene
        return None



    def add_neuron_gene(self, neuron_gene):
        self.neuron_genes.append(neuron_gene)



    def add_connection_gene(self, connection_gene):
        self.connection_genes.append(connection_gene)



    def remove_connection_gene(self, index):
        del self.connection_genes[index]



    def remove_neuron_gene(self, index):
        del self.neuron_genes[index]



    def to_yaml(self):

        neuron_genes = list(n_g.__dict__ for n_g in self.neuron_genes)
        conn_genes = list(c_g.__dict__ for c_g in self.connection_genes)

        yaml.add_representer(unicode, unicode_representer)
        yaml_repr = {}
        yaml_repr['neurons'] = neuron_genes
        yaml_repr['connections'] = conn_genes
        return yaml.dump(yaml_repr, default_flow_style=False)



    def copy(self):
        copy_gen = GeneticEncoding()

        for n_gene in self.neuron_genes:
            copy_gen.add_neuron_gene(n_gene.copy())

        for c_gene in self.connection_genes:
            copy_gen.add_connection_gene(c_gene.copy())

        return copy_gen



    def check_validity(self):
        for conn_gene in self.connection_genes:
            mark_from = conn_gene.mark_from
            mark_to = conn_gene.mark_to
            if not self.check_neuron_exists(mark_from):
                return False
            if not self.check_neuron_exists(mark_to):
                return False
        return True



    def check_neuron_exists(self, mark):
        for neuron_gene in self.neuron_genes:
            if mark == neuron_gene.historical_mark: return True
        return False



    def __str__(self):
        return "NEAT Genotype at " + hex(id(self))