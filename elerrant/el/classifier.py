

import re
#import Main_Greek_vocalPassions
from pathlib import Path
import Levenshtein
#use greek stemmer https://pypi.org/project/greek-stemmer/
from greek_stemmer import GreekStemmer
import spacy
import spacy.symbols as POS

# Load Greek Hunspell word list
def load_word_list(path):
    with open(path) as word_list:
        return set([word.strip() for word in word_list])



# Classifier resources
base_dir = "errant/errant/en"
# Spacy
nlp = None
# Greek Stemmer
stemmer = GreekStemmer()
# Greek Word list
spell = load_word_list('/content/errant/el/resources/20110903/el_GR.txt')

# Rare POS tags that make uninformative error categories
rare_pos = {"INTJ", "NUM", "SYM", "X"}
# Open class coarse Spacy POS tags 
open_pos1 = {POS.ADJ, POS.ADV, POS.NOUN, POS.VERB}
# Open class coarse Spacy POS tags (strings)
open_pos2 = {"ADJ", "ADV", "NOUN", "VERB"}
# POS tags with inflectional morphology
inflected_tags = {"ADJ", "ADV", "AUX", "DET", "PRON", "PROPN", "NOUN", "VERB"}
# Some dep labels that map to pos tags.
dep_map = {"ac": "ADP", "svp": "ADP",	"punct": "PUNCT", "CCONJ": "CONJ" }
# Accents/Vowels
accents=['ά','έ', 'ή', 'ί', 'ό', 'ύ', 'ώ']
#Simplified cats
simple_cats={'CCONJ':'CONJ', 'SCONJ':'CONJ', 'ADP':'PREP' }
# Contractions
conts = {"'ναι", "'φερε", "απ'", "σ'", "τ'", "φέρ'", "θ'", "ν'",
         "μ'", "γι'", "μέσ'", "'χει", "'χεις", "'σαι", "'μαι", "'ρθεις", "'ρθει" }

# Contractions
#passions = Main_Greek_vocalPassions.greek_vocalpassions_dict
#conts = {key: list(map(str, value.split())) for key, value in passions.items()}
#cont_list = list(conts.values())
#newlist = [item for items in cont_list for item in items]
#r = re.compile("^'[a-z]*")
#r2 = re.compile("[^.!?]+\'")
#contr1 = list(filter(r.match, newlist))
#contr2 = list(filter(r2.match, newlist))
#conts = contr1 + contr2


# Input: An Edit object
# Output: The same Edit object with an updated error type
def classify(edit):  
    # Nothing to nothing is a detected but not corrected edit
    if not edit.o_toks and not edit.c_toks:
        edit.type = "UNK"
    # Missing
    elif not edit.o_toks and edit.c_toks:
        op = "M:"
        cat = simplify(get_one_sided_type(edit.c_toks))
        edit.type = op+cat   
    # Unnecessary
    elif edit.o_toks and not edit.c_toks:
        op = "U:"
        cat = simplify(get_one_sided_type(edit.o_toks))
        edit.type = op+cat
    # Replacement and special cases
    else:
        # Same to same is a detected but not corrected edit
        if edit.o_str == edit.c_str:
            edit.type = "UNK"
        # Special: Ignore case change at the end of multi token edits
        # E.g. [Doctor -> The doctor], [, since -> . Since]
        # Classify the edit as if the last token wasn't there
        elif edit.o_toks[-1].lower == edit.c_toks[-1].lower and \
                (len(edit.o_toks) > 1 or len(edit.c_toks) > 1):
            # Store a copy of the full orig and cor toks
            all_o_toks = edit.o_toks[:]
            all_c_toks = edit.c_toks[:]
            # Truncate the instance toks for classification
            edit.o_toks = edit.o_toks[:-1]
            edit.c_toks = edit.c_toks[:-1]
            # Classify the truncated edit
            edit = classify(edit)
            # Restore the full orig and cor toks
            edit.o_toks = all_o_toks
            edit.c_toks = all_c_toks
        # Accent/Final N special cases
        #these need to go to replacement
        elif accent(edit.o_toks, edit.c_toks) == "miss_acc":
          edit.type = "M:ACC"
        elif accent(edit.o_toks, edit.c_toks) == "unn_acc":
          edit.type = "U:ACC"
        elif final_n(edit.o_toks, edit.c_toks) == 'unn_fn':
          edit.type = "U:FN"
        elif final_n(edit.o_toks, edit.c_toks) == 'miss_fn':
          edit.type = "M:FN"
        # Replacement
        else:
            op = "R:"
            cat = simplify(get_two_sided_type(edit.o_toks, edit.c_toks))
            edit.type = op+cat
    return edit



