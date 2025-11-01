import sys
def enRango(valor, minimo, maximo):
    if ((valor < minimo) or (valor > maximo)):
        return False
    return True
def calcularPromedio(calif1, calif2, calif3):
    suma = ((calif1 + calif2) + calif3)
    promedio = (suma / 3)
    return promedio
def evaluarEstudiante(promedio, asistencia):
    if (not enRango(promedio, 0, 100)):
        return "error_promedio"
    if (not enRango(asistencia, 0, 100)):
        return "error_asistencia"
    if ((promedio >= 70) and (asistencia >= 80)):
        return "aprobado"
    if ((promedio >= 70) and (asistencia < 80)):
        return "reprobado_asistencia"
    if ((promedio < 70) and (asistencia >= 80)):
        return "reprobado_promedio"
    return "reprobado_ambos"
def imprimirEstadisticas(aprobados, reprobados, total):
    print("=======================================", flush=True)
    print("       ESTADISTICAS FINALES", flush=True)
    print("=======================================", flush=True)
    print(("Total de estudiantes: " + str(total)), flush=True)
    print(("Aprobados: " + str(aprobados)), flush=True)
    print(("Reprobados: " + str(reprobados)), flush=True)
    porcentaje_aprobados = ((aprobados * 100) / total)
    print((("Porcentaje de aprobacion: " + str(porcentaje_aprobados)) + "%"), flush=True)
    print("=========================================", flush=True)
    return
def clasificarPromedio(promedio):
    if (promedio >= 90):
        return "Excelente"
    if (promedio >= 80):
        return "Muy Bien"
    if (promedio >= 70):
        return "Bien"
    if (promedio >= 60):
        return "Regular"
    return "Insuficiente"
total_estudiantes = 5
aprobados = 0
reprobados = 0
suma_promedios = 0
suma_asistencias = 0
nombres = []
calif1_lista = []
calif2_lista = []
calif3_lista = []
promedios = []
asistencias = []
estados = []
promedio_temp = 0
asistencia_temp = 0
temperatura_minima = (-10)
deuda_inicial = (-500)
ajuste_negativo = (-5)
print("============================================", flush=True)
print("=  SISTEMA DE GESTION DE ESTUDIANTES       =", flush=True)
print("=============================================", flush=True)
print("", flush=True)
print("Cargando datos de estudiantes...", flush=True)
print("", flush=True)
nombres.append("Ana Garcia")
calif1_lista.append(85)
calif2_lista.append(90)
calif3_lista.append(88)
asistencias.append(85)
nombres.append("Luis Perez")
calif1_lista.append(60)
calif2_lista.append(65)
calif3_lista.append(62)
asistencias.append(70)
nombres.append("MarÃ­a Lopez")
calif1_lista.append(95)
calif2_lista.append(92)
calif3_lista.append(98)
asistencias.append(95)
nombres.append("Carlos Ruiz")
calif1_lista.append(70)
calif2_lista.append(75)
calif3_lista.append(72)
asistencias.append(82)
nombres.append("Sofia Torres")
calif1_lista.append(50)
calif2_lista.append(55)
calif3_lista.append(52)
asistencias.append(60)
print("============================================", flush=True)
print("  EVALUACION DE ESTUDIANTES", flush=True)
print("============================================", flush=True)
print("", flush=True)
i = 0
while (i < 5):
    c1 = calif1_lista[i]
    c2 = calif2_lista[i]
    c3 = calif3_lista[i]
    asist = asistencias[i]
    prom = calcularPromedio(c1, c2, c3)
    promedios.append(prom)
    estado = evaluarEstudiante(prom, asist)
    estados.append(estado)
    print(((("Estudiante #" + str((i + 1))) + ": ") + nombres[i]), flush=True)
    print(((((("  Calificaciones: " + str(c1)) + ", ") + str(c2)) + ", ") + str(c3)), flush=True)
    print(((("  Promedio: " + str(prom)) + " - ") + clasificarPromedio(prom)), flush=True)
    print((("  Asistencia: " + str(asist)) + "%"), flush=True)
    print(("  Estado: " + estado), flush=True)
    print("", flush=True)
    suma_promedios += prom
    suma_asistencias += asist
    if (estado == "aprobado"):
        aprobados += 1
    else:
        reprobados += 1
    i += 1
