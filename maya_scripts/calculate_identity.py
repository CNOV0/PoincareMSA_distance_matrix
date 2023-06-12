import pandas as pd
from Bio import Align, SeqIO

def calculate_identity(seq1, seq2):
""" 
    Align two sequences and calculate the percentage of identity between them
    ---------------------------------------
    Input : seq1 seq2
        sequences
        string
    Output : percentage of identity
        float
"""
    aligner = Align.PairwiseAligner()
    alignments = aligner.align(seq1, seq2)
    best_alignment = alignments[0]
    # get the score of that best alignment ==> nb identity
    alignment_score = best_alignment.score
    # return the % identity
    return alignment_score / max(len(seq1), len(seq2))

def read_mfasta_file(filename):
"""
    Open the mfasta file, read the sequences and store them in a list
    --------------------------------------
    Input : filename
        name of the mfasta file
        string
    Output : sequences
        list of sequences
        list
"""
    sequences = []
    with open(filename, "r") as file:
        for record in SeqIO.parse(file, "fasta"):
            sequences.append(str(record.seq))
    return sequences

def calculate_pairwise_identity(filename):
"""
    Input : filename
        name of the .mfasta file
        string
    Output : df
        dataframe containing the percentage of identity
        pandas dataframe
"""
    sequences = read_mfasta_file(filename)
    num_sequences = len(sequences)

    # Create an empty data frame with sequence indices as column and row labels
    matrix_identity = pd.DataFrame(0.0, index=range(num_sequences), columns=range(num_sequences))

    for i in range(num_sequences):
        for j in range(i + 1, num_sequences):
            seq1 = sequences[i]
            seq2 = sequences[j]
            identity = calculate_identity(seq1, seq2)
            matrix_identity.loc[i , j] = identity
            matrix_identity.loc[j, i] = identity

    return matrix_identity

if __name__ == "__main__":
    matrix_identity = calculate_pairwise_identity("examples/globins/glob.mfasta")
    
    matrix_identity.to_csv("matrix_identity.csv", index=False)
    print("Identity DataFrame saved as matrix_identity.csv")