# Input: Spacy tokens
# Output: A list of pos and dep tag strings
def get_edit_info(toks):
    pos = []
    dep = []
    for tok in toks:
        pos.append(tok.tag_)
        dep.append(tok.dep_)
    return pos, dep

# Input: Spacy tokens
# Output: An error type string based on input tokens from orig or cor
# When one side of the edit is null, we can only use the other side
def get_one_sided_type(toks):
    # Special cases
    if len(toks) == 1:
        # Contractions. 
        if toks[0].lower_ in conts:
            return "CONTR"
        # Subjunctive "να" is treated as part of a verb form
        if toks[0].lower_ == "να" and toks[0].pos == POS.PART :
            return "VERB:FORM"     
        
    # Extract pos tags and parse info from the toks
    pos_list, dep_list = get_edit_info(toks)
    # Auxiliary verbs e.g "έχω, είχα" 
        # Μέλλοντας "θα"
    if toks[0].lower_ == "θα" and toks[0].pos == POS.PART :
        return "VERB:FORM"
    if toks[0].pos == POS.VERB and set(dep_list).issubset({"aux", "auxpass", "obj", "advmod"}):
        return "VERB:FORM"
    # POS-based tags. Ignores rare, uninformative categories
    if len(set(pos_list)) == 1 and pos_list[0] not in rare_pos:
        return pos_list[0]
    # More POS-based tags using special dependency labels
    if len(set(dep_list)) == 1 and dep_list[0] in dep_map.keys():
        return dep_map[dep_list[0]]
    # Tricky cases
    else:
        return "OTHER"


# Input 1: Spacy orig tokens
# Input 2: Spacy cor tokens
# Output: An error type string based on orig AND cor
def get_two_sided_type(o_toks, c_toks):
    # Extract pos tags and parse info from the toks as lists
    o_pos, o_dep = get_edit_info(o_toks)
    c_pos, c_dep = get_edit_info(c_toks)

    # Orthography; i.e. whitespace and/or case errors.
    if only_orth_change(o_toks, c_toks):
        return "ORTH"
    # Word Order; only matches exact reordering.
    if exact_reordering(o_toks, c_toks):
        return "WO"   
    # 1:1 replacements (very common)
    if len(o_toks) == len(c_toks)==1:
        # Contraction. 
        if (o_toks[0].lower_ in conts or \
                c_toks[0].lower_ in conts) and \
                o_pos == c_pos:
            return "CONTR"
              

