test_list = ['EURUSD','CADSGD','EURUSD','CADSGD','EURUSD', 'CADSGD']

counts = [(pair, test_list.count(pair)) for pair in test_list]

print(counts)