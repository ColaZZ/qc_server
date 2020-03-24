#!/usr/bin/python3
import random


def loto(some_list, probabilities):
    x = random.uniform(0, 1)
    cumulative_probability = 0.0
    for item, item_probability in zip(some_list, probabilities):
         cumulative_probability += item_probability
         if x < cumulative_probability:
            break
    return item


def test():
    print(loto(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'], [0.15, 0.15, 0.1, 0.1, 0.05, 0.1, 0.1, 0.1, 0.1, 0.05]))


if __name__ == "__main__":
    test()
