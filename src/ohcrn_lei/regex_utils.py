import re
# from mavehgvs.patterns import protein as prot_regex
from enum import Enum

def get_coding_genomic_protein_changes(text:str)->dict:
    cDNA = Enum('cDNA', ['[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?(?:[GCTAgcta])?>(?:[GCTAgcta])',
                     '[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?(?:[GCTAgcta])?=',
                     '[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?(?:_(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?)?(?:[GCTAgcta]+)?delins(?:[GCTAgcta]+)',
                     '[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?(?:_(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?)?del(?:[GCTAgcta]+)?',
                     '[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?_(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?ins(?:[GCTAgcta]+)',
                     '[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?_(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?inv',
                     '[cC]\.(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?(?:_(?:\d+|\*\d+|-\d+)(?:[+-]\d+)?)?dup(?:[GCTAgcta]+)?'])

    gDNA = Enum('gDNA', [r"g\.\d+(?:_\d+)?(?:[A-Za-z]*>[A-Za-z]*|(?:del|dup|ins|inv|delins)?[A-Za-z0-9]*)?"])

    #Replace the predefined aminoacid codes for a more general regex
    #that matches one capital letter followed by two lower ones
    #Protein patterns taken from https://github.com/VariantEffect/mavehgvs/blob/main/src/mavehgvs/patterns/protein.py
    # p_single_var = prot_regex.pro_single_variant.replace(prot_regex.amino_acid, "(?:[A-Z][a-z]{2})")
    # p_multi_var = prot_regex.pro_multi_variant.replace(prot_regex.amino_acid, "(?:[A-Z][a-z]{2})")

    protein_rgx = "(?:[Pp]\.)?(?:[A-Z][a-zA-Z]{2}\d+(?:[A-Z][a-z]{2}|fs\*\d*|del|ins|dup|delins|Ter)+\d*)(?:;(?:[A-Z][a-z]{2}\d+(?:[A-Z][a-z]{2}|fs\*\d*|del|ins|dup|delins|Ter)\d*))*?"
    
    pDNA = Enum('pDNA', [protein_rgx])

    changes = [cDNA, gDNA, pDNA]

    results_changes = {}

    #Iterate over the changes and their regex to get the matches
    #There will be one list with matches for each variant type
    for change_type in changes:
        #Extract the variant name by slicing
        change_name = str(change_type)
        change_name = change_name[change_name.find("'")+1:-2]
        #Match each regex and store the results in the dictionary
        results_changes[change_name] = []
        for regex in change_type:
            temp = re.findall(regex.name, text)
            if len(temp) > 0:
                results_changes[change_name].extend(temp)
    
    for change in results_changes:
        cp_list = results_changes[change]
        results_changes[change] = list(set(cp_list))
    
    return results_changes

def get_variant_ids(text:str)->list:
    var_id_regex = ["(?:OMIM)(?:\s*[:#])?\s*\d+",
                "(?:Clinvar:)?([SRV]CV[A-Z0-9]{9})",
                "(?:dbSNP:)?(rs\d+)",
                "^COSMIC:COSM[0-9]+$",
                "^clingene:CA\d+$",
                "^uniprot:\.var:\d+$"]

    found_ids = []

    for rgx in var_id_regex:
        found_ids.extend(re.findall(rgx, text))

    return list(set(found_ids))

def get_chromosomes(text:str)->list:
    chromosome_regex = '^Chr([1-9]|1[0-9]|2[0-2]|X|Y)$'
    chrom_results = re.findall(chromosome_regex, text)

    return list(set(chrom_results))
