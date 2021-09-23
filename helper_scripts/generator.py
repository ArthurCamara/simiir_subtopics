#
# Updated simulation generation script
# For Arthur's experiments (ECIR 2022)
#
# David Maxwell
# 2021-09-21
#

import os
import sys
import json
import errno
import itertools

########## START EDITABLE REGION ##########

STOPWORD_FILE_PATH = '../example_data/terms/stopwords.txt'  # MAKE THESE ABSOLUTE TO BE SAFE
BACKGROUND_MODEL_FILE_PATH = '../example_data/terms/vocab.txt'  # MAKE THESE ABSOLUTE TO BE SAFE

BING_KEY = '631e6bb0c30047acbf63d240eff250e2'

TIME_LIMIT = 2400

shorthands = {
    'seed': 's',
    'limit': 'l',
    'relevant_threshold': 'r',
    'nonrelevant_threshold': 'n',
    'threshold': 't',
    'depth': 'd',
    'full_background': 'b',
    'lam': 'l',
}

costs = {
    'q': 8,         # Cost of issuing a query
    'serp': 2,      # Cost of examining a SERP (can be removed)
    'snip': 3,      # Cost of examining a snippet
    'doc': 10,      # Cost of examining a document
    'mark': 1.68,   # Cost to mark a document
}

logger = {
    'className': 'FixedCostLogger',
    'attributes': [
        {'name': 'time_limit', 'type': 'float', 'value': f'{TIME_LIMIT}', 'is_argument': 'true'},
        {'name': 'query_cost', 'type': 'float', 'value': f'{costs["q"]}', 'is_argument': 'true'},
        {'name': 'document_cost', 'type': 'float', 'value': f'{costs["doc"]}', 'is_argument': 'true'},
        {'name': 'snippet_cost', 'type': 'float', 'value': f'{costs["snip"]}', 'is_argument': 'true'},
        {'name': 'serp_results_cost', 'type': 'float', 'value': f'{costs["serp"]}', 'is_argument': 'true'},
        {'name': 'mark_document_cost', 'type': 'float', 'value': f'{costs["mark"]}', 'is_argument': 'true'},
    ]
}

topics = {
    'ethics': {
        'id': 1,
        'filename': '/ssd2/arthur/simmir_py2/simiir/example_data/topics/ethics.topic',
        'subtopicsFilename': '/ssd2/arthur/simmir_py2/simiir/example_data/subtopics/ethics.subtopics',
    },
    'genetically_modified_organism': {
        'id': 2,
        'filename': '/ssd2/arthur/simmir_py2/simiir/example_data/topics/genetically_modified_organism.topic',
        'subtopicsFilename': '/ssd2/arthur/simmir_py2/simiir/example_data/subtopics/genetically_modified_organism.subtopics',
    },
    'noise-induced_hearing_loss': {
        'id': 3,
        'filename': '/ssd2/arthur/simmir_py2/simiir/example_data/topics/noise-induced_hearing_loss.topic',
        'subtopicsFilename': '/ssd2/arthur/simmir_py2/simiir/example_data/subtopics/noise-induced_hearing_loss.subtopics',
    },
    'subprime_mortgage_crisis': {
        'id': 4,
        'filename': '/ssd2/arthur/simmir_py2/simiir/example_data/topics/subprime_mortgage_crisis.topic',
        'subtopicsFilename': '/ssd2/arthur/simmir_py2/simiir/example_data/subtopics/subprime_mortgage_crisis.subtopics',
    },
    'radiocarbon_dating_considerations': {
        'id': 5,
        'filename': '/ssd2/arthur/simmir_py2/simiir/example_data/topics/radiocarbon_dating_considerations.topic',
        'subtopicsFilename': '/ssd2/arthur/simmir_py2/simiir/example_data/subtopics/radiocarbon_dating_considerations.subtopics',
    },
    'business_cycle': {
        'id': 7,
        'filename': '/ssd2/arthur/simmir_py2/simiir/example_data/topics/business_cycle.topic',
        'subtopicsFilename': '/ssd2/arthur/simmir_py2/simiir/example_data/subtopics/business_cycle.subtopics',
    },
    'irritable_bowel_syndrome': {
        'id': 8,
        'filename': '/ssd2/arthur/simmir_py2/simiir/example_data/topics/irritable_bowel_syndrome.topic',
        'subtopicsFilename': '/ssd2/arthur/simmir_py2/simiir/example_data/subtopics/irritable_bowel_syndrome.subtopics',
    },
    'theory_of_mind': {
        'id': 9,
        'filename': '/ssd2/arthur/simmir_py2/simiir/example_data/topics/theory_of_mind.topic',
        'subtopicsFilename': '/ssd2/arthur/simmir_py2/simiir/example_data/subtopics/theory_of_mind.subtopics',
    }
}

