# import subprocess 
# import sys
from neo4j import GraphDatabase
import argparse
import spacy
import en_core_web_sm

# TO DO: add "is a" information, supporting spacy tags [done]
# TO DO: add origin/source, destination/target, weight information to each node
# TO DO: create example of multiple colliding sentences using "is"
    # TO DO: create a generate_question function using "is". make it a generalizable component
# TO DO: set a timer for certain pathways, to do spaced reminders
# TO DO: create generate_sentence function, probabilistically generate sentences
# TO DO: implement autosuggest, auto complete, spell check
# TO DO: add support for synonyms

# TO DO: get all sentences
# TO DO: complete the sentence


class MemoRepoInterface(object):

    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    # create=experience, creating new memories
    # read=access, check
    # update=memorize, updating old memories
    # destroy=forget
    # semantics = list of properties
    # def controller(self, concept):
    #     with self._driver.session() as session:
    #         if 
    #         node = session.write_transaction(self._memorize_concept, concept)
    #         print(node)


    # MEMORIZATION MODULE BEGINS HERE: *************************************

    def memorize(self, statement):
        print("Memorizing the concepts: {0}".format(statement))
        print("============================================")
        
        self.memorize_concepts(statement) # words + symbols
        self.memorize_relations(statement) # order
        
        # Meta functions
        self.memorize_pos_statements(statement, meta=True) # part of speech

    def memorize_concepts(self, statement, meta=False):
        # if statement is a complete sentence, add beginning and end nodes. For now assume all statements are complete sentences. 
        # Assume the format: xxxx yyyy zzzz
        # Later, support this format: Xxxx yyyy zzzz.
        
        concepts = statement.split() # later this should account for special symbols and marks. right now only accounts for naive words via splitting by spaces.
        
        len_sentence = len(concepts)
        trace_list = []
        for i in range(-1, len_sentence+1): # accounts for start and end node
            
            if i == -1:
                # first add beginning node
                with self._driver.session() as session:
                    concept = "≡"
                    next_concept = concepts[i+1]
                    node = session.write_transaction(self._memorize_concept, concept, meta)
                    print("Memorized the concept: {0}, from node {1}".format(dict(node)['concept'], node.id) + "\n")
                    
                    trace = concept + next_concept
                    node_trace = session.write_transaction(self._memorize_trace, str(trace), concept, meta)
                    print("Set the trace: {0}, from node {1}".format(node_trace[0], node_trace[1]) + "\n")
                    continue
            
            if i == len_sentence:
                # finally, add the end node
                with self._driver.session() as session:
                    concept = "."
                    node = session.write_transaction(self._memorize_concept, concept, meta)
                    print("Memorized the concept: {0}, from node {1}".format(dict(node)['concept'], node.id) + "\n")
                    
                    trace = " ".join(trace_list)
                    node_trace = session.write_transaction(self._memorize_trace, str(trace), concept, meta)
                    print("Set the trace: {0}, from node {1}".format(node_trace[0], node_trace[1]) + "\n")
                    continue
            
            concept = concepts[i]
            with self._driver.session() as session:
                node = session.write_transaction(self._memorize_concept, concept, meta)
                print("Memorized the concept: {0}, from node {1}".format(dict(node)['concept'], node.id) + "\n")

                next_concept = None
                if i == len_sentence - 1:
                    next_concept = "."
                    trace_list.append(concept)
                    trace = "≡" + " ".join(trace_list) + next_concept
                else:
                    next_concept = concepts[i+1]
                    trace_list.append(concept)
                    trace = "≡" + " ".join(trace_list) + " " + next_concept
             
                node_trace = session.write_transaction(self._memorize_trace, str(trace), concept, meta)
                print("Set the trace: {0}, from node {1}".format(node_trace[0], node_trace[1]) + "\n")
                
                # To Do: node should be a tuple. the function should return the correctly formatted info.
                # don't handle in this memorize() function

    def memorize_relations(self, statement, meta=False):
        # if sentence is complete, start from "≡" and end with "."
        # for now, assume all sentences are complete
        concepts = statement.split()
        for i in range(-1, len(concepts)):
            origin_concept = None
            if i == -1:
                origin_concept = "≡"
            else:
                origin_concept = concepts[i]
            
            destination_concept = None
            if i == len(concepts) - 1:
                destination_concept = "."
            else:
                destination_concept = concepts[i+1]
                
            with self._driver.session() as session:
                relation = session.write_transaction(self._memorize_relation, origin_concept, destination_concept, meta)
                print("Memorized the relation: {0}, from link {1}".format(relation[0], relation[1]) + "\n")

    # def memorize_punctuation(self, statement):
        # if the sentence is a whole sentence, add "begin sentence" node in the beginning and "end sentence" node at the end of the sentence.
    
    def memorize_sentences(self, statement):
        concepts = statement.split()
        for i in range(len(concepts)-1):
            origin_concept = concepts[i]
            destination_concept = concepts[i+1]
            with self._driver.session() as session:
                relation = session.write_transaction(self._memorize_relation, origin_concept, destination_concept)
                print("Memorized the relation: {0}, from link {1}".format(relation[0], relation[1]) + "\n")
        return True

    def memorize_pos_statements(self, statement, meta=False):
        nlp = spacy.load("en_core_web_sm")    
        doc = nlp(statement)

        for token in doc:
            statement = "{0} is a {1}".format(str(token), token.tag_)
            print("Memorizing the concepts: {0}".format(statement))
            print("============================================")

            self.memorize_concepts(statement, meta)
            self.memorize_relations(statement, meta)
        return True

    # MEMORIZATION MODULE ENDS HERE: *************************************
    # RECITATION MODULE BEGINS HERE: *************************************

    def recite(self, command):
        print("Reciting {0} sentences:".format(command))
        print("============================================")
        
        if command == "all":
            self.recite_all()

    def recite_all(self):
        with self._driver.session() as session:
            sentences = session.write_transaction(self._recite_all)
        return True
        


    # FUNDAMENTALS BEGIN
    @staticmethod
    def _check_concept(tx, concept):
        """
            check, read, access, retrieve, ...
            if concept exists, return the concept
            if concept does not exist, return None
        """
        print("Checking if the concept exists: {0}".format(concept))
        result = list(tx.run("MATCH (n:Concept {concept: $concept}) "
                        "RETURN n;", concept=concept))
        
        if len(result) == 0: # if the concept does not exist, return no concept
            print("Concept does not exist: {0}".format(concept))
            return None
        elif len(result) == 1: # if the concept exists, return that concept
            print("Concept already exist.")
            return result[0]
        elif len(result) > 1:
            # To Do: clean up duplicate nodes, then return single concept
            return result[0]

    @staticmethod
    def _create_concept(tx, concept, meta=False):
        print("Creating the new concept: {0}".format(concept))
        result = None
        if meta:
            result = tx.run("CREATE (a:Concept) "
                        "SET a.concept = $concept, a.count = 0 "
                        "RETURN a", concept=concept)
        else:
            result = tx.run("CREATE (a:Concept) "
                        "SET a.concept = $concept, a.count = 1 "
                        "RETURN a", concept=concept)
        return result.single()[0]
    
    
    @staticmethod
    def _update_concept(tx, concept, meta=False):
        """
            update concept 
        """
        print("Updating concept: {0}".format(concept))
        result = None
        if meta:
            result = tx.run("MATCH (c:Concept {concept: $concept}) "
                        "RETURN c", concept=concept)
        else:
            result = tx.run("MATCH (c:Concept {concept: $concept}) "
                        "SET c.count = c.count + 1  "
                        "RETURN c", concept=concept)
        return result.single()[0]


    @staticmethod
    def _check_relation(tx, origin_concept, destination_concept):
        result = list(tx.run("MATCH (c1:Concept {concept: $origin_concept}) -[p:Precedes]-> (c2:Concept {concept: $destination_concept}) "
                        "RETURN c1.concept + ' -[p:Precedes]-> ' + c2.concept ", origin_concept=origin_concept, destination_concept=destination_concept))
        if len(result) == 0: # if the relation does not exist, return no relation
            print("Relation does not exist: {0} -> {1}".format(origin_concept, destination_concept))
            return None
        elif len(result) == 1: # if the relation exists, return that relation
            print("Relation already exist.")
            return result[0]
        elif len(result) > 1:
            # To Do: clean up duplicate relations, then return single relation??
            return result[0]

    @staticmethod
    def _create_relation(tx, origin_concept, destination_concept, meta=False):
        print("Creating the relationship: {0} -> {1}".format(origin_concept, destination_concept))
        result = None
        if meta:
            result = list(tx.run("MATCH (c1:Concept {concept: $origin_concept}), (c2:Concept {concept: $destination_concept}) "
                        "CREATE (c1) -[p:Precedes {count: 0}]-> (c2) "
                        "RETURN p ", origin_concept=origin_concept, destination_concept=destination_concept))    
        else:
            result = list(tx.run("MATCH (c1:Concept {concept: $origin_concept}), (c2:Concept {concept: $destination_concept}) "
                        "CREATE (c1) -[p:Precedes {count: 1}]-> (c2) "
                        "RETURN p ", origin_concept=origin_concept, destination_concept=destination_concept))
        return result[0].get('p').type, result[0].get('p').id

    @staticmethod
    def _update_relation(tx, origin_concept, destination_concept, meta=False):
        """
            update relation
        """
        print("Updating relation: {0} -> {1}".format(origin_concept, destination_concept))
        result = None
        if meta:
            result = tx.run("MATCH (c1:Concept {concept: $origin_concept}) -[p:Precedes]-> (c2:Concept {concept: $destination_concept}) "
                        "SET p.count = p.count "
                        "RETURN p", origin_concept=origin_concept, destination_concept=destination_concept)
        else:
            result = tx.run("MATCH (c1:Concept {concept: $origin_concept}) -[p:Precedes]-> (c2:Concept {concept: $destination_concept}) "
                        "SET p.count = p.count + 1  "
                        "RETURN p", origin_concept=origin_concept, destination_concept=destination_concept)
        
        node = result.single()[0]
        return node.type, node.id
    
    # def _check_molecules()
    # abandon this, need to create two nodes and a bond at a time, but that requires either complex/dynamic cypher queries and multiple cases to be efficient

    @staticmethod
    def _check_trace(tx, trace, concept):
        print("Checking trace: {0}".format(trace))
        result = tx.run("MATCH (c1:Concept {concept: $concept}) "
                        "RETURN c1", concept=concept)
        
        node = result.single()[0]
        properties = dict(node)
        keys = properties.keys()
        
        print('178', node)
        # if trace does not exist, return None
        if trace not in keys: 
            return None
        else:
            return node


    @staticmethod
    def _create_trace(tx, trace, concept, meta=False):
        print("Creating trace: {0}".format(trace))

        result = None
        if meta:
            result = tx.run("MATCH (c1:Concept {concept: $concept}) "
                        "WITH c1 "
                        "CALL apoc.create.setProperty(c1, $trace, 0) "
                        "YIELD node "
                        "RETURN c1", trace=trace, concept=concept)
        else:
            result = tx.run("MATCH (c1:Concept {concept: $concept}) "
                        "WITH c1 "
                        "CALL apoc.create.setProperty(c1, $trace, 1) "
                        "YIELD node "
                        "RETURN c1", trace=trace, concept=concept)
        
        node = result.single()[0]
        print('192', node)
        return trace, node.id
    
    def _update_trace(tx, concept, trace, new_trace_count, meta=False):
        print("Updating trace: {0}".format(trace))

        if meta:
            new_trace_count -= 1

        result = tx.run("MATCH (c1:Concept {concept: $concept}) "
                        "WITH c1 "
                        "CALL apoc.create.setProperty(c1, $trace, $new_trace_count) "
                        "YIELD node "
                        "RETURN c1", concept=concept, trace=trace, new_trace_count=new_trace_count)

        node = result.single()[0]
        return trace, node.id

    @staticmethod
    def _recite_all(tx):
        print("Here is the list: ")

        # get all nodes whose direct child is (.)
        # for all nodes' get properties, get keys
        # return keys

        # result = tx.run("MATCH (c1:Concept)-[r]-(c2:Concept {concept: '.'}) "
        # "RETURN c1 "
        # )
        # records = result.records()
        # sentences = []
        # for rec in records:
        #     node_property_keys = list(dict(dict(rec)['c1']).keys())
        #     node_property_keys.remove('count')
        #     node_property_keys.remove('concept')
        #     for sentence in node_property_keys:
        #         print(sentence)
        #         sentences.append(sentence)
        # return sentences

        result = tx.run("MATCH (c1:Concept {concept: '.'}) "
        "RETURN c1 "
        )
        node_properties = dict(result.single()[0])
        print('359', node_properties)
        for (k, v) in node_properties.items():
            print(v, k)
        node_property_keys = list(node_properties.keys())
        node_property_keys.remove('count')
        node_property_keys.remove('concept')
        sentences = []
        for sentence in node_property_keys:
            print(sentence)
            sentences.append(sentence)
        return sentences


    # FUNDAMENTALS END        

    @staticmethod
    def _memorize_concept(tx, concept, meta=False):
        """
            concept, word, idea
        """
        print("Memorizing the concept: {0}".format(concept))
        node = MemoRepoInterface._check_concept(tx, concept)
        if node is None: # if concept does not exist, create concept
            return MemoRepoInterface._create_concept(tx, concept, meta)
        else: # if concept does exist, update old concept
            print("Updating old concept.")
            return MemoRepoInterface._update_concept(tx, concept, meta)
    
    @staticmethod
    def _memorize_relation(tx, origin_concept, destination_concept, meta=False):
        print("Memorizing the relation: {0} -> {1}".format(origin_concept, destination_concept))
        relation = MemoRepoInterface._check_relation(tx, origin_concept, destination_concept)
        if relation is None:
            return MemoRepoInterface._create_relation(tx, origin_concept, destination_concept, meta)
        else:
            print("Updating old relation.")
            return MemoRepoInterface._update_relation(tx, origin_concept, destination_concept, meta)

    @staticmethod
    def _memorize_trace(tx, trace, concept, meta=False):
        print("Memorizing trace.")
        trace_check = MemoRepoInterface._check_trace(tx, trace, concept)
        print('257', trace_check)
        if trace_check is None:
            return MemoRepoInterface._create_trace(tx, trace, concept, meta)
        else:
            print("Updating old trace.")
            trace_count = dict(trace_check)[trace]
            new_trace_count = trace_count + 1
            return MemoRepoInterface._update_trace(tx, concept, trace, new_trace_count, meta)

def main():
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "memorepopassword"
    interface = MemoRepoInterface(uri, user, password)
    
    nlp = spacy.load("en_core_web_sm")   
    # nlp = en_core_web_sm.load() 
    print("Welcome to Memorepo!")
    
    parser = argparse.ArgumentParser(description='Interact with MemoRepo.')
    parser.add_argument('--memorize', nargs="?", const="interface")
    parser.add_argument('--recite', nargs="?", const="all")
    args = parser.parse_args()

    if args.memorize == "interface":
        print("Input your sentences here:")
        while True:
            statement = input(">>> ")
            # Do spacy preprocessing
            # doc = nlp(statement)
            # for token in doc:
            #     print(token.text, token.lemma_, spacy.explain(token.tag_))
            interface.memorize(str(statement))
    elif args.memorize:
        # memorize given sentence
        print(args.memorize)
        interface.memorize(str(args.memorize))

    if args.recite == "all":
        # get_all sentences that exist in memrepo
        # arguments = all, some, specific
        interface.recite(str(args.recite))
        #write
        # if args.
        # if args.recall


main()
