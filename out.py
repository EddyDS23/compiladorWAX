# # Programa de prueba WaxLang
# # Declaración correcta
A = (5 + 3)
B = (2.5 + 7.5)
C = "hola mundo"
D = True
print(A)
print(B)
print(C)
print(D)
# /* Comentario de bloque
# ignorado por el parser */
# # Error: tipo incompatible (int != string)
# #wax X: int = "texto";
# # Error: variable no declarada
# #print(Y);
# # Error: redeclaración de variable
# #wax A: int = 10;