subtopic_strategies = {
    'GREEDY': {
        'id': 1,
        'className': 'GreedySubtopicPicker',
        'attributes': [
            {'name': 'limit', 'type': 'float', 'value': '1.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '2.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '3.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '4.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '5.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '6.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '7.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '8.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '9.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '10.0', 'is_argument': 'true'},
        ],
    },
    'RANDOM': {
        'id': 2,
        'className': 'RandomSubtopicPicker',
        'attributes': [
            {'name': 'seed', 'type': 'integer', 'value': '42', 'is_argument': 'true'},
            {'name': 'seed', 'type': 'integer', 'value': '123', 'is_argument': 'true'},
            {'name': 'seed', 'type': 'integer', 'value': '51', 'is_argument': 'true'},

            {'name': 'limit', 'type': 'float', 'value': '1.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '2.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '3.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '4.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '5.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '6.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '7.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '8.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '9.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '10.0', 'is_argument': 'true'},
        ],
    },
    'REVERSE': {
        'id': 3,
        'className': 'ReverseGreedySubtopicPicker',
        'attributes': [
            {'name': 'limit', 'type': 'float', 'value': '1.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '2.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '3.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '4.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '5.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '6.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '7.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '8.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '9.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '10.0', 'is_argument': 'true'},
        ],
    },
    'GREEDYSMART': {
        'id': 4,
        'className': 'GreedySmart',
        'attributes': [
            {'name': 'limit', 'type': 'float', 'value': '1.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '2.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '3.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '4.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '5.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '6.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '7.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '8.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '9.0', 'is_argument': 'true'},
            {'name': 'limit', 'type': 'float', 'value': '10.0', 'is_argument': 'true'},
        ],
    },
}

querying_strategies = {
    'SMART': {
        'id': '13',
        'className': 'SubtopicLMGenerator',
        'attributes': [
            {'name': 'stopword_file', 'type': 'string', 'value': f'{STOPWORD_FILE_PATH}', 'is_argument': 'true'},
        ],
    },
}

stopping_strategies = {
    'SS1': {
        'id': 1,
        'className': 'FixedDepthDecisionMaker',
        'attributes': [
            {'name': 'depth', 'type': 'integer', 'value': '1', 'is_argument': 'true'},
            {'name': 'depth', 'type': 'integer', 'value': '2', 'is_argument': 'true'},
            {'name': 'depth', 'type': 'integer', 'value': '3', 'is_argument': 'true'},
            {'name': 'depth', 'type': 'integer', 'value': '4', 'is_argument': 'true'},
            {'name': 'depth', 'type': 'integer', 'value': '5', 'is_argument': 'true'},
            {'name': 'depth', 'type': 'integer', 'value': '6', 'is_argument': 'true'},
            {'name': 'depth', 'type': 'integer', 'value': '7', 'is_argument': 'true'},
            {'name': 'depth', 'type': 'integer', 'value': '8', 'is_argument': 'true'},
            {'name': 'depth', 'type': 'integer', 'value': '9', 'is_argument': 'true'},
            {'name': 'depth', 'type': 'integer', 'value': '10', 'is_argument': 'true'},
            {'name': 'depth', 'type': 'integer', 'value': '15', 'is_argument': 'true'},
            {'name': 'depth', 'type': 'integer', 'value': '18', 'is_argument': 'true'},
            {'name': 'depth', 'type': 'integer', 'value': '21', 'is_argument': 'true'},
            {'name': 'depth', 'type': 'integer', 'value': '24', 'is_argument': 'true'},
        ],
    },
    'SS2': {
        'id': 2,
        'className': 'TotalNonrelDecisionMaker',
        'attributes': [
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '1', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '2', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '3', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '4', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '5', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '6', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '7', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '8', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '9', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '10', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '15', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '18', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '21', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '24', 'is_argument': 'true'},
        ],
    },
    'SS3': {
        'id': 3,
        'className': 'SequentialNonrelDecisionMaker',
        'attributes': [
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '1', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '2', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '3', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '4', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '5', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '6', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '7', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '8', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '9', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '10', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '15', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '18', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '21', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '24', 'is_argument': 'true'},
        ],
    },
    'SS4': {
        'id': 4,
        'className': 'SatisfactionFrustrationCombinationDecisionMaker',
        'attributes': [
            {'name': 'timeout_threshold', 'type': 'integer', 'value': '300', 'is_argument': 'true'},
            
            {'name': 'relevant_threshold', 'type': 'integer', 'value': '1', 'is_argument': 'true'},
            {'name': 'relevant_threshold', 'type': 'integer', 'value': '2', 'is_argument': 'true'},
            {'name': 'relevant_threshold', 'type': 'integer', 'value': '3', 'is_argument': 'true'},
            {'name': 'relevant_threshold', 'type': 'integer', 'value': '4', 'is_argument': 'true'},
            {'name': 'relevant_threshold', 'type': 'integer', 'value': '5', 'is_argument': 'true'},
            {'name': 'relevant_threshold', 'type': 'integer', 'value': '6', 'is_argument': 'true'},
            {'name': 'relevant_threshold', 'type': 'integer', 'value': '7', 'is_argument': 'true'},
            {'name': 'relevant_threshold', 'type': 'integer', 'value': '8', 'is_argument': 'true'},
            {'name': 'relevant_threshold', 'type': 'integer', 'value': '9', 'is_argument': 'true'},
            {'name': 'relevant_threshold', 'type': 'integer', 'value': '10', 'is_argument': 'true'},
            
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '1', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '2', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '3', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '4', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '5', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '6', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '7', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '8', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '9', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '10', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '15', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '18', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '21', 'is_argument': 'true'},
            {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '24', 'is_argument': 'true'},
        ],
    },



    
    # 'SS': {
    #     'id': 2,
    #     'className': 'SequentialNonrelDecisionMakerSkip',
    #     'attributes': [
    #         {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '3', 'is_argument': 'true'},
    #         {'name': 'nonrelevant_threshold', 'type': 'integer', 'value': '4', 'is_argument': 'true'},
    #     ],
    # },
}