# 2. SPELLING AND INFLECTION
        # Only check alphabetical strings on the original side
        # Spelling errors take precedence over POS errors; this rule is ordered
        if o_toks[0].text.isalpha():          
            # Check a greek dict for both orig and lower case.
            # E.g. "cat" is in the dict, but "Cat" is not.
            if o_toks[0].text not in spell and \
                    o_toks[0].lower_ not in spell:
                # Check if both sides have a common lemma
                if o_toks[0].lemma == c_toks[0].lemma:
                    # Inflection; often count vs mass nouns or e.g. got vs getted
                    #spacy issue returns nonetype when does not properly assign pos
                    if o_pos == c_pos and o_pos[0] in {"NOUN", "ADJ", "ADV", "PRON", "VERB"}:
                        return o_pos[0]+":FORM"
                    # Unknown morphology; i.e. we cannot be more specific.
                    else:
                        return "MORPH"
                # Use string similarity to detect true spelling errors.
                else:
                  char_ratio = Levenshtein.ratio(o_toks[0].text, c_toks[0].text)
                  # Ratio > 0.5 means both side share at least half the same chars.
                  # WARNING: THIS IS AN APPROXIMATION.
                  if char_ratio > 0.5:
                      return "SPELL"
                  # If ratio is <= 0.5, the error is more complex e.g. tolk -> say
                  else:
                      # If POS is the same, this takes precedence over spelling.
                      if o_pos == c_pos and \
                              o_pos[0] not in rare_pos:
                          return o_pos[0]
                      # Tricky cases.
                      
                      if char_ratio > 0.9:
                        if o_toks[0] not in conts and c_toks[0] not in conts and \
                        accent(o_toks,c_toks) == "repl_acc":
                          return "ACC"
                      else:
                        return "OTHER"   

        # 3. MORPHOLOGY
        # Only ADJ, ADV, NOUN and VERB can have inflectional changes.
        if o_toks[0].lemma == c_toks[0].lemma and \
                o_pos[0] in open_pos2 and \
                c_pos[0] in open_pos2:
            # Same POS on both sides
            if o_pos == c_pos:
                # Adjective form; e.g. comparatives
                if o_pos[0] == "ADJ":
                    return "ADJ:FORM"
                # Noun number
                if o_pos[0] == "NOUN":
                    return "NOUN:FORM"
                # Verbs - various types
                if o_pos[0] == "VERB":
                    # NOTE: These rules are carefully ordered.
                    # Use the dep parse to find some form errors.
                    # Main verbs preceded by aux cannot be tense or SVA.
                    if preceded_by_aux(o_toks, c_toks):
                        return "VERB:FORM"
                if o_pos == c_pos and o_pos[0] == "VERB":
                        return "VERB:FORM"
                        

        # 4. GENERAL
        # Auxiliaries with different lemmas
        if o_dep[0].startswith("aux") and c_dep[0].startswith("aux"):
            return "VERB:FORM"
        # POS-based tags. Some of these are context sensitive mispellings.
        if o_pos == c_pos and o_pos[0] not in rare_pos:
            return o_pos[0]
        # Some dep labels map to POS-based tags.
        if o_dep == c_dep and o_dep[0] in dep_map.keys():
            return dep_map[o_dep[0]]
        else:
            return "OTHER"

    # Multi-token replacements (uncommon)
    # All auxiliaries
    if set(o_dep+c_dep).issubset({"aux", "auxpass"}):
        return "VERB:FORM"
    # All same POS
    if len(set(o_pos+c_pos)) == 1:
        # Final verbs with the same lemma are tense; e.g. eat -> has eaten 
        if o_pos[0] == "VERB" and \
                o_toks[-1].lemma == c_toks[-1].lemma:
            return "VERB:FORM"
        # POS-based tags.
        elif o_pos[0] not in rare_pos:
            return o_pos[0]
    # All same special dep labels.
    if len(set(o_dep+c_dep)) == 1 and \
            o_dep[0] in dep_map.keys():
        return dep_map[o_dep[0]]
    # Infinitives, gerunds, phrasal verbs.
    if set(o_pos+c_pos) == {"PART", "VERB"}:
        # Final verbs with the same lemma are form; e.g. to eat -> eating
        if o_toks[-1].lemma == c_toks[-1].lemma:
            return "VERB:FORM"
        # Remaining edits are often verb; e.g. to eat -> consuming, look at -> see
        else:
            return "VERB"
    # Possessive nouns; e.g. friends -> friend 's
    if (o_pos == ["NOUN", "PART"] or c_pos == ["NOUN", "PART"]) and \
            o_toks[0].lemma == c_toks[0].lemma:
        return "NOUN:POSS"
    # Adjective forms with "most" and "more"; e.g. more free -> freer
    #if (o_toks[0].lower_ in {"most", "more"} or \
           # c_toks[0].lower_ in {"most", "more"}) and \
           # o_toks[-1].lemma == c_toks[-1].lemma and \
           # len(o_toks) <= 2 and len(c_toks) <= 2:
        #return "ADJ:FORM"

    # Tricky cases.
    else:
        return "OTHER"