print("============================================", flush=True)
print("  ANALISIS DE RENDIMIENTO", flush=True)
print("============================================", flush=True)
mejor_promedio = 0
mejor_indice = 0
j = 0
while (j < 5):
    if (promedios[j] > mejor_promedio):
        mejor_promedio = promedios[j]
        mejor_indice = j
    j += 1
print(("  Mejor estudiante: " + nombres[mejor_indice]), flush=True)
print(("   Promedio: " + str(mejor_promedio)), flush=True)
print("", flush=True)
peor_promedio = 100
peor_indice = 0
k = 0
while (k < 5):
    if (promedios[k] < peor_promedio):
        peor_promedio = promedios[k]
        peor_indice = k
    k += 1
print(("  Estudiante en riesgo: " + nombres[peor_indice]), flush=True)
print(("   Promedio: " + str(peor_promedio)), flush=True)
print("", flush=True)
print("============================================", flush=True)
print("  CALCULOS ESTADISTICOS", flush=True)
print("============================================", flush=True)
promedio_general = (suma_promedios / total_estudiantes)
asistencia_general = (suma_asistencias / total_estudiantes)
print(("Promedio general del grupo: " + str(promedio_general)), flush=True)
print((("Asistencia general del grupo: " + str(asistencia_general)) + "%"), flush=True)
print("", flush=True)
arriba_promedio = 0
debajo_promedio = 0
m = 0
while (m < 5):
    if (promedios[m] >= promedio_general):
        arriba_promedio += 1
    else:
        debajo_promedio += 1
    m += 1
print(("Estudiantes arriba del promedio: " + str(arriba_promedio)), flush=True)
print(("Estudiantes debajo del promedio: " + str(debajo_promedio)), flush=True)
print("", flush=True)
print("============================================", flush=True)
print("  ALERTAS Y RECOMENDACIONES", flush=True)
print("============================================", flush=True)
cumple_estandares = ((promedio_general >= 70) and (asistencia_general >= 80))
if (not cumple_estandares):
    print("   ALERTA: El grupo NO cumple los estandares minimos", flush=True)
    if (promedio_general < 70):
        print("   - Promedio del grupo es bajo", flush=True)
    if (asistencia_general < 80):
        print("   - Asistencia del grupo es baja", flush=True)
else:
    print("  El grupo cumple con los estandares minimos", flush=True)
print("", flush=True)
print("", flush=True)
print("============================================", flush=True)
print("  DETALLES POR TIPO DE REPROBACION", flush=True)
print("============================================", flush=True)
rep_asistencia = 0
rep_promedio = 0
rep_ambos = 0
n = 0
while (n < 5):
    estado_n = estados[n]
    if (estado_n == "reprobado_asistencia"):
        rep_asistencia += 1
    if (estado_n == "reprobado_promedio"):
        rep_promedio += 1
    if (estado_n == "reprobado_ambos"):
        rep_ambos += 1
    n += 1
print(("Reprobados por asistencia: " + str(rep_asistencia)), flush=True)
print(("Reprobados por promedio: " + str(rep_promedio)), flush=True)
print(("Reprobados por ambos: " + str(rep_ambos)), flush=True)
print("", flush=True)
print("============================================", flush=True)
print("  SIMULACION DE MEJORA", flush=True)
print("============================================", flush=True)
puntos_extra = 5
estudiantes_mejorados = 0
print((("Aplicando " + str(puntos_extra)) + " puntos extra..."), flush=True)
print("", flush=True)
p = 0
while (p < 5):
    prom_original = promedios[p]
    if (prom_original < 70):
        prom_nuevo = prom_original
        prom_nuevo += puntos_extra
        print(("Estudiante: " + nombres[p]), flush=True)
        print(("  Promedio original: " + str(prom_original)), flush=True)
        print(("  Promedio nuevo: " + str(prom_nuevo)), flush=True)
        if (prom_nuevo >= 70):
            print("    Ahora APRUEBA", flush=True)
            estudiantes_mejorados += 1
        else:
            print("    Aun reprueba", flush=True)
        print("", flush=True)
    p += 1