serp_impressions = {
    'FIXED': {
        'id': 0,
        'className': 'AlwaysTrueSERPImpression',
        'attributes': {

        }
    }
}

snippet_decision_makers = {
    'SNIPPET_LM': {
        'id': '0',
        'className': 'TopicBasedLMTextClassifier',
        'attributes': [
            {'name': 'clean', 'type': 'boolean', 'value': 'true', 'is_argument': 'true'},
            {'name': 'stopword_file', 'type': 'string', 'value': f'{STOPWORD_FILE_PATH}', 'is_argument': 'true'},
            {'name': 'updating', 'type': 'boolean', 'value': 'true', 'is_argument': 'false'},
            {'name': 'update_method', 'type': 'integer', 'value': '2', 'is_argument': 'false'},
            {'name': 'background_file', 'type': 'string', 'value': f'{BACKGROUND_MODEL_FILE_PATH}', 'is_argument': 'true'},

            {'name': 'full_background', 'type': 'boolean', 'value': '1', 'is_argument': 'false'},
            {'name': 'full_background', 'type': 'boolean', 'value': '0', 'is_argument': 'false'},

            {'name': 'threshold', 'type': 'float', 'value': '0.0', 'is_argument': 'false'},
            {'name': 'threshold', 'type': 'float', 'value': '0.1', 'is_argument': 'false'},
            {'name': 'threshold', 'type': 'float', 'value': '0.2', 'is_argument': 'false'},
            {'name': 'threshold', 'type': 'float', 'value': '0.3', 'is_argument': 'false'},
            {'name': 'threshold', 'type': 'float', 'value': '0.4', 'is_argument': 'false'},
            {'name': 'threshold', 'type': 'float', 'value': '0.5', 'is_argument': 'false'},
            {'name': 'threshold', 'type': 'float', 'value': '0.6', 'is_argument': 'false'},
            {'name': 'threshold', 'type': 'float', 'value': '0.7', 'is_argument': 'false'},

            {'name': 'lam', 'type': 'float', 'value': '0.0', 'is_argument': 'false'},
            {'name': 'lam', 'type': 'float', 'value': '0.1', 'is_argument': 'false'},
            {'name': 'lam', 'type': 'float', 'value': '0.2', 'is_argument': 'false'},
            {'name': 'lam', 'type': 'float', 'value': '0.3', 'is_argument': 'false'},
            {'name': 'lam', 'type': 'float', 'value': '0.4', 'is_argument': 'false'},
            {'name': 'lam', 'type': 'float', 'value': '0.5', 'is_argument': 'false'},
            {'name': 'lam', 'type': 'float', 'value': '0.6', 'is_argument': 'false'},
            {'name': 'lam', 'type': 'float', 'value': '0.7', 'is_argument': 'false'},
        ] 
    }
}

