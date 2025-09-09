from random import randint

def generate_code(length:int) -> str:
    alp = "1234567890qwertyuiop[]asdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM!@#$%^&*()"
    result_str = ""
    for letter in range(length):
        result_str += alp[randint(0, len(alp)-1)]
    return result_str