def only_orth_change(o_toks, c_toks):
    o_join = "".join([o.lower_ for o in o_toks])
    c_join = "".join([c.lower_ for c in c_toks])
    if o_join == c_join:
        return True
    return False


     


# Input 1: Spacy orig tokens
# Input 2: Spacy cor tokens
# Output: Boolean; the tokens are exactly the same but in a different order
def exact_reordering(o_toks, c_toks):
    # Sorting lets us keep duplicates.
    o_set = sorted([o.lower_ for o in o_toks])
    c_set = sorted([c.lower_ for c in c_toks])
    if o_set == c_set:
        return True
    return False



def accent(o_toks, c_toks):
  o_toks = str(o_toks)
  c_toks = str(c_toks)
  o_chars =[char for char in o_toks]
  c_chars = [char for char in c_toks]
   
  char_list1=[]  
  char_list2=[]  

  if set(o_chars).isdisjoint(accents) == False and set(c_chars).isdisjoint(accents) == True:
    return "unn_acc"
  elif set(o_chars).isdisjoint(accents) == True and set(c_chars).isdisjoint(accents) == False:
   return "miss_acc"
  elif set(o_chars).isdisjoint(accents) == False and set(c_chars).isdisjoint(accents) == False:
    char1 = list(set(o_chars).intersection(accents))
    char2 = list(set(c_chars).intersection(accents))
    if len(char2)>1:
      return 'miss_acc'
    elif len(char1)>1:
      return 'unn_acc'
    else:
      len(char1) == len(char2)
      if o_chars.index(char1[0]) != c_chars.index(char2[0]): 
        return'repl_acc'

    
def final_n(o_toks, c_toks):
  o_toks = str(o_toks)
  c_toks = str(c_toks)
  o_chars =[char for char in o_toks]
  c_chars = [char for char in c_toks]

  if o_chars == c_chars[:-1] and c_chars[-1]=='ν':
    return "miss_fn"
  elif o_chars[:-1] == c_chars and o_chars[-1]=='ν':
    return "unn_fn"

     
# Input 2: A corrected text spacy token.
# Output: Boolean; both tokens have a dependant auxiliary verb.
def preceded_by_aux(o_tok, c_tok):
    # If the toks are aux, we need to check if they are the first aux.
    if o_tok[0].dep_.startswith("aux") and c_tok[0].dep_.startswith("aux"):
        # Find the parent verb
        o_head = o_tok[0].head
        c_head = c_tok[0].head
        # Find the children of the parent
        o_children = o_head.children
        c_children = c_head.children
        # Check the orig children.
        for o_child in o_children:
            # Look at the first aux...
            if o_child.dep_.startswith("aux"):
                # Check if the string matches o_tok
                if o_child.text != o_tok[0].text:
                    # If it doesn't, o_tok is not first so check cor
                    for c_child in c_children:
                        # Find the first aux in cor...
                        if c_child.dep_.startswith("aux"):
                            # If that doesn't match either, neither are first aux
                            if c_child.text != c_tok[0].text:
                                return True
                            # Break after the first cor aux
                            break
                # Break after the first orig aux.
                break
    # Otherwise, the toks are main verbs so we need to look for any aux.
    else:
        o_deps = [o_dep.dep_ for o_dep in o_tok[0].children]
        c_deps = [c_dep.dep_ for c_dep in c_tok[0].children]
        if "aux" in o_deps or "auxpass" in o_deps:
            if "aux" in c_deps or "auxpass" in c_deps:
                return True
    return False

def simplify(cat):
  if cat in simple_cats:
    cat = simple_cats.get(cat)
  return cat