document_decision_makers = {
    'DOCUMENT_LM': {
        'id': '0',
        'className': 'TopicBasedLMTextClassifier',
        'attributes': [
            {'name': 'clean', 'type': 'boolean', 'value': 'true', 'is_argument': 'true'},
            {'name': 'stopword_file', 'type': 'string', 'value': f'{STOPWORD_FILE_PATH}', 'is_argument': 'true'},
            {'name': 'updating', 'type': 'boolean', 'value': 'true', 'is_argument': 'false'},
            {'name': 'update_method', 'type': 'integer', 'value': '1', 'is_argument': 'false'},
            {'name': 'background_file', 'type': 'string', 'value': f'{BACKGROUND_MODEL_FILE_PATH}', 'is_argument': 'true'},

            {'name': 'full_background', 'type': 'boolean', 'value': '1', 'is_argument': 'false'},
            {'name': 'full_background', 'type': 'boolean', 'value': '0', 'is_argument': 'false'},

            {'name': 'threshold', 'type': 'float', 'value': '0.0', 'is_argument': 'false'},
            {'name': 'threshold', 'type': 'float', 'value': '0.1', 'is_argument': 'false'},
            {'name': 'threshold', 'type': 'float', 'value': '0.2', 'is_argument': 'false'},
            {'name': 'threshold', 'type': 'float', 'value': '0.3', 'is_argument': 'false'},
            {'name': 'threshold', 'type': 'float', 'value': '0.4', 'is_argument': 'false'},
            {'name': 'threshold', 'type': 'float', 'value': '0.5', 'is_argument': 'false'},
            {'name': 'threshold', 'type': 'float', 'value': '0.6', 'is_argument': 'false'},
            {'name': 'threshold', 'type': 'float', 'value': '0.7', 'is_argument': 'false'},

            {'name': 'lam', 'type': 'float', 'value': '0.0', 'is_argument': 'false'},
            {'name': 'lam', 'type': 'float', 'value': '0.1', 'is_argument': 'false'},
            {'name': 'lam', 'type': 'float', 'value': '0.2', 'is_argument': 'false'},
            {'name': 'lam', 'type': 'float', 'value': '0.3', 'is_argument': 'false'},
            {'name': 'lam', 'type': 'float', 'value': '0.4', 'is_argument': 'false'},
            {'name': 'lam', 'type': 'float', 'value': '0.5', 'is_argument': 'false'},
            {'name': 'lam', 'type': 'float', 'value': '0.6', 'is_argument': 'false'},
            {'name': 'lam', 'type': 'float', 'value': '0.7', 'is_argument': 'false'},
        ] 
    },
}

ordering = [{
        'name': 'sub',
        'object': subtopic_strategies,
    }, {
        'name': 'q',
        'object': querying_strategies,
    }, {
        'name': 'ss',
        'object': stopping_strategies,
    }, {
        'name': 'se',
        'object': serp_impressions,
    }, {
        'name': 'sn',
        'object': snippet_decision_makers,
    }, {
        'name': 'doc',
        'object': document_decision_makers,
    },
]


