# MaLSTM-Keras
A Keras implementation of the MaLSTM model for computing Semantic Similarity.

Src: [Mueller, Jonas and Aditya Thyagarajan. “Siamese Recurrent Architectures for Learning Sentence Similarity.” AAAI (2016).](file:///home/jmourad/Downloads/12195-56216-1-PB.pdf)

# Download Embedding: 
GoogleNews-vectors-negative300.bin.gz

# Create Conda Envirement Using yml File
```
conda env create -f environment.yml
```

# Run Model from Terminal With parameters:
```
python manhattan_lstm.py -dn "quora"  -df "../Datasets/quora.tsv" -n 30 -b 2048
```

# Accuracy and Loss
![Model Accuracy](/Images/ModelAccuracy.png)
![Model Loss](/Images/ModelLoss.png)
