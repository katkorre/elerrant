# ERRANT
In this repository you can find the Greek version of the automatic annotation tool ERRANT, along with two new datasets in Modern Greek, the Greek Native Corpus (GNC) and the Greek WikiEdits corpus (GWE). Elerrant was presented at RANLP 2021 and it is described in:

- Katerina Korre, Marita Chatzipanagiotou and John Pavlopoulos. 2021. ELERRANT: Automatic Grammatical Error Type Classification for Greek. In Proceedings of the Recent Advances in Natural Language Processing. 

Elerrant is based on the ERRor ANnotation Toolkit (ERRANT) described in: 

- Christopher Bryant, Mariano Felice, and Ted Briscoe. 2017. [Automatic annotation and evaluation of Error Types for Grammatical Error Correction](https://aclanthology.org/P17-1074.pdf). In Proceedings of the 55th Annual   Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). Vancouver, Canada.

- Mariano Felice, Christopher Bryant, and Ted Briscoe. 2016. [Automatic extraction of learner errors in esl sentences using linguistically enhanced alignments](https://aclanthology.org/C16-1079.pdf). In Proceedings of     COLING 2016, the 26th International Conference on Computational Linguistics: Technical Papers. Osaka, Japan.

Please cite the above papers if you make use of this code.

# Overview
The main aim of ERRANT is to automatically annotate parallel sentences with error type information. Specifically, given an original and corrected sentence pair, ERRANT will extract the edits that transform the former to the latter and then classify them according to a rule-based error type framework. This can be used to standardise parallel datasets or facilitate detailed error type evaluation. The annotated output file is in M2 format and an evaluation script is provided.

Example:
Original: This are gramamtical sentence .
Corrected: This is a grammatical sentence .
Output M2:
S This are gramamtical sentence .
A 1 2|||R:VERB:SVA|||is|||REQUIRED|||-NONE-|||0
A 2 2|||M:DET|||a|||REQUIRED|||-NONE-|||0
A 2 3|||R:SPELL|||grammatical|||REQUIRED|||-NONE-|||0
A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||1

In M2 format, a line preceded by S denotes an original sentence while a line preceded by A indicates an edit annotation. Each edit line consists of the start and end token offset of the edit, the error type, and the tokenized correction string. The next two fields are included for historical reasons (see the CoNLL-2014 shared task) while the last field is the annotator id.

A "noop" edit is a special kind of edit that explicitly indicates an annotator/system made no changes to the original sentence. If there is only one annotator, noop edits are optional, otherwise a noop edit should be included whenever at least 1 out of n annotators considered the original sentence to be correct. This is something to be aware of when combining individual m2 files, as missing noops can affect results.

# ELERRANT Usage
To use ELERRANT use the following commands:
```
parallel('out_m2','orig.txt',['corr.txt'])
```
This is the main annotation command that takes an original text file and at least one parallel corrected text file as input, and outputs an annotated M2 file.

```
!python errant/commands/compare_m2.py -hyp <hyp_m2> -ref <ref_m2> 
!python errant/commands/compare_m2.py -hyp <hyp_m2> -ref <ref_m2> -cat {1,2,3}
!python errant/commands/compare_m2.py -hyp <hyp_m2> -ref <ref_m2> -ds
!python errant/commands/compare_m2.py -hyp <hyp_m2> -ref <ref_m2> -ds -cat {1,2,3}
```
This is the evaluation command that compares a hypothesis M2 file against a reference M2 file. The default behaviour evaluates the hypothesis overall in terms of span-based correction. The -cat {1,2,3} flag can be used to evaluate error types at increasing levels of granularity, while the -ds or -dt flag can be used to evaluate in terms of span-based or token-based detection (i.e. ignoring the correction). All scores are presented in terms of Precision, Recall and F-score (default: F0.5), and counts for True Positives (TP), False Positives (FP) and False Negatives (FN) are also shown.

# MIT License
Copyright (c) 2017 Christopher Bryant, Mariano Felice

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