########## END EDITABLE REGION (YOU SHOULD NOT NEED TO EDIT ANYTHING BELOW THIS LINE) ##########


def generate_combinations():
    level_combinations = {}

    for level in ordering:
        level_name = level['name']

        for object_name in level['object']:
            combinations, duplicates = get_attribute_combinations(level['object'][object_name])

            if level_name not in level_combinations:
                    level_combinations[level_name] = {}
            
            if level['object'][object_name]['id'] not in level_combinations[level_name]:
                level_combinations[level_name][level['object'][object_name]['id']] = {
                    'variables': duplicates,
                    'combinations': [],
                }
            
            if combinations == []:
                continue

            for combination in combinations:
                level_combinations[level_name][level['object'][object_name]['id']]['combinations'].append(combination)
    
    return level_combinations


def generate_component_combinations(all_combinations):
    component_listing = []

    for level in all_combinations:
        level_component_listing = list(all_combinations[level].keys())
        level_component_listing = [{'component': x, 'level': level} for x in level_component_listing]

        component_listing.append(level_component_listing)
    
    return list(itertools.product(*component_listing))


def expand_combination(all_combinations, combination):
    expanded = []

    for component_mapping in combination:
        level_expanded = []

        level = component_mapping['level']
        component_id = component_mapping['component']
        combinations = all_combinations[level][component_id]['combinations']
        variables = all_combinations[level][component_id]['variables']

        #print(f'* {level}\t{component_id}\t{len(variables)}\t{len(combinations)}')
        
        if len(variables) == 0:
            try:
                single_attributes = (list(combinations[0]))
            except IndexError:
                single_attributes = []

            level_expanded.append({
                'level': level,
                'component_id': component_id,
                'attributes': single_attributes,  # !! ADDED, CHECK, WAS JUST [] BEFORE
                'variables': variables,  # Do we need this here?
            })
        else:
            for combination in combinations:
                level_expanded.append({
                    'level': level,
                    'component_id': component_id,
                    'attributes': combination,
                    'variables': variables,  # Do we need this here?
                })
        
        expanded.append(level_expanded)

    return list(itertools.product(*expanded))


def generate_identifier(expanded_entry, is_path=True):
    identifier_string = ''

    for level in expanded_entry:
        level_type = level['level']
        level_id = level['component_id']
        attributes_string = ''

        if len(level['variables']) > 0:
            for attribute in level['attributes']:
                if attribute['name'] in level['variables']:
                    attributes_string = f'{attributes_string}{shorthands[attribute["name"]]}{str(attribute["value"]).replace(".", "").replace("-","9")}'

            if is_path:
                identifier_string = os.path.join(f'{identifier_string}', f'{level_type}{level_id}', f'vars-{attributes_string}')
            else:
                identifier_string = f'{identifier_string}{level_type}{level_id}-{attributes_string}_'
            
            continue
        
        if is_path:
            identifier_string = os.path.join(f'{identifier_string}', f'{level_type}{level_id}')
        else:
            identifier_string = f'{identifier_string}{level_type}{level_id}_'
    
    return identifier_string if is_path else identifier_string[:-1]