print(("Estudiantes que mejoraron: " + str(estudiantes_mejorados)), flush=True)
print("", flush=True)
print("============================================", flush=True)
print("  GENERACION DE REPORTE (bucle WHILE)", flush=True)
print("============================================", flush=True)
contador = 0
while (contador < 5):
    print(((((str((contador + 1)) + ". ") + nombres[contador]) + " - Promedio: ") + str(promedios[contador])), flush=True)
    contador += 1
print("", flush=True)
print("============================================", flush=True)
print("  OPERACIONES CON NUMEROS NEGATIVOS", flush=True)
print("============================================", flush=True)
balance = 1000
cargo = (-150)
print(("Balance inicial: $" + str(balance)), flush=True)
print(("Cargo (negativo): $" + str(cargo)), flush=True)
balance += cargo
print(("Balance despues del cargo: $" + str(balance)), flush=True)
retiro = 50
balance -= retiro
print(("Balance despues del retiro: $" + str(balance)), flush=True)
deposito = 200
reembolso = (-deposito)
print(("Deposito: $" + str(deposito)), flush=True)
print(("Reembolso (negativo): $" + str(reembolso)), flush=True)
print("", flush=True)
print("============================================", flush=True)
print("  CUENTA REGRESIVA (FOR descendente)", flush=True)
print("============================================", flush=True)
cuenta = 5
while (cuenta >= 1):
    print(((("Posicion #" + str(cuenta)) + ": ") + nombres[(cuenta - 1)]), flush=True)
    cuenta -= 1
print("", flush=True)
print("============================================", flush=True)
print("  ESTUDIANTES EN POSICIONES PARES", flush=True)
print("============================================", flush=True)
par = 0
while (par < 5):
    print(((("Posicion " + str(par)) + ": ") + nombres[par]), flush=True)
    par += 2
print("", flush=True)
print("============================================", flush=True)
print("  CALCULOS AVANZADOS", flush=True)
print("============================================", flush=True)
total_puntos = suma_promedios
print(("Total de puntos acumulados: " + str(total_puntos)), flush=True)
puntos_ajustados = total_puntos
puntos_ajustados *= 2
print(("Puntos x2: " + str(puntos_ajustados)), flush=True)
puntos_ajustados /= 5
print(("Puntos promedio x2: " + str(puntos_ajustados)), flush=True)
print("", flush=True)
print("============================================", flush=True)
print("  VALIDACIONES FINALES", flush=True)
print("============================================", flush=True)
todos_aprueban = (aprobados == total_estudiantes)
nadie_aprueba = (reprobados == total_estudiantes)
if todos_aprueban:
    print("Felicidades Todos los estudiantes aprobaron", flush=True)
if nadie_aprueba:
    print("Ningun estudiante aprobo", flush=True)
if ((not todos_aprueban) and (not nadie_aprueba)):
    print("Resultados mixtos en el grupo", flush=True)
print("", flush=True)
print("============================================", flush=True)
print("|  PROGRAMA FINALIZADO EXITOSAMENTE        |", flush=True)
print("============================================", flush=True)
print("", flush=True)
print("Funcionalidades demostradas:", flush=True)
print("  Declaracion de variables (int, string, bool, list)", flush=True)
print("  Funciones con retorno (bool, int, string)", flush=True)
print("  Funciones void", flush=True)
print("  Condicionales (if/else)", flush=True)
print("  Bucles (while y for)", flush=True)
print("  FOR basico (i++)", flush=True)
print("  FOR descendente (i--)", flush=True)
print("  FOR con paso (i+=2)", flush=True)
print("  Listas y metodo append()", flush=True)
print("  Acceso a listas por indice", flush=True)
print("  Operadores compuestos (+=, -=, *=, /=)", flush=True)
print("  Incremento/Decremento (++, --)", flush=True)
print("  Operador NOT (!)", flush=True)
print("  Operador unario negativo (-)", flush=True)
print("  Operaciones aritmeticas (+, -, *, /)", flush=True)
print("  Operaciones logicas (&&, ||)", flush=True)
print("  Comparaciones relacionales (<, >, <=, >=, ==, !=)", flush=True)
print("  Manejo de scopes", flush=True)
print("  Conversion a string str()", flush=True)
print("", flush=True)
print("Gracias por usar el compilador WAX!", flush=True)