def flatten(list):
    for i in list:
        for j in i:
            yield j


def groupByI(str, x):
    return (str[i:i + x] for i in range(0, len(str), x))