def mkdir_p(path):
    """
    http://stackoverflow.com/a/600612
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_expanded_entry_level(expanded_entry, level):
    for object_level in expanded_entry:
        if object_level['level'] == level:
            return object_level
    
    return None

def get_configuration_data(object, identifier):
    for nested_object in object:
        if identifier == object[nested_object]['id']:
            return object[nested_object]
    
    return None

def generate_attributes_xml_string(attributes):
    attributes_string = ''

    if attributes is None:
        return ''
    
    with open('./base_files/attribute.xml', 'r') as attribute_src:
        attribute_file = attribute_src.read()

    for attribute in attributes:
        curr_attribute = (attribute_file + '.')[:-1]

        curr_attribute = curr_attribute.replace('{name}', attribute['name'])
        curr_attribute = curr_attribute.replace('{type}', attribute['type'])
        curr_attribute = curr_attribute.replace('{value}', str(attribute['value']))
        curr_attribute = curr_attribute.replace('{is_argument}', attribute['is_argument'])

        attributes_string = f'{attributes_string}{curr_attribute}\n'
    
    return attributes_string
        
        
def generate_simulation_files(all_combinations, expanded_entry, output_dir, experiment_base_dir, write=True):
    base_path = generate_identifier(expanded_entry, is_path=True)
    identifier = generate_identifier(expanded_entry, is_path=False)

    absolute_output_path = os.path.join(output_dir, base_path)

    if write:
        mkdir_p(absolute_output_path)

    absolute_experiment_output_path = os.path.join(experiment_base_dir, base_path, 'output')

    if write:
        list_output = open(os.path.join(output_dir, 'list'), 'a')

    helper_json = {}

    # Create the singular user file. This could be better.
    with open('./base_files/user.xml', 'r') as user_src:
        user_file = user_src.read()

        user_file = user_file.replace('{userID}', f'user-{identifier}')

        # Costs
        user_file = user_file.replace('{timeLimit}', str(TIME_LIMIT))
        user_file = user_file.replace('{queryCost}', str(costs['q']))
        user_file = user_file.replace('{documentCost}', str(costs['doc']))
        user_file = user_file.replace('{snippetCost}', str(costs['snip']))
        user_file = user_file.replace('{serpCost}', str(costs['serp']))
        user_file = user_file.replace('{markCost}', str(costs['mark']))

        # Query Generation Strategy
        query = get_expanded_entry_level(expanded_entry, 'q')

        user_file = user_file.replace('{queryGeneratorClass}', get_configuration_data(querying_strategies, query['component_id'])['className'])
        user_file = user_file.replace('{queryGeneratorAttributes}', generate_attributes_xml_string(query['attributes']))

        # Snippet Decision Maker
        snip = get_expanded_entry_level(expanded_entry, 'sn')

        user_file = user_file.replace('{snippetClassifierClass}', get_configuration_data(document_decision_makers, snip['component_id'])['className'])
        user_file = user_file.replace('{snippetClassifierAttributes}', generate_attributes_xml_string(snip['attributes']))

        # Document Decision Maker
        doc = get_expanded_entry_level(expanded_entry, 'doc')

        user_file = user_file.replace('{documentClassifierClass}', get_configuration_data(document_decision_makers, doc['component_id'])['className'])
        user_file = user_file.replace('{documentClassifierAttributes}', generate_attributes_xml_string(doc['attributes']))

        # Stopping Strategy
        stop = get_expanded_entry_level(expanded_entry, 'ss')

        user_file = user_file.replace('{stoppingClass}', get_configuration_data(stopping_strategies, stop['component_id'])['className'])
        user_file = user_file.replace('{stoppingAttributes}', generate_attributes_xml_string(stop['attributes']))

        # Subtopic Strategy
        sub = get_expanded_entry_level(expanded_entry, 'sub')

        user_file = user_file.replace('{subtopicClass}', get_configuration_data(subtopic_strategies, sub['component_id'])['className'])
        user_file = user_file.replace('{subtopicAttributes}', generate_attributes_xml_string(sub['attributes']))

        # SERP Examination Strategy
        serp = get_expanded_entry_level(expanded_entry, 'se')

        user_file = user_file.replace('{serpClass}', get_configuration_data(serp_impressions, serp['component_id'])['className'])
        user_file = user_file.replace('{serpAttributes}', generate_attributes_xml_string(serp['attributes']))
        
        if write:
            with open(os.path.join(absolute_output_path, 'user.xml'), 'w') as user_output:
                user_output.write(user_file)

    # Create the simulation file.
    with open('./base_files/simulation.xml', 'r') as simulation_src:
        simulation_file = simulation_src.read()
        
        simulation_file = simulation_file.replace('{simulationID}', identifier)
        simulation_file = simulation_file.replace('{outputPath}', absolute_experiment_output_path)
        simulation_file = simulation_file.replace('{bing_key}', BING_KEY)
        simulation_file = simulation_file.replace('{users}', f'<user configurationFile="{os.path.join(absolute_output_path, "simulation.xml")}" />')

        topic_str = ''

        with open('./base_files/topic.xml', 'r') as topic_src:
            topic_file = topic_src.read()

        for topic_name in topics:
            topic_data = topics[topic_name]
            curr_topic_file = (topic_file + '.')[:-1]

            curr_topic_file = curr_topic_file.replace('{topicID}', topic_name)
            curr_topic_file = curr_topic_file.replace('{topicFilename}', topic_data['filename'])
            curr_topic_file = curr_topic_file.replace('{subtopicsFilename}', topic_data['subtopicsFilename'])

            topic_str = f'{topic_str}{curr_topic_file}\n         '

        simulation_file = simulation_file.replace('{topics}', topic_str)
        
        if write:
            with open(os.path.join(absolute_output_path, 'simulation.xml'), 'w') as simulation_output:
                simulation_output.write(simulation_file)
        
            list_output.write(f'{os.path.join(absolute_output_path, "simulation.xml")}{os.linesep}')

            with open(os.path.join(absolute_output_path, 'ECIR2022_CREATED'), 'w') as simulation_output:
                pass
        
        # Print the created simulation file.
        # print(os.path.join(absolute_output_path, 'simulation.xml'))
    
    if write:
        list_output.close()
    else:
        print(absolute_output_path)


def get_attribute_combinations(config_object):
    attribute_categories = {}
    attribute_categories_nested = []
    duplicates = []

    for attribute in config_object['attributes']:
        if attribute['name'] in attribute_categories.keys() and attribute['name'] not in duplicates:
            duplicates.append(attribute['name'])
        
        if attribute['name'] not in attribute_categories.keys():
            attribute_categories[attribute['name']] = []

        attribute_categories[attribute['name']].append(attribute)
    
    for attribute_category in attribute_categories.keys():
        attribute_categories_nested.append(attribute_categories[attribute_category])
    
    if attribute_categories_nested == []:
        return ([],[])
    
    return (list(itertools.product(*attribute_categories_nested)), duplicates)


def main(output_dir, experiment_base_dir, write=True):
    all_combinations = generate_combinations()
    component_combinations = generate_component_combinations(all_combinations)
    helper_json = {}
    sim_list = []
    count = 0

    for combination in component_combinations:
        expanded = expand_combination(all_combinations, combination)

        for expanded_entry in expanded:
            sim_list.append(generate_simulation_files(all_combinations, expanded_entry, output_dir, experiment_base_dir, write))

            # Append to helper file.
            base_path = generate_identifier(expanded_entry, is_path=True)
            absolute_output_path = os.path.join(output_dir, base_path)
            helper_json[os.path.join(absolute_output_path, 'simulation.xml')] = expanded_entry

            count += 1
    
    if write:
        with open(os.path.join(output_dir, 'helper.json'), 'w') as helper_output:
            helper_output.write(json.dumps(helper_json))
        
        with open(os.path.join(output_dir, 'config.json'), 'w') as config_output:
            config = {
                'TIME_LIMIT': TIME_LIMIT,
                'STOPWORD_FILE_PATH': STOPWORD_FILE_PATH,
                'BACKGROUND_MODEL_FILE_PATH': BACKGROUND_MODEL_FILE_PATH,  
                'shorthands': shorthands,
                'costs': costs,
                'logger': logger,
                'topics': topics,
                'subtopic_strategies': subtopic_strategies,
                'querying_strategies': querying_strategies,
                'stopping_strategies': stopping_strategies,
                'serp_impressions': serp_impressions,
                'snippet_decision_makers': snippet_decision_makers,
                'document_decision_makers': document_decision_makers,
                'ordering': ordering,
            }

            config_output.write(json.dumps(config))

    print(f"Created {count} simulation configurations.")


def usage(script_name):
    print(f"Usage: {script_name} <output_dir> <experiment_base_dir>")
    print()
    print("Where:")
    print("  - <output_dir> Path where output simulation configuration files should be created")
    print("  - <experiment_base_dir> Absolute path to the base directory for where the simulations will be run")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        usage(sys.argv[0])
        sys.exit(1)
    
    output_dir = sys.argv[1]
    experiment_base_dir = sys.argv[2]
    write = True  # Change this to False if you just want to see a list of simulations that will be created, and not to actually make the directories!

    sys.exit(main(output_dir, experiment_base_dir, write))